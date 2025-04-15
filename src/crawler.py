import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import InvalidSessionIdException
from bs4 import BeautifulSoup
import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor
from webdriver_manager.chrome import ChromeDriverManager
from collections import deque

# Custom config and utility imports
from config import DOMAINS, PRODUCT_PATTERNS
from utils import is_product_url, is_same_domain, get_absolute_url

# Max number of threads to use for parallel crawling
Max_worker = 4


def setup_driver():
    """
    Initialize a Chrome WebDriver with custom options.
    """
    options = Options()
    # options.add_argument("--headless=new")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def scroll_to_bottom(driver, wait_time=3, max_scrolls=10):
    """
    Scrolls to the bottom of the page multiple times to trigger dynamic content loading.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")

    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def save_partial_csv(product_urls, domain_name):
    """
    Save partially scraped product URLs to a CSV file for resuming later.
    """
    os.makedirs("data/output/tmp", exist_ok=True)
    partial_file = f"data/output/tmp/{urlparse(domain_name).netloc}_products.csv"
    df = pd.DataFrame([{"Domain": urlparse(url).netloc, "Product_URL": url} for url in product_urls])
    df.to_csv(partial_file, index=False)


def load_existing_product_urls(domain):
    """
    Load previously scraped product URLs from a temporary CSV file if available.
    """
    partial_file = f"data/output/tmp/{urlparse(domain).netloc}_products.csv"
    if os.path.exists(partial_file):
        df = pd.read_csv(partial_file)
        return set(df["Product_URL"].tolist())
    return set()


def crawl_page_iterative(start_url, base_url, driver, product_urls, max_depth=2, domain_name=None):
    """
    Iteratively crawl a website starting from the given URL using BFS.
    Product URLs are collected and saved periodically.
    """
    visited_urls = set(product_urls)
    queue = deque([(start_url, 0)])

    while queue:
        url, depth = queue.popleft()
        if url in visited_urls or depth > max_depth:
            continue
        visited_urls.add(url)

        try:
            driver.get(url)
            scroll_to_bottom(driver, wait_time=2, max_scrolls=10)
        except InvalidSessionIdException:
            print(f"[ERROR] Invalid session for {url}")
            break
        except Exception as e:
            print(f"[ERROR] Failed to load {url}: {e}")
            continue

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href']
            full_url = get_absolute_url(base_url, href)

            if not is_same_domain(full_url, base_url):
                continue
            if full_url in visited_urls:
                continue

            if is_product_url(full_url, PRODUCT_PATTERNS):
                product_urls.add(full_url)
            else:
                queue.append((full_url, depth + 1))

        if domain_name:
            save_partial_csv(product_urls, domain_name)


def crawl_domain(domain):
    """
    Launches the crawler for a single domain, handling setup and teardown.
    """
    print(f"[START] Crawling {domain}")
    driver = setup_driver()
    product_urls = load_existing_product_urls(domain)

    try:
        crawl_page_iterative(domain, domain, driver, product_urls, max_depth=3, domain_name=domain)
    except Exception as e:
        print(f"[ERROR] Failed to crawl domain {domain}: {e}")
    finally:
        save_partial_csv(product_urls, domain)
        driver.quit()

    print(f"[DONE] Crawled {domain} — Found {len(product_urls)} product URLs")
    return list(product_urls)


def main():
    """
    Main entry point: handles parallel crawling and merges final results.
    """
    start_time = time.time()

    try:
        with ThreadPoolExecutor(Max_worker) as executor:
            executor.map(crawl_domain, DOMAINS)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user. Saving progress...")

    all_product_dfs = []
    tmp_dir = "data/output/tmp"
    if os.path.exists(tmp_dir):
        for file in os.listdir(tmp_dir):
            if file.endswith("_products.csv"):
                df = pd.read_csv(os.path.join(tmp_dir, file))
                all_product_dfs.append(df)

    if all_product_dfs:
        final_df = pd.concat(all_product_dfs, ignore_index=True)
        final_df.drop_duplicates(subset=["Product_URL"], inplace=True)
        output_file = "data/output/product_urls.csv"
        final_df.to_csv(output_file, index=False)

        print(f"Results saved to {output_file}")
        print(f"Total product URLs: {len(final_df)}")
    else:
        print("No product URLs found to save.")

    print(f"Total time: {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    main()