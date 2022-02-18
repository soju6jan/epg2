import os, sys, traceback, requests
from datetime import datetime, timedelta
from .plugin import P, logger, db, d
from .model import ModelEpg2Program
from support.base.util import default_headers


class Epg2Hcn(object):
    @classmethod
    def make_epg(cls, channel):
        try:

            url = 'https://www.hcn.co.kr/user/channel/ND_getChInfoList.do'
            current_dt = datetime.now()

            epg_data = []
            for day in range(6):
                param_dt = current_dt + timedelta(days=day) 
                post_data = {
                    'chId': channel.hcn_id,
                    'onairdate': param_dt.strftime('%Y-%m-%d')
                } 
                data = requests.post(url, headers=default_headers, data=post_data).json()
                epg_data += data['ChannelInfoList']
            
            for idx, item in enumerate(epg_data):
                p = ModelEpg2Program()
                p.channel = channel
                p.start_time = datetime.strptime(f"{item['onairdate']} {item['starttime']}", '%Y-%m-%d %H:%M')
                if idx == len(epg_data)-1:
                    p.end_time = datetime.strptime(f"{item['onairdate']} 23:59", '%Y-%m-%d %H:%M')
                else:
                    p.end_time = datetime.strptime(f"{epg_data[idx+1]['onairdate']} {epg_data[idx+1]['starttime']}", '%Y-%m-%d %H:%M')

                p.title = item['title']
                if item['rating'] == '0':
                    p.rate = '모든 연령 시청가'
                else:
                    p.rate = f"{item['rating']}세 이상 시청가"
                p.genre = item['genre1']+ '|' + item['genre2']
                if 'description1' in item and 'description2' in item:
                    p.desc = item['description1'] + '\n' + item['description2'] 
                elif 'description1' in item:
                    p.desc = item['description1']
                if 'actor' in item:
                    p.actor = item['actor'].replace(',', '|')
                if 'director' in item:
                    p.director = item['director'].replace(',', '|')
                if 'liveRebroad' in item and item['liveRebroad'] == '재방송':
                    p.re = True
                if item['genre1'] == '영화' or item['genre2'] == '영화':
                    p.is_movie = True
                db.session.add(p)
            logger.warning(f"HCN {channel.name} {len(epg_data)}개 추가")
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False

