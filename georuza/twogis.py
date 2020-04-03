import contextlib
import json
from urllib.parse import quote_plus
from pymongo import MongoClient
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import re

from georuza import settings


def get_db():
    client = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
    return client['georuza_2gis']


class DataFetcher:

    def __init__(self, db) -> None:
        self._driver = webdriver.Chrome()
        self._db = db
        self._visited_pages = []
        self._pages_to_visit = set()
        self._loaded_rubrics = {}

    @staticmethod
    def parse_style_attribute(style_string: str):
        if 'background-image' in style_string:
            result = re.search(r'.*background-image: url\(\"('
                               r'?P<url>.*)\"\).*', style_string)
            if result:
                return result.group('url')
            else:
                return None
        return None

    def get_pages_to_visit(self):
        links = self._driver.find_elements_by_css_selector('a._1hs4dnvh')
        paths_on_page = set((x.get_attribute('href') for x in links))
        self._pages_to_visit.update(paths_on_page - set(self._visited_pages))

    def parse_page(self, url, ribric):
        print(f'Start parse {ribric} {url}')
        self._driver.get(url)
        elements = self._driver.find_elements_by_css_selector(
            '._awwm2v ._1h8gq0d'
        )
        for el in elements:
            data = {
                'ribric': ribric
            }
            with contextlib.suppress(NoSuchElementException):
                title_el = el.find_element_by_css_selector('._hc69qa')
                # print(title_el.text)
                data['name'] = title_el.text
            with contextlib.suppress(NoSuchElementException):
                address_element = el.find_element_by_css_selector('._tluih8')
                # print(address_element.text)
                data['address'] = address_element.text

            with contextlib.suppress(NoSuchElementException):
                image_el = el.find_element_by_css_selector('._1dk5lq4')
                style = image_el.get_attribute('style')
                # print(self.parse_style_attribute(style))
                data['image_url'] = self.parse_style_attribute(style)

            try:
                not_working_el = el.find_element_by_css_selector('._bdr0ip')
                not_work_text = not_working_el.text
            except NoSuchElementException:
                data['closed'] = False
            else:
                data['closed'] = 'не' in not_work_text.lower()

            # print(data['closed'])

            if data.get('name'):
                self._db.organizations.insert_one(data)

        self._visited_pages.append(url)


    def fetch(self, ribric='Поесть'):
        self._pages_to_visit.add(f'https://2gis.ru/khabarovsk/search/'
                                 f'{quote_plus(ribric)}')
        while self._pages_to_visit:
            url = self._pages_to_visit.pop()
            self.parse_page(url, ribric)
            self.get_pages_to_visit()

    def fetch_all_rubrics(self):
        with open(settings.FILES_DIR / '2gis-rubrics-data.json') as f:
            rubrics = json.loads(f.read())
        for rubric in rubrics:
            rubric_name = rubric['name']
            print(f'Start parse rubric {rubric_name}')
            self.fetch(rubric_name)
            print(f'Rubric {rubric_name} done')
            self._db.organizations.insert_one({
                'name': rubric_name,
                'loaded': True
            })

def main():
    fetcher = DataFetcher(get_db())
    fetcher.fetch_all_rubrics()

main()