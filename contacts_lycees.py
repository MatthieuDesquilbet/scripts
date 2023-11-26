import logging
import requests
import re
from bs4 import BeautifulSoup
from base_utils import setup_logger, write_csv

ENV = "local"
SEARCH_URL = "https://www.education.gouv.fr/annuaire?keywords=&department=75&academy=01&status=All&establishment=3&geo_point=&page={}"
OUT_FILE = "out/lycees_paris.csv"


def handle_lycee(lycee):
    address = lycee.find_all("p", class_="establishment--address-line")[0].string
    contact_infos = lycee.find_all("div", class_="establishment--search_item__address")
    regexp = re.compile("0(?P<tel>\d{9}).*\s(?P<email>.*@.*)$")
    search = regexp.search(" ".join(contact_infos[0].stripped_strings))

    return {
        "1_name": lycee.h2.string.strip(),
        "2_email": search.group("email"),
        "3_tel": f"+33{search.group('tel')}",
        "4_address": " ".join(re.split("\s+", address, flags=re.UNICODE)).strip(),
    }


def handle_page(page):
    a = requests.get(SEARCH_URL.format(page), timeout=10)
    soup = BeautifulSoup(a.text, "html.parser")
    lycees_from_page = []
    for lycee in soup.find_all("div", class_="etablissement"):
        lycees_from_page.append(handle_lycee(lycee))

    return lycees_from_page


def main():
    lycees = []
    for page in range(10):
        lycees += handle_page(page)
    write_csv(lycees, OUT_FILE, sort_headers=True)
    return True


if __name__ == "__main__":
    setup_logger(__file__, ENV, level=logging.INFO)
    main()
