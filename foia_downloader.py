import os
import requests
import argparse
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# pypdf is the updated library for parsing PDF files
from pypdf import PdfReader

# Import our centralized DB logic
from db import get_connection, initialize_db

# Constants for CIA FOIA website structure
BASE_URL = "https://www.cia.gov/readingroom"
SEARCH_URL = f"{BASE_URL}/search/site/?f%5B0%5D=im_field_document_type%3A1702"
OUTPUT_DIR = "cia_foia_library"

def parse_pdf(file_path):
    """
    Attempts to extract text from a PDF using pypdf.
    Returns the extracted text as a single string.
    If extraction fails (e.g., scanned images without OCR), returns an empty string.
    """
    text_content = []
    try:
        with open(file_path, "rb") as pdf_file:
            reader = PdfReader(pdf_file)
            # Some PDFs can have a large number of pages or encrypted content
            for page in reader.pages:
                extracted = page.extract_text() or ""
                text_content.append(extracted)
    except Exception as e:
        print(f"Warning: Could not parse PDF '{file_path}' due to: {e}")
        return ""
    return "\n".join(text_content)

def index_document(title, url, file_path, file_size, download_date, content):
    """
    Inserts document metadata and extracted content into the database.
    Also inserts a default tag 'Uncategorized' for each new document.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Insert into main documents table
    cursor.execute("""
        INSERT INTO documents (title, url, file_path, file_size, download_date)
        VALUES (?, ?, ?, ?, ?)
    """, (title, url, file_path, file_size, download_date))
    
    doc_id = cursor.lastrowid

    # Insert into the full-text index
    cursor.execute("""
        INSERT INTO documents_fts (title, content, url, file_path, file_size, download_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, content, url, file_path, file_size, download_date))

    # Apply default tag for new documents
    cursor.execute("INSERT INTO tags (document_id, tag) VALUES (?, ?)", (doc_id, "Uncategorized"))

    conn.commit()
    conn.close()
    return doc_id

def get_document_links():
    """
    Crawls the CIA FOIA Reading Room site page-by-page, collecting PDF links.
    Stops when there is no 'next page' link available.
    Returns a list of (title, url) tuples for all discovered PDFs.
    """
    links = []
    page = 0

    while True:
        url = f"{SEARCH_URL}&page={page}"
        print(f"Scraping page {page}...")

        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching page {page} (status {response.status_code}). Stopping.")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        doc_links = soup.find_all("a", href=True)

        found_pdfs = 0
        for link in doc_links:
            href = link["href"]
            # The CIA site uses .pdf suffix to link to PDF files
            if href.endswith(".pdf"):
                full_link = BASE_URL + href
                # Use link text or fallback to the filename
                title = link.text.strip() or href.split("/")[-1]
                links.append((title, full_link))
                found_pdfs += 1

        print(f"Found {found_pdfs} PDFs on page {page}.")

        # If there's no 'next' pagination link, we've reached the last page
        next_page = soup.find("a", class_="pager-next")
        if not next_page:
            print("No more pages. Finished scraping.")
            break

        page += 1

    return links

def download_document(doc):
    """
    Downloads a single PDF document, extracts metadata and text, 
    and stores them in the local SQLite database.
    """
    title, url = doc
    filename = os.path.join(OUTPUT_DIR, url.split("/")[-1])

    # Check if this URL was already downloaded
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM documents WHERE url=?", (url,))
    existing = cursor.fetchone()
    conn.close()
    if existing:
        print(f"Skipping '{title}' (already downloaded).")
        return

    try:
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            with open(filename, "wb") as f, tqdm(
                total=total_size, unit="B", unit_scale=True, desc=title[:50]
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            print(f"Downloaded: {title}")

            # Extract PDF text for full-text indexing
            content = parse_pdf(filename)

            # Insert doc metadata + content into the DB
            index_document(
                title=title,
                url=url,
                file_path=filename,
                file_size=total_size,
                download_date=datetime.now().isoformat(),
                content=content
            )
        else:
            print(f"Failed to download '{title}' (URL: {url}), status code: {response.status_code}.")
    except Exception as e:
        print(f"Error downloading '{title}' from {url}: {e}")

def main():
    """
    Main entry point for the downloader script:
      1. Parse command-line arguments for concurrency control.
      2. Initialize the database (create tables if needed).
      3. Scrape the CIA FOIA site for PDF links.
      4. Download them with a ThreadPoolExecutor for parallelism.
    """
    parser = argparse.ArgumentParser(description="CIA FOIA Downloader Script")
    parser.add_argument("--max-workers", type=int, default=5, 
                        help="Number of concurrent download threads (default: 5)")
    args = parser.parse_args()

    # Ensure local output directory for PDFs
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Ensure DB schema is up to date
    initialize_db()

    print("Fetching document links from CIA Reading Room...")
    doc_links = get_document_links()
    print(f"Total documents discovered: {len(doc_links)}")

    # Download PDFs in parallel
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        executor.map(download_document, doc_links)

    print("All downloads completed.")

if __name__ == "__main__":
    main()