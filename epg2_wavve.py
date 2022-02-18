import os, sys, traceback, requests
from datetime import datetime, timedelta
from .plugin import P, logger, db, d
from .model import ModelEpg2Program
import framework.wavve.api as Wavve

class Epg2Wavve(object):
    @classmethod
    def make_epg(cls, channel):
        try:
            logger.debug(channel)
        
            current_dt = datetime.now()
            start_param = current_dt.strftime('%Y-%m-%d') + ' 00:00'
            end_dt = current_dt + timedelta(days=6)
            end_param = end_dt.strftime('%Y-%m-%d') + ' 24:00'
            data = Wavve.live_epgs_channels(channel.wavve_id, start_param, end_param)

            for item in data['list']:
                p = ModelEpg2Program()
                p.channel = channel
                p.start_time = datetime.strptime(item['starttime'], '%Y-%m-%d %H:%M')
                p.end_time = datetime.strptime(item['endtime'], '%Y-%m-%d %H:%M')
                p.title = item['title']
                p.episode_number = None
                p.part_number = None
                p.rate = None
                p.re = None
                p.is_movie = False
                #p.poster = 'https://' + item['channelimage']
                db.session.add(p)
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False

"""
{
    "cpid": "C4",
    "channelid": "E07",
    "channelname": "EBS 2",
    "channelimage": "img.pooq.co.kr/BMS/Channelimage30/image/E07.jpg",
    "scheduleid": "E07_20220215234000",
    "programid": "",
    "title": "가만히 10분 멍TV [손칼국수]",
    "image": "wchimg.wavve.com/live/thumbnail/E07.jpg",
    "starttime": "2022-02-15 23:40",
    "endtime": "2022-02-15 23:50",
    "timemachine": "Y",
    "license": "y",
    "livemarks": [],
    "targetage": "0",
    "tvimage": "img.pooq.co.kr/BMS/ChannelImg/ebs2.png",
    "ispreorder": "n",
    "preorderlink": "n",
    "alarm": "n"
}
"""
