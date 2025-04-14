# Configuration for the crawler
DOMAINS = [
    "https://www.virgio.com/",
    "https://www.tatacliq.com/",
    "https://nykaafashion.com/",
    "https://www.westside.com/"
]

PRODUCT_PATTERNS = [
    r"/product/",
    r"/p/",
    r"/item/",
    r"/shop/",
    r"-p-",
    r"/pdp/",
    r"/products/",
    r"[0-9]+$"
]