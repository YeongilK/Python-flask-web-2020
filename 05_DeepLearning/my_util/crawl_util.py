import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from flask import current_app
import pandas as pd

def siksin(place):
    url_base = 'https://www.siksinhot.com'
    url_sub = '/search?keywords=' + quote(place)
    url = url_base + url_sub
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    lis = soup.select_one('.listTy1').find('ul').find_all('li')

    rest_list = []
    for i in range(0, len(lis), 5):
        store = lis[i].select_one('.store').string
        img = lis[i].find('img').attrs['src'].split('?')[0]
        href = lis[i].find('a').attrs['href']
        url = url_base + href
        req = requests.get(url) 
        rest = BeautifulSoup(req.text, 'html.parser')
        feature = rest.select_one('.store_name_score').find('p').string
        tel = rest.select_one('.p_tel').find('p').get_text()
        addr = rest.select_one('.txt_adr').get_text()
        rest_list.append({'store':store, 'img':img, 'feature':feature,
                          'tel':tel, 'addr':addr, 'href':url})
    return rest_list

def genie():
    url = 'https://www.genie.co.kr/chart/top200'
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
    req = requests.get(url, headers = header)
    soup = BeautifulSoup(req.text, 'html.parser')
    trs = soup.select_one('.list-wrap').find('tbody').select('tr.list')

    music_list = []
    for tr in trs:
        num = tr.select_one('.number').get_text()
        rank = f'<strong>{num.split()[0]}</strong>'
        last = num.split()[1]
        if last == '유지':
            rank += '<br><small>-</small>'
        elif last.find('상승') > 0:
            rank += f'<br><small><span style="color: red;">▲{last[:-2]}</span></small>'
        else:
            rank += f'<br><small><span style="color: blue;">▼{last[:-2]}</span></small>'
        title = tr.select_one('a.title').string.strip()
        artist = tr.select_one('a.artist').string
        album = tr.select_one('a.albumtitle').string
        img = 'https:' + tr.select_one('a.cover').find('img').attrs['src']
        music_list.append({'rank':rank, 'title':title, 'artist':artist,
                            'album':album, 'img':img})
    return music_list

def interpark():
    url_base = 'http://ticket.interpark.com'
    url_sub = '/contents/Ranking/RankList?pKind=01003&pType=D'
    url = url_base + url_sub
    req = requests.get(url)
    soup = BeautifulSoup(req.text, 'html.parser')
    top3 = soup.select_one('.rankingDetailBody ').select('.rankBody.top3')
    lis = soup.select_one('.rankingDetailBody ').select('.rankBody.')

    concert_list = []
    base_href = 'https://tickets.interpark.com/goods/'
    for li in top3:
        tds = li.find_all('td')
        rank = int(tds[0].find('i').get_text())
        title = tds[0].select_one('.prdInfo').attrs['title']
        if tds[1].find('div'):
            if tds[1].find('D'):
                period = tds[1].get_text()[13:].strip()
            else:
                period = tds[1].get_text()[10:].strip()
        else:
            period = tds[1].get_text().strip()
        share = tds[2].get_text()
        href = base_href + tds[0].find('a').attrs['onclick'][4:12]
        img = tds[0].find('img').attrs['src']
        concert_list.append({'rank': rank, 'title': title, 'period': period,
                            'share': share, 'href': href, 'img': img})
        
    for li in lis:
        tds = li.find_all('td')
        rank = int(tds[0].find('i').get_text())
        title = tds[0].select_one('.prdInfo').attrs['title']
        if tds[1].find('div'):
            period = tds[1].get_text()[13:].strip()
        else:
            period = tds[1].get_text().strip()
        share = tds[2].get_text()
        href = base_href + tds[0].find('a').attrs['onclick'][4:12]
        img = tds[0].find('img').attrs['src']
        concert_list.append({'rank': rank, 'title': title, 'period': period,
                            'share': share, 'href': href, 'img': img})
    return concert_list
