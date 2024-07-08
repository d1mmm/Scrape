import sys
import time

import pandas as pd
from selenium import webdriver
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import logging

logging.basicConfig(filename='scraping.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def wait_click(driver, key, value):
    try:
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((key, value))).click()
    except TimeoutException as timeout:
        logging.error(timeout)


def add_options_to_query(driver, parsed_data):
    logging.info(f"Set the type of transport {parsed_data[0]}")
    driver.find_element(By.CLASS_NAME, "e-form").send_keys(parsed_data[0])

    logging.info(f"Set the brand of transport {parsed_data[1]}")
    driver.find_element(By.ID, "brandTooltipBrandAutocompleteInput-brand").send_keys(parsed_data[1])
    wait_click(driver, By.XPATH, "//*[@id='brandTooltipBrandAutocomplete-brand']/ul/li/a")

    logging.info(f"Set the model of transport {parsed_data[2]}")
    driver.find_element(By.ID, "brandTooltipBrandAutocompleteInput-model").send_keys(parsed_data[2])
    wait_click(driver, By.XPATH, "//*[@id='brandTooltipBrandAutocomplete-model']/ul/li/a")

    logging.info(f"Set the region {parsed_data[3]}")
    driver.find_element(By.ID, "brandTooltipBrandAutocompleteInput-region").send_keys(parsed_data[3])
    wait_click(driver, By.XPATH, "//*[@id='brandTooltipBrandAutocomplete-region']/ul/li/a")

    wait_click(driver, By.CLASS_NAME, "wrap-pseudoelement")
    logging.info(f"Set the year from {parsed_data[4]}")
    driver.find_element(By.ID, "yearFrom").send_keys(parsed_data[4])
    logging.info(f"Set the year till {parsed_data[5]}")
    driver.find_element(By.ID, "yearTo").send_keys(parsed_data[5])
    wait_click(driver, By.CLASS_NAME, "wrap-pseudoelement")

    wait_click(driver, By.XPATH, "//*[@id='mainSearchForm']/div[2]/div[2]/div[3]")
    logging.info(f"Set the price from {parsed_data[6]}")
    driver.find_element(By.ID, "priceFrom").send_keys(parsed_data[6])
    logging.info(f"Set the price to {parsed_data[7]}")
    driver.find_element(By.ID, "priceTo").send_keys(parsed_data[7])
    wait_click(driver, By.XPATH, "//*[@id='mainSearchForm']/div[2]/div[2]/div[3]")

    logging.info("Search...")
    wait_click(driver, By.XPATH, "//*[@id='mainSearchForm']/div[3]/button")


def get_phone(driver):
    wait_click(driver, By.CLASS_NAME, "phones_item")
    phone = driver.find_element(By.CLASS_NAME, "popup-successful-call-desk").text
    driver.back()
    return phone


def save_csv_data(df, name):
    logging.info(f"Save data to {name}")
    df.to_csv(name, index=False)


def save_pd_data(data):
    df = pd.DataFrame(data)
    df.index += 1
    save_csv_data(df, "autoria.csv")


def get_info(driver, parsed_data):
    logging.info(f"Add options to search")
    add_options_to_query(driver, parsed_data)
    data = []

    for index in range(int(parsed_data[8])):
        if index == 20:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.page-link[data-page='1']")))
            url = next_button.get_attribute("href")
            logging.info("Move to the next page")
            driver.get(url)
            index = 0

        logging.info("Update all records on the page")
        records = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "section.ticket-item"))
        )

        driver.execute_script("arguments[0].scrollIntoView();", records[index])

        title = records[index].find_element(By.CLASS_NAME, "head-ticket").text
        logging.info(f"Get the title {title}")
        description = records[index].find_element(By.CLASS_NAME, "descriptions-ticket").text
        logging.info(f"Get the description {description}")
        wait_click(records[index], By.CLASS_NAME, "head-ticket")
        phone = get_phone(driver)
        logging.info(f"Get the phone {phone}")
        time.sleep(1)

        data.append({"Tittle": title, "Phone Number": phone, "Description": description})

    return save_pd_data(data)


def main(parsed_data):
    try:
        logging.info("Init webdriver")
        driver = webdriver.Chrome()
        logging.info("Go to https://auto.ria.com/")
        driver.get("https://auto.ria.com/")
        get_info(driver, parsed_data)
    except WebDriverException as web:
        logging.error(web)
    finally:
        logging.info("Webdriver close")
        driver.quit()


if __name__ == "__main__":
    try:
        arguments = sys.argv[1:]
        input_string = " ".join(arguments)
        parsed_data = [item.strip() for item in input_string.split(',')]
        if len(parsed_data) != 9:
            logging.error("The data is incorrect. Please enter the correct information\n"
                          "Such as: Type of transport Brand Model City Year From Year Till Price From Price To "
                          "Quantity of records\n"
                          "Example: Легкові Audi Q5 Київ 2018 2018 0 40000, 2")
            exit(-1)
        main(parsed_data)
    except Exception as e:
        logging.error(e)
