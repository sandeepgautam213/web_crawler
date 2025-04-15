import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from webdriver_manager.chrome import ChromeDriverManager
from config import DOMAINS, PRODUCT_PATTERNS
from utils import is_product_url, is_same_domain, get_absolute_url


def setup_driver():
    """Set up headless Chrome WebDriver."""
    options = Options()
    # options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def scroll_to_bottom(driver, wait_time=2, max_scrolls=10):
    """Scroll to the bottom of the page gradually."""
    last_height = driver.execute_script("return document.body.scrollHeight")

    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def crawl_page(url, base_url, driver, visited_urls, product_urls, depth=0, max_depth=2):
    """Crawl a single page and extract potential product URLs."""
    try:
        if url in visited_urls or depth > max_depth:
            return
        visited_urls.add(url)

        driver.get(url)
        scroll_to_bottom(driver, wait_time=2, max_scrolls=10)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            full_url = get_absolute_url(base_url, href)

            if is_same_domain(full_url, base_url) and full_url not in visited_urls:
                if is_product_url(full_url, PRODUCT_PATTERNS):
                    product_urls.add(full_url)
                else:
                    crawl_page(full_url, base_url, driver, visited_urls, product_urls, depth + 1, max_depth)

    except Exception as e:
        print(f"[ERROR] Failed to crawl {url}: {e}")


def crawl_domain(domain):
    print(f"[START] Crawling {domain}")
    driver = setup_driver()
    visited_urls = set()
    product_urls = set()

    try:
        crawl_page(domain, domain, driver, visited_urls, product_urls,max_depth=3)
    except Exception as e:
        print(f"[ERROR] Failed to crawl domain {domain}: {e}")
        return []
    finally:
        driver.quit()

    print(f"[DONE] Crawled {domain} — Found {len(product_urls)} product URLs")
    return list(product_urls)


def main():
    """Main function to crawl all domains and save product URLs."""
    start_time = time.time()
    all_product_urls = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(crawl_domain, DOMAINS)
        for result in results:
            all_product_urls.extend(result)

    data = [{"Domain": urlparse(url).netloc, "Product_URL": url} for url in all_product_urls]
    df = pd.DataFrame(data)
    df.drop_duplicates(subset=["Product_URL"], inplace=True)

    output_file = "data/output/product_urls.csv"
    df.to_csv(output_file, index=False)
    print(f"[SUCCESS] Results saved to {output_file}")
    print(f"[STATS] Total product URLs: {len(df)}")
    print(f"[TIME] Total time: {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    main()
