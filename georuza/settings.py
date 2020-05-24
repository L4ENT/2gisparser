import os
from pathlib import Path

MONGO_HOST = os.getenv('MONGO_HOST', 'mongo')
MONGO_PORT = int(os.getenv('MONGO_PORT', '27017'))

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

FILES_DIR = Path(os.getenv(
    'FILES_DIR',
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'files')
))

_2GIS_KEY = os.getenv('2GIS_KEY', 'russpc1826')
_2GIS_API2_URL = os.getenv('2GIS_API2_URL', 'http://catalog.api.2gis.ru/2.0/')
_2GIS_API3_URL = os.getenv('2GIS_API2_URL', 'http://catalog.api.2gis.ru/3.0/')
_2GIS_API_URLS = {
    2: _2GIS_API2_URL,
    3: _2GIS_API3_URL
}

SELENIUM_COMMAND_EXECUTOR_URL = 'http://selenium.139.162.210.217.nip.io/wd/hub'
