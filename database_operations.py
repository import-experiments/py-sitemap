import sqlite3
from datetime import datetime

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('pysitemap.sqlite3')

# Create a cursor object
cursor = conn.cursor()

# Create the visited_urls table
cursor.execute('''
CREATE TABLE IF NOT EXISTS visited_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    visited BOOLEAN,
    datetime DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Function to create a new entry
def create_entry(url, visited=None):
    cursor.execute('''
    INSERT INTO visited_urls (url, visited)
    VALUES (?, ?)
    ''', (url, visited))
    conn.commit()

# Function to read all entries
def read_entries():
    cursor.execute('SELECT * FROM visited_urls')
    return cursor.fetchall()

# Function to get an entry by id
def get_entry_by_id(entry_id):
    cursor.execute('SELECT * FROM visited_urls WHERE id = ?', (entry_id,))
    return cursor.fetchone()

# Function to get entries by url
def get_entries_by_url(url):
    cursor.execute('SELECT * FROM visited_urls WHERE url = ?', (url,))
    return cursor.fetchall()

# Function to get entries by visited=True
def get_entries_by_visited():
    cursor.execute('SELECT * FROM visited_urls WHERE visited = ?', (True,))
    return cursor.fetchall()

# Function to update an entry by id
def update_entry(entry_id, url=None, visited=None):
    if url:
        cursor.execute('''
        UPDATE visited_urls
        SET url = ?
        WHERE id = ?
        ''', (url, entry_id))
    if visited is not None:
        cursor.execute('''
        UPDATE visited_urls
        SET visited = ?
        WHERE id = ?
        ''', (visited, entry_id))
    conn.commit()

# Function to delete an entry by id
def delete_entry(entry_id):
    cursor.execute('''
    DELETE FROM visited_urls
    WHERE id = ?
    ''', (entry_id,))
    conn.commit()

# Function to delete all entries
def delete_all_entries():
    cursor.execute('DELETE FROM visited_urls')
    conn.commit()

# Close the connection
def close_connection():
    conn.close()

if __name__ == "__main__":
    # Example usage
    # Create some entries
    create_entry('https://example.com', True)
    create_entry('https://example.org', False)

    # Read all entries
    entries = read_entries()
    print("Entries:", entries)

    # Get an entry by id
    entry = get_entry_by_id(1)
    print("Entry by ID:", entry)

    # Get entries by url
    entries = get_entries_by_url('https://example.com')
    print("Entries by URL:", entries)

    # Get entries by visited=True
    entries = get_entries_by_visited()
    print("Entries by visited=True:", entries)

    # Update an entry
    update_entry(1, visited=False)

    # Read all entries after update
    entries = read_entries()
    print("Entries after update:", entries)

    # Delete an entry
    delete_entry(2)

    # Read all entries after deletion
    entries = read_entries()
    print("Entries after deletion:", entries)

    # Delete all entries
    delete_all_entries()

    # Read all entries after deleting all
    entries = read_entries()
    print("Entries after deleting all:", entries)

    # Close the connection
    close_connection()