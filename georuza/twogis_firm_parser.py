import contextlib
import json
from urllib.parse import quote, urlparse
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
        print(f'Start parse {ribric["name"]} {url}')
        self._driver.get(url)
        elements = self._driver.find_elements_by_css_selector(
            '._awwm2v ._y3rccd'
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

            with contextlib.suppress(NoSuchElementException):
                twogis_site_a_el = el.find_element_by_css_selector('._13ptbeu')
                data['2gis_url'] = twogis_site_a_el.get_attribute('href')

            with contextlib.suppress(NoSuchElementException):
                category_el = el.find_element_by_css_selector('._oqoid')
                # print(self.parse_style_attribute(style))
                data['category'] = category_el.text

            with contextlib.suppress(NoSuchElementException):
                data['rating'] = None
                rating_cont_el = el.find_element_by_css_selector('._e296pg')
                pos_container = rating_cont_el.find_element_by_css_selector(
                    '._tjufnr'
                )
                data['rating'] = len(
                    pos_container.find_elements_by_css_selector(
                        'span'
                    )
                )

            with contextlib.suppress(NoSuchElementException):
                reviews_count_el = el.find_element_by_css_selector('._uzv9b5')
                try:
                    data['reviews_count'] = int(reviews_count_el.text)
                except Exception:
                    pass

            try:
                not_working_el = el.find_element_by_css_selector('._bdr0ip')
                not_work_text = not_working_el.text
            except NoSuchElementException:
                data['closed'] = False
            else:
                data['closed'] = 'не' in not_work_text.lower()

            # print(data['closed'])

            if data.get('name'):
                self._db.orgs.insert_one(data)

        self._visited_pages.append(url)

    def fetch(self, ribric):
        self._pages_to_visit.add(f'https://2gis.ru/khabarovsk/search/'
                                 f'{quote(ribric["title"])}')
        while self._pages_to_visit:
            url = self._pages_to_visit.pop()
            self.parse_page(url, ribric)
            self.get_pages_to_visit()

    def fetch_all_rubrics(self):
        with open(settings.FILES_DIR / 'rubrics-choice-2.json') as f:
            rubrics = json.loads(f.read())
        for rubric in sorted(
                rubrics, key=lambda x: x['org_count'], reverse=True):
            rubric_name = rubric['name']
            print(f'Start parse rubric {rubric_name}')
            self.fetch(rubric)
            print(f'Rubric {rubric_name} done')

    def get_firm_id_from_url(self, url: str):
        url_obj = urlparse(url)
        re_result = re.search(r'/khabarovsk/firm/(.*)', url_obj.path)
        if (re_result):
            firm_id, _ = re_result.groups()
        else:
            firm_id = None
        return firm_id

    def reset_firm_id_for_all_orgs(self):
        orgs_with_url = self._db.orgs.find({'2gis_url': {'$exists': True}})
        for org in orgs_with_url:
            firm_id =self.get_firm_id_from_url(org['2gis_url'])
            print(f'NAME: {org["name"]} FIRM ID: {firm_id}')
            if firm_id:
                org['firm_id'] = firm_id
                self._db.orgs.save(org)

    def fetch_firm_info(self, firm_id):
        self._driver.get(f'https://2gis.ru/firm/{firm_id}')
        initial_state = self._driver.execute_script('return initialState;')
        print(initial_state)


def main():
    fetcher = DataFetcher(get_db())
    fetcher.fetch_all_rubrics()


main()
