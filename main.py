import logging
import re
import ssl
import time
from urllib import request
import bs4
from bs4 import BeautifulSoup as soup
from urllib.parse import quote


logging.basicConfig(
    format="%(levelname)s >>> %(asctime)s - %(message)s [%(lineno)s]",
    level=logging.DEBUG,
    handlers=[logging.StreamHandler()]
)


def web_search(ot, to, date):
    logging.info('web search')
    url = f'https://atlasbus.by/Маршруты/{ot}/{to}?date={date}'
    url = quote(url, safe=':/?=&')

    time_a = time.time()

    client = request.urlopen(url, context=ssl._create_unverified_context())
    html = client.read()
    client.close()

    time_b = time.time()

    logging.debug(time_b - time_a)

    return html


def parse(html):
    logging.info('start parsing')
    page = soup(html, 'html.parser')
    blocks = page.findAll(string="Заказать")

    if blocks and blocks[0] is None:
        logging.error('no blocks')
        return []

    return map(lambda parent: re.search(r'\b\d{2}:\d{2}\b', str(parent.parent.parent.parent.parent.parent.parent.parent)), blocks)

def convert_time(hhmm):
    return int(hhmm.split(':')[0]) * 60 + int(hhmm.split(':')[1])

def afk_search(time_range, ot, to, date):
    logging.debug(f'{ot}/{to}/{date} - {time_range}')
    logging.info('start afk')
    time_min = convert_time(time_range[0])
    time_max = convert_time(time_range[1])
    while True:
        time_list = parse(web_search(ot, to, date))
        logging.warning(time_list)
        time.sleep(10)
        bus_list = map(lambda t: convert_time(t.group()) if time_min <= convert_time(t.group()) <= time_max else None, time_list)
        bus_list = filter(lambda b: b is not None, bus_list)
        resp = [f'{res // 60}:{res % 60 if res % 60 != 0 else '00'}' for res in bus_list]
        if resp:
            return
        else:
            logging.warning(resp)

print(afk_search(['10:00', '10:10'], ot="Минск", to="Слуцк", date="2024-12-20"))


