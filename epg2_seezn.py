import os, sys, traceback, requests, urllib.parse
from datetime import datetime, timedelta
from .plugin import P, logger, db, d
from .model import ModelEpg2Program
from support.base.util import default_headers
#
class Epg2Seezn(object):
    @classmethod
    def make_epg(cls, channel):
        try:
            url = f'https://api.seezntv.com/svc/menu/app6/api/epg_proglist?ch_no={channel.seezn_id}'
            logger.debug(channel)

            data = requests.get(url, headers=default_headers).json()
            current_dt = datetime.now()
            today = current_dt.strftime('%Y%m%d')
            count = 0
            for item in data['data']['list']:
                if today != item['start_ymd']:
                    continue
                p = ModelEpg2Program()
                p.channel = channel
                p.start_time = datetime.strptime(item['start_ymd'] + ' ' + item['start_time'], '%Y%m%d %H:%M')

                p.end_time = datetime.strptime(item['start_ymd'] + ' ' + item['end_time'], '%Y%m%d %H:%M')
                if p.end_time < p.start_time:
                    p.end_time = p.end_time + timedelta(days=1)
                p.title = urllib.parse.unquote_plus(item['program_name'])
                if item['frequency'] != '':
                    p.episode_number = item['frequency']
                if item['rebroad'] == 'Y':
                    p.re = True
                if item['rating'] == '0':
                    p.rate = '모든 연령 시청가'
                else:
                    p.rate = f"{item['rating']}세 이상 시청가"
                db.session.add(p)
                count += 1
            logger.warning(f"seezn {channel.name} {count} 추가")
            return True
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return False

"""
{
    "rebroad": "",
    "onair_yn": "N",
    "program_subname": "",
    "program_name": "%EB%B3%B4%EC%95%88%EA%B4%80",
    "block_yn": "N",
    "ch_image_list": "http://img.megatvdnp.co.kr/uploads/images/imgurlmodifya5_image/20171226/OMSMNG_20171226173341785.png",
    "hd": "N",
    "frequency": "",
    "ch_image_detail": "http://img.megatvdnp.co.kr/uploads/images/imgurlmodifya5_image/20171226/OMSMNG_20171226173341785.png",
    "director": "김형주",
    "live_url": "http://menu.megatvdnp.co.kr:38086/app6/api/epg_play?ch_no=305",
    "start_ymd": "20220215",
    "free_yn": "Y",
    "service_ch_name": "PLAYY 힐링 영화",
    "cast": "이성민,조진웅,김성균",
    "ch_image_onair": "http://img.megatvdnp.co.kr/uploads/images/imgurlmodifya5_image/20171226/OMSMNG_20171226173341785.png",
    "end_time": "00:23",
    "start_time": "22:27",
    "pack_group_id": "MTVBA",
    "rating": "15",
    "program_id": "H08_00843527",
    "live": "N"
},
"""
