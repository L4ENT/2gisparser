import json
from itertools import count
from urllib.parse import urljoin

import redis
import requests
from pymongo import MongoClient
from requests import HTTPError

from georuza import parings_hashes
from georuza import settings
from georuza.loggers import logger


def get_db():
    client = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
    return client['georuza_2gis']


class Cache:
    PARSING_SUCCESS = 'PARSING_SUCCESS'
    PARSING_EXPIRED = 'PARSING_EXPIRED'
    PARSING_FAILED = 'PARSING_FAILED'

    def __init__(self) -> None:
        self._backend = redis.Redis(settings.REDIS_HOST, settings.REDIS_PORT)

    def set(self, key, value):
        return self._backend.set(key, value)

    def get(self, key):
        return self._backend.get(key)

    def drop(self, key):
        return self._backend.delete(key)

    def was_parsed(self, hash_key):
        data = self.get(hash_key)
        return data and data.decode() in (
            self.PARSING_SUCCESS, self.PARSING_EXPIRED
        )

    def parsing_is_success(self, hash_key):
        data = self.get(hash_key)
        return data and data.decode() == self.PARSING_SUCCESS

    def parsing_is_failed(self, hash_key):
        data = self.get(hash_key)
        return data and data.decode() == self.PARSING_FAILED

    def _parsing_set(self, hash_key, parse_status):
        return self.set(hash_key, parse_status)

    def parsing_success(self, hash_key):
        return self._parsing_set(hash_key, self.PARSING_SUCCESS)

    def parsing_failed(self, hash_key):
        return self._parsing_set(hash_key, self.PARSING_FAILED)


    def parsing_failue(self, hash_key):
        self.set(hash_key, 1)

class DataFetcher:

    def __init__(self, db, cache) -> None:
        self._db = db
        self._cache: Cache = cache
        self.requests_count = 0

    def fetch(self, path: str, params: dict = None, api_version:int = 2):
        get_params = {'key': settings._2GIS_KEY}
        get_params.update(params)
        response = requests.get(
            urljoin(settings._2GIS_API_URLS[api_version], path),
            params=get_params
        )
        self.requests_count += 1
        response_json = response.json()
        if not response_json['meta']['code'] in (200, 201):
            error = response_json['meta'].get('error')
            message = error and error['message'] or 'Request error.'
            raise HTTPError(message, response=response)
        return response_json

    def fetch_branches(self, region_id:int):
        with open(settings.FILES_DIR / '2gis-rubrics-data.json') as f:
            rubrics = json.loads(f.read())
        for rubric in rubrics:
            self.fetch_branches_by_rubric(rubric, region_id)


    def fetch_branches_by_rubric(
            self, rubric: dict, region_id: int, start_page:int = 1):
        page_size = 50
        total = rubric['branch_count']
        for page_num in count(start_page):
            rubric_id = int(rubric['id'])
            rubric_name = rubric['name']

            params = {
                'rubric_id': rubric_id,
                'page': page_num,
                'page_size': page_size,
                'region_id': region_id
            }

            hash_key = parings_hashes.rubric_page_parsing_hash(params)

            if not self._cache.was_parsed(hash_key):
                try:
                    data = self.fetch('catalog/branch/list', params)
                except (requests.exceptions.ConnectionError, HTTPError) as ex:
                    self._cache.parsing_failed(hash_key)
                    logger.warning(f'{rubric_name} page {page_num} failed.')
                    raise ex
                else:
                    branches = data['result']['items']
                    for branch in branches:
                        self._db.branches.insert_one(branch)
                    total = data['result']['total'] or 0
                    self._cache.parsing_success(hash_key)
            else:
                logger.warning(f'{rubric_name} page {page_num} passed.')


            if page_size * page_num >= total:
                logger.info(
                    f'[SUCCESS] {rubric_name}'
                    f': pages={page_num}'
                    f': requests={self.requests_count}'
                )
                break


def main():
    fetcher = DataFetcher(get_db(), Cache())
    fetcher.fetch_branches(35)

main()