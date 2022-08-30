import bs4
import requests
import re

from text_unidecode import unidecode

site = requests.get(
        "https://moovitapp.com/index/en/public_transit-lines-Israel-1-1")
soup = bs4.BeautifulSoup(site.text, 'html.parser')

    # Downloading main page and finding links
links2 = soup.select('div[class="lines-container agency-lines"] a[href]')
links=[]
def connect_mooivt(line):

    bus_lines = []

    select = line

    web = ""
    bus = re.compile(r'\d+')
    for i in range(0, len(links2)):
        # Finding link with bus number
        if (bus.search(links2[i].get('href')).group() == select):
            bus_lines.append(links2[i])

    return bus_lines

def specific_line(index):
    web = links2[int(index)].get('href')
    site = requests.get("https://moovitapp.com/index/en/" + web)
    soup = bs4.BeautifulSoup(site.text, 'html.parser')
    links = soup.select('ul[class="stops-list bordered"] h3')

    return links


def plan_drive(start,end):
    for i in links[start:end]:
        print(i)

