from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm
import time
import logging
import argparse
import pandas as pd
import numpy as np
import re
from link_scraper import get_links


# initialize web driver
def initialize_browser(args):
    if args.url is None:
        logging.critical("Exception occurred")
        raise Exception("Webpage URL must not be None")
    else:
        driver = webdriver.Chrome()
        logging.info("Web driver initialized")
    return driver


# scroll down to bottom of the page
def scroll_down(driver):
    SCROLL_PAUSE_TIME = 0.5

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# scrape product name
def scrape_name(tag) -> str:
    try:
        name = tag.find("div", attrs={"class": "name"}).text
    except AttributeError:
        logging.info(
            "AttributeError exception occured while scraping product name")
        name = ""

    return name


# helper function to scrape product price
def scrape_price(tag) -> str:
    try:
        price = tag.find("div", attrs={"class": "price"}).text
        price = re.sub("৳", "Tk", price)
    except AttributeError:
        logging.info(
            "AttributeError exception occured while scraping product price")
        price = ""

    return price


# helper function to scrape product volume
def scrape_volume(tag) -> str:
    try:
        volume = tag.find("div", attrs={"class": "subText"}).text
    except AttributeError:
        logging.info(
            "AttributeError exception occured while scraping product volume")
        volume = ""

    return volume


# scrapes data
def scrape_data(driver, url) -> dict:
    # time

    driver.get(url)

    time.sleep(3)

    scroll_down(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    parent_div = soup.find("div", {"class": "productPane"})

    if not parent_div:
        try:
            driver.find_element(by=By.CLASS_NAME, value='btn-primary').click()
        except Exception as e:
            print(f"An exception {e} has occurred")
        driver.refresh()
        soup = BeautifulSoup(driver.page_source, "html.parser")
        parent_div = soup.find("div", {"class": "productPane"})

    data = {
        "Product Name": [],
        "Price": [],
        "Product Weight": []
    }

    for div in parent_div:
        data["Product Name"].append(scrape_name(div))
        data["Price"].append(scrape_price(div))
        data["Product Weight"].append(scrape_volume(div))

    logging.info(f"Total Product Count: {len(parent_div)} for URL: {url}")

    return data


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="URL of the sub category webpage that you want to scrape data")
    args = parser.parse_args()

    sub_category_api_endpoint = re.sub('.*?/', '', args.url)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        filename=f"logs/{sub_category_api_endpoint}.log")
    # initialize the browser
    driver = initialize_browser(args)
    start_time = time.time()
    category_links = get_links(driver, args.url, [])
    if len(category_links) == 0:
        data = scrape_data(driver, args.url)
        dataframe = pd.DataFrame.from_dict(data)
        dataframe['Product Name'].replace('', np.nan, inplace=True)
        dataframe = dataframe.dropna(subset=['Product Name'])
        dataframe.to_csv(f"data/{re.sub('.*?/', '', args.url)}.csv",
                         header=True,
                         index=False)
        logging.info(
            f"Dataframe object saved to data/{re.sub('.*?/', '', args.url)}.csv")

        elapsed = (time.time() - start_time) / 60
        logging.info(f'Total elapsed time: {elapsed:.2f} min')
        driver.quit()
        return

    logging.info(
        f"{sub_category_api_endpoint} subcategory contains {len(category_links)} links")
    # scrape data and store them in a links list
    for _, link in enumerate(tqdm(category_links, desc=f"scraping data from category {sub_category_api_endpoint}")):
        logging.info(f"Scraping from sub-category URL: {args.url}")
        data = scrape_data(driver, link)
        dataframe = pd.DataFrame.from_dict(data)
        dataframe['Product Name'].replace('', np.nan, inplace=True)
        dataframe = dataframe.dropna(subset=['Product Name'])
        dataframe.to_csv(f"data/{re.sub('.*?/', '', link)}.csv",
                         header=True,
                         index=False)
        logging.info(
            f"Dataframe object saved to data/{re.sub('.*?/', '', link)}.csv")

    elapsed = (time.time() - start_time) / 60
    logging.info(f'Total elapsed time: {elapsed:.2f} min')

    # close the webdriver
    driver.quit()


if __name__ == "__main__":
    main()
