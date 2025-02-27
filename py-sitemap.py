import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from database_operations import (
    create_entry, 
    get_entries_by_url, 
    get_entries_by_visited, 
    delete_all_entries, 
    close_connection
)

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def validate_url(url, base_url):
    """
    Validate if the URL belongs to the same domain as the base URL.
    Returns True if the URL is on the same domain, False otherwise.
    """
    base_url_domain = urlparse(base_url).netloc
    url_domain = urlparse(url).netloc
    
    # Handle relative URLs
    if not url_domain:
        return True
        
    return base_url_domain == url_domain

def is_valid_link(url):
    """
    Check if a URL should be visited:
    - No query parameters (?)
    - No fragments (#)
    Returns True if the URL is valid to visit, False otherwise.
    """
    return not ("?" in url or "#" in url)

def get_links(url, base_url):
    """
    Fetch a page and extract all valid links:
    1. Get the page content
    2. Parse with BeautifulSoup
    3. Find all anchor tags
    4. Filter for valid links only
    Returns a set of valid URLs to visit
    """
    try:
        # Fetch the page
        response = requests.get(url, headers=headers)
        print(f"Response code: {response.status_code} for {url}")
        
        if response.status_code != 200:
            print(f"Failed to fetch {url}")
            return set()

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all anchor tags and extract valid links
        valid_links = set()
        for a_tag in soup.find_all('a', href=True):
            link = urljoin(url, a_tag['href'])
            
            # Only add links that are:
            # 1. On the same domain
            # 2. Don't contain ? or #
            if validate_url(link, base_url) and is_valid_link(link):
                valid_links.add(link)
                
        print(f"Found {len(valid_links)} valid links on {url}")
        return valid_links
        
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return set()

def crawl(start_url):
    """
    Main crawling function:
    1. Start with the home page
    2. Get all valid links
    3. Add new links to to_visit
    4. Continue until no more links to visit
    """
    print(f"Starting URL: {start_url}")
    print("-" * 50)
    
    # Initialize with the start URL
    to_visit = {start_url}
    
    while to_visit:
        # Get the next URL to visit
        current_url = to_visit.pop()
        
        # Skip if we've already visited this URL
        if get_entries_by_url(current_url) and current_url != start_url:
            continue
                
        print(f"Visiting: {current_url}")
        
        # Mark this URL as visited in the database
        create_entry(current_url, True)
        
        # Get new links from this page
        new_links = get_links(current_url, start_url)
        
        # Add any links we haven't seen before to to_visit
        unvisited_links = {link for link in new_links if not get_entries_by_url(link)}
        to_visit.update(unvisited_links)
        
        print(f"Added {len(unvisited_links)} new links to visit")
        print(f"Remaining links to visit: {len(to_visit)}")
        print("-" * 30)

    # Print summary
    print("\nCrawl Summary:")
    print("-" * 50)
    print("Visited links:")
    visited_links = get_entries_by_visited()
    for link in visited_links:
        print(f"- {link[1]}")
    print(f"\nTotal URLs visited: {len(visited_links)}")
    print(f"Crawl completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

    close_connection()

if __name__ == "__main__":
    # Clear the database before starting
    delete_all_entries()
    
    # Get the start URL from user input
    start_url = input("Enter the URL to crawl: ")
    
    # Start the crawl
    crawl(start_url)