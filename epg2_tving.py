import os, sys, traceback, requests
from datetime import datetime, timedelta
from .plugin import P, logger, db, d
from .model import ModelEpg2Program, ModelEpg2Channel, ModelEpg2Content
from support.site.tving import SupportTving
from lib_metadata.site_tving import tv_mpaa_map

# 3시간씩 호출, 채널 동시호출, 일주일 편성표
# 포스터, Plot 정보 제공
class Epg2Tving(object):

    @classmethod
    def __get_split_ch_list(cls):

        tving_ch_list = ModelEpg2Channel.get_channel_list_by_source('tving')
        tving_ch_ids = [x.tving_id for x in tving_ch_list]
        ch_param_list = []
        count = 0
        while True:
            start_index = count * 20
            end_index = (count+1)*20
            if end_index > len(tving_ch_ids):
                end_index = len(tving_ch_ids)
            ch_param_list.append(tving_ch_ids[start_index:end_index])
            if end_index == len(tving_ch_ids):
                break
            count += 1
        
        logger.debug(ch_param_list)
        for ch in ch_param_list:
            logger.debug(len(ch))
        return ch_param_list

    @classmethod
    def __get_epg_data(cls):
        current_dt = datetime.now()
        start_dt = datetime(current_dt.year, current_dt.month, current_dt.day, int(current_dt.hour/3)*3, 0, 1)
        epg_data = {}
        ch_param_list = cls.__get_split_ch_list()
        for ch_param in ch_param_list:
            count = 0
            while count < 48:  # 하루 8 * 일 6 
                tmp = start_dt + timedelta(hours=(count*3))
                date_param = tmp.strftime('%Y%m%d')
                start_time = str(tmp.hour).zfill(2) + '0000'
                end_time = str((tmp + timedelta(hours=3)).hour).zfill(2) + '0000'
                data = SupportTving.ins.get_schedules(ch_param, date_param, start_time, end_time)
                
                for ch in data['result']:
                    if ch['schedules'] == None:
                        continue
                    if ch['channel_code'] not in epg_data:
                        epg_data[ch['channel_code']] = []
                    epg_data[ch['channel_code']] += ch['schedules']
                count += 1
        return epg_data

    @classmethod
    def make_epg(cls):
        try:
            epg_data = cls.__get_epg_data()
            for ch_id, ch_data in epg_data.items():
                db_item = ModelEpg2Channel.get_by_source_id('tving', ch_id) 
                if db_item == None:
                    logger.error(f"확인필요 채널 ID : {ch_id}")
                    continue
                ModelEpg2Program.delete_by_channel_name(db_item.name)

                logger.debug(f"{db_item.name} : {len(ch_data)}")
                current_dt = datetime.now()
                count = 0
                for schedule in ch_data:
                    #if schedule['movie'] != None:
                    #    logger.debug(d(schedule['episode']))
                    #continue
                    p = ModelEpg2Program()
                    p.channel = db_item
                    p.start_time = datetime.strptime(str(schedule['broadcast_start_time']), '%Y%m%d%H%M%S')
                    p.end_time = datetime.strptime(str(schedule['broadcast_end_time']), '%Y%m%d%H%M%S')
                    p.title = schedule['program']['name']['ko']
                    p.content_id = schedule['program']['code']
                    ModelEpg2Content.append_by_tving(schedule['program'])
                    if schedule['episode'] != None: 
                        p.episode_number = str(schedule['episode']['frequency'])
                        p.desc = schedule['episode']['synopsis']['ko']
                        p.rate = tv_mpaa_map[schedule['episode']['grade_code']]
                    content_id = schedule['episode']
                    db.session.add(p)
                    count += 1
                db_item.update_time = current_dt
                db_item.epg_from = 'tving'
                db.session.add(db_item)
                logger.warning(f"{db_item.name} {count}개 추가")
            db.session.commit()
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


        
        
"""
#https://api.tving.com/v2/media/schedules?pageNo=1&pageSize=20&order=chno&scope=all&adult=n&free=all&broadDate=20220216&broadcastDate=20220216&startBroadTime=120000&endBroadTime=150000&channelCode=C00772,C01582,C00708,C01581,C01583,C00593,C01723,C15846,C00544,C00588,C00805,C00590,C07381,C04601,C07382,C00551,C15741,C01143,C17142,C43341&screenCode=CSSD0100&networkCode=CSND0900&osCode=CSOD0900&teleCode=CSCD0900&apiKey=1e7952d0917d6aab1f0293a063697610
"""
