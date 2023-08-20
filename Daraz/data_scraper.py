import argparse
import json
import logging
import time

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from tqdm import tqdm

# Constants
TITLE_CLASS_ATTR = "pdp-mod-product-badge-title"
PRICE_CLASS_ATTR = (
    "pdp-price pdp-price_type_normal pdp-price_color_orange pdp-price_size_xl"
)
PRODUCT_DIV_CLASS_ATTR = "html-content pdp-product-highlights"


# Initialize web driver that can access chrome
def initialize_browser():
    driver = webdriver.Chrome()
    logging.info("Web driver initialized")
    return driver


# helper function to scrape name
def scrape_name(soup) -> str:
    try:
        name = soup.find(
            "span", attrs={"class": TITLE_CLASS_ATTR}).text.strip()
    except AttributeError:
        logging.info(
            "AttributeError exception occured while scraping product name")
        name = ""

    return name


# helper function to scrape product price
def scrape_price(soup) -> str:
    try:
        price = soup.find(
            "span", attrs={"class": PRICE_CLASS_ATTR}).text.lstrip("৳ ")

    except AttributeError:
        logging.info(
            "AttributeError exception occured while scraping product price")
        price = ""

    return price


# helper function to scrape product details
def scrape_product_details(soup) -> str:
    try:
        product_details = ""
        outer_tag = soup.find("div", attrs={"class": PRODUCT_DIV_CLASS_ATTR})

        for li in outer_tag.find_all("li"):
            product_details += f"{li.text.strip()}. "

    except AttributeError:
        logging.info(
            "AttributeError exception occured while scraping product details")
        product_details = ""

    return product_details


def scraper(args, driver) -> dict:
    """Scrapes product name, price & product details from urls
    Args:
        args: Argument Parser object
        driver: webdriver

    Returns:
        data: python dictionary that contains product name, price & product details as keys.

    """
    if args.filepath is None:
        logging.critical("Exception has occurred, filename is None!")
        raise Exception("Filename must not be None")

    # load the url links
    with open(args.filepath, "r") as f:
        product_links = json.load(f)

    data = {
        "Product Name": [],
        "Price": [],
        "Product Details": [],
    }

    # iterate over the product urls and scrape data
    for _, link in enumerate(
        tqdm(
            product_links[args.start_index: args.limit],
            desc="scraping data from links",
        )
    ):
        if args.limit is None:
            pass
        elif args.limit < args.start_index:
            logging.warning("Limit is less than start index")
            raise Exception(
                f"""Limit cannot be less than start index\nLimit: {args.limit}, Start Index: {args.start_index}"""
            )

        driver.get("https://" + link)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        time.sleep(1.5)
        data["Product Name"].append(scrape_name(soup))
        data["Price"].append(scrape_price(soup))
        data["Product Details"].append(scrape_product_details(soup))

    return data


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="./log/scrape_data.log",
    )

    # initialize argument parser object
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--filepath", type=str, default=None, help="product link json file path"
    )
    parser.add_argument(
        "--savepath", type=str, default="Data/", help="save path for the csv file"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Threshold Value: Number of products to store in CSV",
    )
    parser.add_argument(
        "--start_index",
        type=int,
        default=0,
        help="Start index let's user explicitly state from which position to start",
    )
    args = parser.parse_args()

    start_time = time.time()

    # initialize browser
    driver = initialize_browser()
    # scrape data from urls and store in python dictionary: data
    data = scraper(args, driver)

    # create pandas dataframe from data
    dataframe = pd.DataFrame.from_dict(data)
    # handle missing values
    dataframe["Product Name"].replace("", np.nan, inplace=True)
    dataframe = dataframe.dropna(subset=["Product Name"])
    dataframe.to_csv(f"{args.savepath}.csv", header=True, index=False)
    logging.info("Dataframe object saved to csv")

    elapsed = (time.time() - start_time) / 60
    print(f"Total elapsed time: {elapsed:.2f} min")
    logging.info(f"Total elapsed time: {elapsed:.2f} min")

    # close the webdriver
    driver.quit()


if __name__ == "__main__":
    main()
