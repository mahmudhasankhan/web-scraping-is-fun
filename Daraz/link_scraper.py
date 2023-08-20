import argparse
import json
import logging
import time
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By


# initialize web driver
def initialize_browser(args):
    if args.url is None:
        logging.critical("Exception occurred")
        raise Exception("Webpage URL must not be None")
    else:
        driver = webdriver.Chrome()
        logging.info("Web driver initialized")
    return driver


# helper function that collects all the product links for a single page
def item_list_collector(driver, product_links, url):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    parent_div = soup.find("div", {"class": "box--ujueT"})

    for div in parent_div:
        for item in parent_div.find_all("a"):
            product_links.append(item["href"])
    logging.info(f"Product Link updated for page-url: {url}")
    return product_links


# function that handles data processing, filteration on the product links list
def filter_product_links(item_link_list: List[str]) -> List[str]:
    new_item_link_list = [link.removeprefix("//") for link in item_link_list]
    filtered_link_list = [
        link for link in new_item_link_list if not link.startswith("/products/")
    ]
    return list(set(filtered_link_list))


# function that collects product links from multiple webpages
def scrape_data(driver, args):
    # time
    start_time = time.time()

    driver.get(args.url)

    product_links_list = []

    time.sleep(10)
    # collect all the products links from a single webpage
    product_links_list = item_list_collector(
        driver=driver, product_links=product_links_list, url=driver.current_url
    )
    current_page_url = ""
    prev_page_url = args.url

    # until reaching the last page, collect product links and move to the next
    while True:
        try:
            driver.find_element(by=By.CLASS_NAME, value="ant-pagination-next").click()
            current_page_url = driver.current_url
            if current_page_url != prev_page_url:
                time.sleep(10)
                product_links_list = item_list_collector(
                    driver=driver,
                    product_links=product_links_list,
                    url=driver.current_url,
                )
                prev_page_url = current_page_url
            else:
                break
        except Exception as e:
            logging.critical(f"Exception {e} has occurred")
            print(f"Exception {e} has occurred")
            break
    elapsed = (time.time() - start_time) / 60
    print(f"Total elapsed time: {elapsed:.2f} min")
    logging.info(f"Total elapsed time: {elapsed:.2f} min")

    return product_links_list


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="./basic.log",
    )

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="URL of the webpage that you want to scrape data",
    )
    parser.add_argument(
        "--savepath",
        type=str,
        default="Data/",
        help="Location for saving the url json file",
    )

    args = parser.parse_args()

    # initialize the browser
    driver = initialize_browser(args)
    # scrape data and store them in a links list
    links = scrape_data(driver, args)

    # filter the links list
    updated_links = filter_product_links(links)

    print(f"Product_Link_Length:{len(updated_links)}")

    # save list object to a json file
    with open(f"{args.savepath}.json", "w") as f:
        json.dump(updated_links, f, indent=4)


if __name__ == "__main__":
    main()
