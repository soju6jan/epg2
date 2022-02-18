import os, sys, traceback, requests, lxml.html, re
from datetime import datetime, timedelta
from .plugin import P, logger, db, d
from .model import ModelEpg2Program
from support.base.util import default_headers



class Epg2Kt(object):
    @classmethod
    def make_epg(cls, channel):
        try:
            url = 'https://tv.kt.com/tv/channel/pSchedule.asp'
            current_dt = datetime.now()
            epg_data = []
            for day in range(5):
                param_dt = current_dt + timedelta(days=day) 
                post_data = {'ch_type': '3', 'view_type':'1', 'service_ch_no':channel.kt_id, 'seldate': param_dt.strftime('%Y%m%d')}

                html = requests.post(url, headers=default_headers, data=post_data).text
                root = lxml.html.fromstring(html)
                tags = root.xpath('//ul/li[1]/div/div[2]/div/table/tbody/tr')
               
                for tag in tags:
                    tds = tag.xpath('td')
                    hour = tds[0].text_content().strip()
                    lines = []
                    for minute in tds[1].xpath('p'):
                        lines.append({'start_time':f"{post_data['seldate']} {hour}:{minute.text.strip()}"})

                    for idx, title_tag in enumerate(tds[2].xpath('p')):
                        lines[idx]['title'] = title_tag.text_content().replace('방송중', '').strip()
                        age_tag = title_tag.xpath('b/img')[0]
                        lines[idx]['age'] = age_tag.attrib['alt']

                    for idx, genre_tag in enumerate(tds[3].xpath('p')):
                        lines[idx]['genre'] = genre_tag.text.strip()
                    epg_data += lines

            for idx, item in enumerate(epg_data):
                p = ModelEpg2Program()
                p.channel = channel
                p.start_time = datetime.strptime(item['start_time'], '%Y%m%d %H:%M')
                if idx == len(epg_data)-1:
                    p.end_time = datetime.strptime(p.start_time.strftime('%Y%m%d') + ' 23:59', '%Y%m%d %H:%M')
                else:
                    p.end_time = datetime.strptime(epg_data[idx+1]['start_time'], '%Y%m%d %H:%M')
                
                p.title = item['title']
                        
                p.rate = '모든 연령 시청가' if item['age'] == '전체 시청 가능' else item['age'].replace('가능', '시청가')
                p.genre = item['genre']
                if item['genre'] == '영화':
                    p.is_movie = True
                db.session.add(p)
            logger.warning(f"LGU {channel.name} {len(epg_data)}개 추가")
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False

