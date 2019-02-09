from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup as bs
from bs4 import Comment
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote import webelement
from helpers import get_city_code
import sys


options = Options()
options.add_argument("--window-size=1920x1700")


class OneWayTrip:
    def __init__(self, **kwargs):
        """
        one way trip initialization
        """

        # user input
        self.flight_data = kwargs

        # flight source and target
        self.flight_data['from'] = get_city_code(self.flight_data['from'])
        self.flight_data['to'] = get_city_code(self.flight_data['to'])

        # input validation
        self.input_validator()

        # url create
        self.url = self.url_maker()

        # all airlines extracted data container
        self.airlines_query_result = {}

        # web driver initialization
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)

        # pipeline call
        self.run()

    def run(self):
        if self.get_url():
            return

        page = self.driver.page_source
        soup = bs(page, "html.parser")
        data = soup.find_all("div", class_="top_first_part")
        self.get_all_flight_data(data)
        time.sleep(3)

        # search logic on the bases of flight number
        try:
            element = self.driver.find_element_by_xpath(f"//*[contains(text(), '{self.flight_data['flight_number']}')]//ancestor::div[2]//*[contains(text(), 'Book')]")

            print("Booking started..")
            self.driver.execute_script("arguments[0].scrollIntoView();", element)

            if isinstance(element, webelement.WebElement):
                element.click()

            time.sleep(3)

            # screen shot
            self.driver.get_screenshot_as_file(f"screen_shots/{self.flight_data['flight_number']}_booking_screenshot.png")
        except NoSuchElementException:
            print("Booking not Find")
            return

        self.get_final_fare()

    def get_text(self, element_src):
        soup = bs(element_src, "html.parser")
        return ' '.join(item.strip() for item in soup.findAll(text=True))

    def get_final_fare(self):
        try:
            self.fare_detail_element = dict()

            total_base_fare = self.driver.find_element_by_xpath('//*[contains(text(), "Total Base Fare")]//following::span[1]').get_attribute("innerHTML")
            self.fare_detail_element['total_base_fare'] = self.get_text(total_base_fare)

            taxes_and_surcharges = self.driver.find_element_by_xpath('//*[contains(text(), "Taxes & Surcharges")]//following::span[1]').get_attribute("innerHTML")
            self.fare_detail_element['taxes_and_surcharges'] = self.get_text(taxes_and_surcharges)

            total_services = self.driver.find_element_by_xpath('//*[contains(text(), "TOTAL SERVICES")]//following::span[1]').get_attribute("innerHTML")
            self.fare_detail_element['total_services'] = self.get_text(total_services)

            grand_total = self.driver.find_element_by_xpath('//*[contains(text(), "GRAND TOTAL")]//following::span[1]').get_attribute("innerHTML")
            self.fare_detail_element['grand_total'] = self.get_text(grand_total)

            print(f"********* Final Make My Trip Fare Details for flight {self.flight_data['flight_number']} ***********")
            print(self.fare_detail_element)
            print("********* End ***********")
        except NoSuchElementException:
            print("element not found")
            return

    def get_all_flight_data(self, data):
        print("********** Airlines Data **************")
        for item in data:
            item = str(item)
            soup = bs(item, "html.parser")
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))

            for comment in comments:
                try:
                    if comment.strip() == 'Logo':
                        self.airlines_query_result["air_line"] = comment.find_next("span", class_="logo_name").getText()
                        self.airlines_query_result["flight_number"] = comment.find_next("span", class_="flt_number").getText()
                        # print(comment)
                    elif comment.strip() == 'Departure':
                        self.airlines_query_result["departure"] = comment.find_next("span", class_="timeCa").getText()
                        self.airlines_query_result["from"] = comment.find_next("span", class_="city_name").getText()
                        # print(comment)
                    elif comment.strip() == 'Arrival':
                        self.airlines_query_result["arrival"] = comment.find_next("span", class_="timeCa").getText()
                        self.airlines_query_result["to"] = comment.find_next("span", class_="city_name").getText()
                        # airlines_query_result(comment)
                    elif comment.strip() == 'Duration':
                        self.airlines_query_result["duration"] = comment.find_next("span", class_="timeCa").getText()
                        # print(comment)
                    elif comment.strip() == 'Price':
                        self.airlines_query_result['price'] = comment.find_next("p", class_="price_info").getText()

                except AttributeError as e:
                    pass

            print(self.airlines_query_result)
        print("************ End **************")

    def input_validator(self):
        if self.flight_data["to"] == self.flight_data["from"] or \
        self.flight_data['to'] == '' or self.flight_data['from'] == '':
            raise ValueError("provided flight source and target is not valid.")

        if self.flight_data['trip_type'] == '' or self.flight_data['trip_type'].upper() not in ['O', 'R']:
            raise ValueError("provided flight trip type is not valid.")

        if self.flight_data['class_type'] == '' or self.flight_data['class_type'].upper() not in ['E', 'B', 'PE']:
            raise ValueError("provided flight class type is not valid.")

        if self.flight_data['flight_number'] == '':
            raise ValueError("flight number should not be empty")

        if self.flight_data['pa'] + self.flight_data['pc'] + self.flight_data['pi'] == 0 or \
            self.flight_data['pa'] + self.flight_data['pc'] + self.flight_data['pi'] > 9 or \
            self.flight_data['pa'] < self.flight_data['pi'] or self.flight_data['pa'] < self.flight_data['pc']:
            raise ValueError("provided number of passengers are not valid.")

    def url_maker(self):
        url = f"https://flights.makemytrip.com/makemytrip/search/" \
              f"{self.flight_data['trip_type'].upper()}/{self.flight_data['trip_type'].upper()}/" \
              f"{self.flight_data['class_type'].upper()}/" \
              f"{str(self.flight_data['pa'])}/{str(self.flight_data['pc'])}/{str(self.flight_data['pi'])}/S/V0/" \
              f"{self.flight_data['from']}_{self.flight_data['to']}_{self.flight_data['trip_date']}" \
              f"?contains=false&remove="

        return url

    def get_url(self):
        self.driver.get(self.url)
        time.sleep(5)
        curr_url = self.driver.current_url

        if 'error/NO_FLIGHTS' in curr_url:
            print("No flights found")
            return True
        else:
            return False

    def quit(self):
        self.driver.quit()


class RoundTrip:
    def __init__(self, **kwargs):
        """
        round trip initialization
        """
        # User input
        self.flight_data = kwargs

        # flight source and target both side
        self.flight_data['o_from'] = get_city_code(self.flight_data['o_from'])
        self.flight_data['o_to'] = get_city_code(self.flight_data['o_to'])
        self.flight_data['r_from'] = get_city_code(self.flight_data['r_from'])
        self.flight_data['r_to'] = get_city_code(self.flight_data['r_to'])

        # input validation
        self.input_validator()

        # url create
        self.url = self.url_maker()

        # web driver initialization
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)

        # pipeline call
        self.run()

    def run(self):
        if self.get_url():
            return

        # search logic on the bases of flight number
        print(f"Finding booking for dep:{self.flight_data['o_flight_number']} and ret: {self.flight_data['r_flight_number']}")

        try:
            dep_flights = "_".join([flight.replace("-", "_") for flight in self.flight_data['o_flight_number']])
            element1 = self.driver.find_element_by_xpath(f'//*[@id="dep-{dep_flights}_"]')

            if isinstance(element1, webelement.WebElement):
                element1.click()

            # for scroll screen
            # self.driver.execute_script("arguments[0].scrollIntoView();", element)

        except NoSuchElementException:
            print("Booking for departure not Available")
            return

        try:
            ret_flights = "_".join([flight.replace("-", "_") for flight in self.flight_data['r_flight_number']])
            element2 = self.driver.find_element_by_xpath(f'//*[@id="ret-{ret_flights}_"]')

            if isinstance(element2, webelement.WebElement):
                element2.click()
        except NoSuchElementException:
            print("Booking for return not Available")
            return

        # for booking

        try:
            booking_element = self.driver.find_element_by_xpath('//*[@id="content"]/div/div[4]/div[1]/div[1]/div[3]/div[3]/div/div[2]/span/span/a')
            # booking_element = self.driver.find_element_by_xpath('//span[contains(text(), "Book")]')
            print("Booking Available")
            print(booking_element.get_attribute("innerHTML"))
            if isinstance(booking_element, webelement.WebElement):
                booking_element.click()

                time.sleep(3)

                # for screen shot
                self.driver.get_screenshot_as_file(
                    f"screen_shots/{self.flight_data['o_flight_number']}_{self.flight_data['r_flight_number']}_booking_screenshot.png")
                self.get_final_fare()
        except NoSuchElementException:
            print("Booking not Available")
            return

    def input_validator(self):
        if self.flight_data["o_to"] == self.flight_data["o_from"] or \
        self.flight_data["r_to"] == self.flight_data["r_from"] or \
        self.flight_data['o_to'] == '' or self.flight_data['o_from'] == '' or \
        self.flight_data['r_to'] == '' or self.flight_data['r_from'] == '':
            raise ValueError("provided flight source and target are not valid.")

        if self.flight_data['trip_type'] == '' or self.flight_data['trip_type'].upper() not in ['O', 'R']:
            raise ValueError("provided flight trip type is not valid.")

        if self.flight_data['class_type'] == '' or self.flight_data['class_type'].upper() not in ['E', 'B', 'PE']:
            raise ValueError("provided flight class type is not valid.")

        if self.flight_data['o_flight_number'] == '' or self.flight_data['r_flight_number'] == '':
            raise ValueError("flight number should not be empty")

        if self.flight_data['pa'] + self.flight_data['pc'] + self.flight_data['pi'] == 0 or \
            self.flight_data['pa'] + self.flight_data['pc'] + self.flight_data['pi'] > 9 or \
            self.flight_data['pa'] < self.flight_data['pi'] or self.flight_data['pa'] < self.flight_data['pc']:
            raise ValueError("provided number of passengers are not valid.")

        else:
            pass

    def url_maker(self):
        url = f"https://flights.makemytrip.com/makemytrip/search/" \
              f"{self.flight_data['trip_type'].upper()}/{self.flight_data['trip_type'].upper()}/" \
              f"{self.flight_data['class_type'].upper()}/" \
              f"{str(self.flight_data['pa'])}/{str(self.flight_data['pc'])}/{str(self.flight_data['pi'])}/S/V0/" \
              f"{self.flight_data['o_from']}_{self.flight_data['o_to']}_{self.flight_data['o_trip_date']}," \
              f"{self.flight_data['r_from']}_{self.flight_data['r_to']}_{self.flight_data['r_trip_date']}" \
              f"?contains=false&remove="

        return url

    def get_url(self):
        self.driver.get(self.url)
        time.sleep(5)
        curr_url = self.driver.current_url

        if 'error/NO_FLIGHTS' in curr_url:
            print("No flights found")
            return True
        else:
            return False

    def get_text(self, element_src):
        soup = bs(element_src, "html.parser")
        return ' '.join(item.strip() for item in soup.findAll(text=True))

    def get_final_fare(self):
        try:
            self.fare_detail_element = dict()

            total_base_fare = self.driver.find_element_by_xpath('//*[contains(text(), "Total Base Fare")]//following::span[1]').get_attribute("innerHTML")
            self.fare_detail_element['total_base_fare'] = self.get_text(total_base_fare)

            taxes_and_surcharges = self.driver.find_element_by_xpath('//*[contains(text(), "Taxes & Surcharges")]//following::span[1]').get_attribute("innerHTML")
            self.fare_detail_element['taxes_and_surcharges'] = self.get_text(taxes_and_surcharges)

            total_services = self.driver.find_element_by_xpath('//*[contains(text(), "TOTAL SERVICES")]//following::span[1]').get_attribute("innerHTML")
            self.fare_detail_element['total_services'] = self.get_text(total_services)

            grand_total = self.driver.find_element_by_xpath('//*[contains(text(), "GRAND TOTAL")]//following::span[1]').get_attribute("innerHTML")
            self.fare_detail_element['grand_total'] = self.get_text(grand_total)

            print(f"********* Final Make My Trip Fare Details for flight {self.flight_data['o_flight_number']} and {self.flight_data['r_flight_number']} ***********")
            print(self.fare_detail_element)
            print("********* End ***********")
        except NoSuchElementException:
            print("element not found")
            return

    def quit(self):
        self.driver.quit()


class MultiCityTrip:
    def __init__(self):
        """
        multi city trip initialization
        """
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)

    def url_maker(self):
        pass

    def quit(self):
        self.driver.quit()


def main():
    one_way_input = {
        "trip_type": 'O',
        "class_type": 'e',
        "pa": 1,
        "pc": 0,
        "pi": 0,
        "from": "Mumbai",
        "to": "Delhi",
        "trip_date": '10-02-2019',
        "flight_number": "9W-762"
    }

    two_way_input = {
        "trip_type": "R",
        "class_type": "E",
        "pa": 1,
        "pc": 0,
        "pi": 0,
        "o_from": "Mumbai",
        "o_to": "Delhi",
        "o_trip_date": '13-02-2019',
        "o_flight_number": ["SG-635", "8912"],
        "r_from": "Delhi",
        "r_to": "Mumbai",
        "r_trip_date": "17-02-2019",
        "r_flight_number": ["SG-153"],
    }

    # one_obj = OneWayTrip(**one_way_input)
    two_obj = RoundTrip(**two_way_input)
    # del one_obj


if __name__ == '__main__':
    main()
