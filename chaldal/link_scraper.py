from bs4 import BeautifulSoup
from selenium import webdriver
import time

CLASS_NAME = "category-links-wrapper"
SCROLL_PAUSE_TIME = 0.5


def get_links(driver, sub_category_url: str, url_list: list) -> list:
    driver.get(sub_category_url)
    time.sleep(SCROLL_PAUSE_TIME)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    container = soup.find("div", {"class": CLASS_NAME})
    if not container:
        return url_list
    for link in container:
        url_list.append("https://chaldal.com"+link["href"])
    return url_list


def main():
    driver = webdriver.Chrome()
    l_list = get_links(driver, "https://chaldal.com/breakfast", [])
    print(l_list)


if __name__ == "__main__":
    main()
