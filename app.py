from flask import Flask, request, render_template, send_file, redirect, url_for
import os
import sqlite3

# Import DB helpers
from db import get_connection, initialize_db

app = Flask(__name__)

@app.before_first_request
def setup():
    """
    Before the first request is handled,
    ensure that our database schema is initialized.
    """
    initialize_db()

def query_database(query="", filters=None, tag=None):
    """
    Searches the SQLite database with optional text query, date/size filters, and tag filter.
    
    By default, if 'query' is present, we do a JOIN with 'documents_fts' to match
    both 'title' and 'content' columns. The user can also specify date range, file size,
    and tag constraints.
    
    Returns a list of row tuples from the DB.
    """
    if filters is None:
        filters = {}

    conn = get_connection()
    cursor = conn.cursor()

    # Basic SELECT statement
    sql = """
    SELECT d.id, d.title, d.file_path, d.download_date, d.file_size, t.tag
    FROM documents d
    LEFT JOIN tags t ON d.id = t.document_id
    """

    # If we have a text query, use the FTS table (documents_fts)
    where_clauses = []
    params = []

    if query:
        # Switch to selecting from the FTS join
        sql = """
        SELECT d.id, d.title, d.file_path, d.download_date, d.file_size, t.tag
        FROM documents d
        JOIN documents_fts f ON d.id = f.rowid
        LEFT JOIN tags t ON d.id = t.document_id
        WHERE f MATCH ?
        """
        # Trick: replace spaces with '* ' to broaden search for partial matches
        params.append(query.replace(" ", "* ") + "*")

    # If we have date/size filters, add them
    if filters.get("start_date"):
        where_clauses.append("d.download_date >= ?")
        params.append(filters["start_date"])
    if filters.get("end_date"):
        where_clauses.append("d.download_date <= ?")
        params.append(filters["end_date"])
    if filters.get("min_size"):
        where_clauses.append("d.file_size >= ?")
        params.append(filters["min_size"])
    if filters.get("max_size"):
        where_clauses.append("d.file_size <= ?")
        params.append(filters["max_size"])

    # If a tag is provided, filter by that
    if tag:
        where_clauses.append("t.tag = ?")
        params.append(tag)

    # Merge our WHERE clauses
    if where_clauses:
        # If we already used WHERE in the FTS logic, use AND; otherwise use WHERE
        sql += " AND " if "WHERE" in sql else " WHERE "
        sql += " AND ".join(where_clauses)

    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()
    return results

@app.route("/", methods=["GET"])
def index():
    """
    Home page: shows a search form with optional query, tag, date range, and size range.
    If the user has submitted any search criteria, displays results in a table.
    """
    query = request.args.get("query", "").strip()
    tag = request.args.get("tag", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    min_size = request.args.get("min_size", "").strip()
    max_size = request.args.get("max_size", "").strip()

    # Build filter dictionary
    filters = {
        "start_date": start_date if start_date else None,
        "end_date": end_date if end_date else None,
        "min_size": int(min_size) if min_size.isdigit() else None,
        "max_size": int(max_size) if max_size.isdigit() else None,
    }

    # Only query if the user actually provided something in the form
    results = []
    if query or tag or any(filters.values()):
        results = query_database(query=query, filters=filters, tag=tag)

    return render_template("index.html",
                           results=results,
                           query=query,
                           tag=tag,
                           start_date=start_date,
                           end_date=end_date,
                           min_size=min_size,
                           max_size=max_size)

@app.route("/download/<path:filename>")
def download(filename):
    """
    Sends the requested PDF file to the user for download.
    'filename' is the local path to the PDF in our 'cia_foia_library' folder.
    """
    return send_file(filename, as_attachment=True)

@app.route("/add_tag", methods=["POST"])
def add_tag():
    """
    Handles submission of a new tag for a given document ID.
    Then redirects back to the home page (or you can redirect to previous search).
    """
    doc_id = request.form["doc_id"]
    new_tag = request.form["tag"].strip()

    # Don't add empty tags
    if not new_tag:
        return redirect("/")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tags (document_id, tag) VALUES (?, ?)", (doc_id, new_tag))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/tags")
def list_tags():
    """
    Displays all existing tags, along with the number of documents associated
    with each. Users can click on a tag to filter for documents with that tag.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tag, COUNT(*) as count
        FROM tags
        GROUP BY tag
        ORDER BY count DESC
    """)
    tag_counts = cursor.fetchall()
    conn.close()
    return render_template("tags.html", tag_counts=tag_counts)

if __name__ == "__main__":
    # Run the Flask development server on 0.0.0.0:5000
    app.run(debug=True, host="0.0.0.0", port=5000)