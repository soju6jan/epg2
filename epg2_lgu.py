import os, sys, traceback, requests, lxml.html, re
from datetime import datetime, timedelta
from .plugin import P, logger, db, d
from .model import ModelEpg2Program
from support.base.util import default_headers



class Epg2Lgu(object):
    @classmethod
    def make_epg(cls, channel):
        try:
            url = 'http://www.uplus.co.kr/css/chgi/chgi/RetrieveTvSchedule.hpi'
            current_dt = datetime.now()
            epg_data = []
            for day in range(6):
                param_dt = current_dt + timedelta(days=day) 
                post_data = {'chnlCd': channel.lgu_id, 'evntCmpYmd': param_dt.strftime('%Y%m%d')}

                html = requests.post(url, headers=default_headers, data=post_data).text
                root = lxml.html.fromstring(html)
                tags = root.xpath('//div[2]/table/tbody/tr')
                for tag in tags:
                    tds = tag.xpath('td')
                    epg_data.append({
                        'start_time': f"{post_data['evntCmpYmd']} {tds[0].text_content().strip()}",
                        'genre': tds[2].text_content().strip(),
                        'title': tds[1].text.strip(),
                        'age': tds[1].xpath('span/span[@class="tag cte_all"]/text()')[0],
                    })

            for idx, item in enumerate(epg_data):
                p = ModelEpg2Program()
                p.channel = channel
                p.start_time = datetime.strptime(item['start_time'], '%Y%m%d %H:%M')
                if idx == len(epg_data)-1:
                    p.end_time = datetime.strptime(p.start_time.strftime('%Y%m%d') + ' 23:59', '%Y%m%d %H:%M')
                else:
                    p.end_time = datetime.strptime(epg_data[idx+1]['start_time'], '%Y%m%d %H:%M')
                
                match = re.match(r'(?P<title>.*?)\s\[(?P<part>\d+)부\]', item['title'])
                if match:
                    p.title = match.group('title').strip()
                    p.part_number = match.group('part')
                else:
                    tmp = item['title']
                    if '<재>' in item['title']:
                        p.re = True
                        tmp = tmp.replace('<재>', '').strip()
                    
                    match = re.match(r'(?P<title>.*?)\s\((?P<part>\d+)회\)', item['title'])
                    if match:
                        p.title = match.group('title').strip()
                        p.episode_number = match.group('part')
                    else:
                        p.title = item['title']
                        
                p.rate = '모든 연령 시청가' if item['age'] == 'All' else f"{item['age']}세 이상 시청가"
                p.genre = item['genre']
                if item['genre'] == '영화':
                    p.is_movie = True
                db.session.add(p)
            logger.warning(f"LGU {channel.name} {len(epg_data)}개 추가")
            return True
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return False

