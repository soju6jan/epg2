import os, sys, traceback, re, json, threading, time, shutil, platform
from datetime import datetime, timedelta

from support.base import get_logger, d
from .plugin import P, logger, package_name, ModelSetting, celery, db
from .model import ModelEpg2Channel, ModelEpg2Program, ModelEpg2Content    

from .epg2_daum import Epg2Daum
from .epg2_wavve import Epg2Wavve
from .epg2_tving import Epg2Tving
from .epg2_spotv import Epg2Spotv
from .epg2_hcn import Epg2Hcn
from .epg2_lgu import Epg2Lgu
from .epg2_kt import Epg2Kt
from .epg2_skb import Epg2Skb
from .epg2_seezn import Epg2Seezn

#       API채널전체 API채널별  방송정보  연령  장르   회차  파트  재방송  
# lgu : X           X          X        O     O     O    O     O  
# skb : X           X          X        O     X     O    O     O  
# kt  : X           X          X        O     O     X    X     X

class Task(object):

    @staticmethod
    def is_need_epg_make(db_item):
        #if db_item.update_time + timedelta(days=1) > datetime.now():
        if db_item.update_time == None or db_item.update_time + timedelta(hours=12) < datetime.now():
            return True
        return False


    @staticmethod
    @celery.task
    def start(*args, **kargs):
        from .cli_make_sheet import EPG_Sheet
        sheet = EPG_Sheet()
        Task.make_channel_list(sheet)

        # spotv 
        db_item = ModelEpg2Channel.get_by_name('SPOTV')
        if Task.is_need_epg_make(db_item):
            logger.info("스포티비 EPG 생성")
            Epg2Spotv.make_epg()
        else:
            logger.debug('스포티비 1일 미만이라 패스 : %s', (datetime.now()-db_item.update_time))

        # tving 
        db_item = ModelEpg2Channel.get_by_name('tvN')
        if Task.is_need_epg_make(db_item):
            logger.info("티빙 EPG 생성")
            Epg2Tving.make_epg()
        else:
            logger.debug('티빙-tvN 1일 미만이라 패스 : %s', (datetime.now()-db_item.update_time))

        channel_list = ModelEpg2Channel.get_list()   

        epg_map = [
            {'name':'daum', 'ins' : Epg2Daum, 'count':0},
            {'name':'wavve', 'ins': Epg2Wavve, 'count':0},
            {"name" : 'hcn', 'ins' : Epg2Hcn, 'count':0}, 
            {"name" : 'lgu', 'ins' : Epg2Lgu, 'count':0}, 
            {"name" : 'skb', 'ins' : Epg2Skb, 'count':0}, 
            {"name" : 'kt', 'ins' : Epg2Kt, 'count':0}, 
            {"name" : 'seezn', 'ins' : Epg2Seezn, 'count':0}, 
        ]
        now = datetime.now()

        make_title = []
        make_count = 0
        for index, channel in enumerate(channel_list):
            try:
                logger.debug(f">>>> {index} / {len(channel_list)} : {channel.name} UPDATED TIME:[{channel.update_time}]")
                #if Task.is_need_epg_make(channel) == False and len(channel.programs) > 0 and channel.epg_from != 'seezn' and channel.name not in ['VIKI']:
                if Task.is_need_epg_make(channel) == False and len(channel.programs) > 0 and channel.epg_from != 'seezn':
                    #logger.debug(u'만든지 1일 미만이라 패스 : %s', (now-channel.update_time))
                    continue
                make_title.append(channel.name)
                ModelEpg2Program.delete_by_channel_name(channel.name)
                
                for epg_source in epg_map:
                    ret = getattr(channel, f"{epg_source['name']}_id")
                    if ret == '':
                        continue
                    if epg_source['ins'] == None:
                        continue
                    ret = epg_source['ins'].make_epg(channel)
                    if ret:
                        make_count += 1
                        channel.epg_from = epg_source['name']
                        epg_source['count'] += 1
                        channel.update_time = datetime.now()
                        break
            except Exception as e: 
                logger.error(f'Exception:{str(e)}')
                logger.error(traceback.format_exc())
                logger.debug('XX :%s', channel)
            finally:
                db.session.add(channel)
                db.session.commit()

        logger.debug(d(make_title))
        logger.debug(len(make_title))
        logger.info(make_count)
        if make_count > -1:
            P.ModelSettingDATA.set('updated_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            from .task_xml import Task as TaskXml
            TaskXml.make_xml('all')
            Task.upload()

    @staticmethod
    def make_channel_list(sheet):
        sheet_data = sheet.get_sheet_data()
        # 없어진 채널을 삭제한다.
        db_data = ModelEpg2Channel.get_list()
        for db_item in db_data:
            ret = Task.find_in_sheet(sheet_data, db_item.name)
            if ret == None:
                ModelEpg2Program.delete_by_channel_name(db_item.name)
                ModelEpg2Channel.delete_by_id(db_item.id)

        for sheet_item in sheet_data:
            if sheet_item['카테고리'] in ['', '미사용']:
                continue
            db_item = ModelEpg2Channel.get_by_name(sheet_item['이름'])    
            if db_item == None:
                db_item = ModelEpg2Channel()
            db_item.update(sheet_item)

    
    @staticmethod
    def find_in_sheet(sheet_data, name):
        for item in sheet_data:
            if item['이름'] == name and item['카테고리'] != '미사용':
                return item


    @staticmethod
    def upload():
        epg_sh = os.path.join(os.path.dirname(__file__), 'file', 'epg_upload.sh')
        os.system(f"chmod 777 {os.path.dirname(__file__)}")
        #os.system(f"{epg_sh} {os.path.dirname(__file__)}")
        command = [epg_sh, os.path.dirname(__file__)]
        logger.warning(command)
        from support.base import SupportProcess
        ret = SupportProcess.execute(command, timeout=60)
        logger.warning(ret)


 
if __name__ == '__main__':
    Task.start()
    