import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from database_operations import (
    create_entry, 
    get_entries_by_url, 
    read_entries,
    delete_all_entries, 
    close_connection
)
import xml.etree.ElementTree as ET
from xml.dom import minidom

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# File extensions to filter out
MEDIA_EXTENSIONS = {
    # Image files
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', 
    '.tiff', '.webp', '.svg', '.ico', '.heic',
    # Audio files
    '.mp3', '.wav', '.aac', '.ogg', '.m4a',
    '.wma', '.flac', '.opus', '.mid', '.midi',
    # Video files
    '.mp4', '.avi', '.mov', '.wmv', '.flv',
    '.mkv', '.webm', '.m4v', '.mpg', '.mpeg',
    '.3gp', '.3g2'
}

def generate_sitemap(urls):
    """
    Generate XML sitemap from the list of URLs
    """
    # Create the root element
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    # Add each URL to the sitemap
    for url in urls:
        url_element = ET.SubElement(urlset, 'url')
        loc = ET.SubElement(url_element, 'loc')
        loc.text = url
        
        # Add lastmod element with current date
        lastmod = ET.SubElement(url_element, 'lastmod')
        lastmod.text = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Add changefreq element (set to monthly by default)
        changefreq = ET.SubElement(url_element, 'changefreq')
        changefreq.text = 'monthly'
        
        # Add priority element (set to 0.5 by default)
        priority = ET.SubElement(url_element, 'priority')
        priority.text = '0.5'
    
    # Convert to string with pretty printing
    xml_str = minidom.parseString(ET.tostring(urlset)).toprettyxml(indent="  ")
    
    # Write to file
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(xml_str)

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
    - Not a media file (image, audio, or video)
    Returns True if the URL is valid to visit, False otherwise.
    """
    if "?" in url or "#" in url:
        return False
        
    # Check if the URL ends with a media file extension
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    return not any(path.endswith(ext) for ext in MEDIA_EXTENSIONS)

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
            # 3. Not media files (images, audio, or video)
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

    # Get all URLs from database
    all_entries = read_entries()
    
    # Generate sitemap from URLs
    urls = [entry[1] for entry in all_entries]  # Assuming URL is the second column
    generate_sitemap(urls)

    # Print summary
    print("\nCrawl Summary:")
    print("-" * 50)
    print(f"Total URLs saved in database: {len(all_entries)}")
    print(f"Sitemap generated: sitemap.xml")

    close_connection()

if __name__ == "__main__":
    # Clear the database before starting
    delete_all_entries()
    
    # Get the start URL from user input
    start_url = input("Enter the URL to crawl: ")
    
    # Start the crawl
    crawl(start_url)