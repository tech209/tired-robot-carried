CIA FOIA Library Downloader + Web UI

This project scrapes, downloads, and indexes declassified PDF documents from the CIA FOIA Reading Room. It also provides a lightweight Flask web interface for searching, filtering, tagging, and downloading the archived PDFs.

Features
	•	Automated Downloader
	•	Scrapes the CIA FOIA Reading Room for PDF links.
	•	Downloads and saves each PDF, storing metadata (title, file size, URL, and download date) in a local SQLite database.
	•	Extracts text from each PDF (where possible) for full-text search using pypdf.
	•	Local SQLite Database
	•	Stores all metadata in cia_foia_library.db.
	•	Utilizes an FTS5 (Full Text Search) virtual table for fast searching across titles, URLs, and extracted text.
	•	Tagging System
	•	Users can assign arbitrary tags to any document.
	•	A single document can have multiple tags.
	•	Quickly filter documents by tag via the web UI.
	•	Flask Web UI
	•	Search bar for free-text queries.
	•	Date-range and file-size filtering.
	•	Tag-based filtering.
	•	File download links.
	•	Separate page listing all tags with their document counts.

Project Structure

.
├── app.py             # Flask web application
├── db.py              # Database connection and initialization logic
├── foia_downloader.py # Main scraper & PDF downloader script
├── requirements.txt   # Python dependencies
├── templates
│   ├── index.html     # Main UI template
│   └── tags.html      # Tag listing template
└── Dockerfile         # Optional Docker container build file

Dependencies
	•	Flask: Web framework
	•	requests: For HTTP requests to the CIA FOIA Reading Room
	•	beautifulsoup4: HTML parsing to find PDF links
	•	tqdm: Progress bar for downloads
	•	pypdf: Extract text from PDF files
	•	sqlite3: Included in the Python standard library (for local DB storage)

You can install these via the included requirements.txt.

Quick Start
	1.	Clone the Repository

git clone https://github.com/yourname/cia-foia-downloader.git
cd cia-foia-downloader


	2.	Install Python Dependencies

pip install -r requirements.txt

Ensure you are using Python 3.9 or newer for best compatibility.

	3.	Run the Downloader

python foia_downloader.py --max-workers 5

	•	–max-workers (optional): number of concurrent download threads. Default is 5.
	•	This will create a cia_foia_library/ folder containing all downloaded PDF files.
	•	Metadata is stored in cia_foia_library.db.

	4.	Start the Web App

python app.py

	•	Access the web interface at http://127.0.0.1:5000.
	•	Use the search bar to look for keywords, filter by tag, or apply date/size filters.
	•	Click “Download PDF” in the results table to save a PDF locally.

Docker (Optional)

If you want to run everything in a Docker container:
	1.	Build the Image

docker build -t cia_foia .


	2.	Run the Container

docker run -p 5000:5000 cia_foia

	•	This will run the downloader automatically (with --max-workers 5) and then start the web server.
	•	Go to http://localhost:5000 to use the interface.

Usage Details

Scraper & Downloader
	•	The scraper finds all .pdf links across paginated search results at the CIA FOIA Reading Room.
	•	Download progress bars appear for each document thanks to tqdm.
	•	PDF files are saved in the cia_foia_library/ directory.
	•	pypdf attempts to extract text from each PDF. The extracted text is stored in the content column of the FTS table (documents_fts) for full-text queries.

Web UI
	•	Homepage (/)
	•	Simple search form with the following fields:
	•	Search Query: Matches words in the PDF’s title and text (if extractable).
	•	Tag: Filter documents by a specific tag (e.g., Soviet, Nuclear).
	•	Date Range: Only show documents downloaded within this date range (ISO format).
	•	File Size: Only show PDFs within a minimum/maximum file size (in bytes).
	•	Results show each document’s Title, Download Date, File Size, any Tag, and a Download button.
	•	Tagging
	•	Each search result has an inline form for adding a new tag.
	•	You can also view a list of all tags by visiting the /tags page.
	•	Download Route
	•	Each result row includes a link that points to /download/<filename> to serve the original PDF file.

Known Limitations
	1.	OCR
	•	If a PDF is purely a scanned image and not OCR’d, pypdf may not be able to extract text. The document will still be indexed by title, but full-text search won’t include its contents.
	•	Consider integrating an OCR tool (e.g., Tesseract) for deeper text extraction if you need that.
	2.	Site Changes
	•	If the CIA FOIA website changes its structure or link format, the scraper logic may need updates.
	3.	SQLite Concurrency
	•	SQLite can handle multiple readers and single-writer concurrency well, but for a multi-user production environment with frequent writes, you might need a more robust DB (e.g., PostgreSQL).

Future Enhancements
	•	OCR for Scanned PDFs
	•	Integrate a library like pytesseract and an image converter to handle non-searchable PDFs.
	•	Improved Pagination & Error Handling
	•	Retry failed downloads or handle partial content more gracefully.
	•	Implement throttling or backoff if the server responds with errors.
	•	Advanced UI
	•	Use a JavaScript table (e.g., DataTables) for sorting, pagination, or advanced filtering in the browser.
	•	Docker Compose
	•	A docker-compose.yml file could orchestrate separate containers (downloader & web app) if you’d like them to run independently.

License

This project is available under the MIT License. See LICENSE for details.
