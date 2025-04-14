import re
from urllib.parse import urljoin, urlparse

def is_product_url(url, patterns):
    """Check if a URL is likely a product page."""
    return any(re.search(pattern, url.lower()) for pattern in patterns)

def is_same_domain(url, base_domain):
    """Check if a URL belongs to the same domain."""
    return urlparse(url).netloc == urlparse(base_domain).netloc

def get_absolute_url(base_url, href):
    """Convert relative URL to absolute."""
    return urljoin(base_url, href)