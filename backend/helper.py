from urllib.parse import urlparse

def extract_site_from(url: str) -> str:
    """
    Extract the TLD and main domain part (e.g., 'example.com' from 'subdomain.example.com')
    """
    # Remove protocol if present
    if '://' in url:
        url = urlparse(url).netloc
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    # Split by dots and get the last two parts (domain + TLD)
    parts = url.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return url