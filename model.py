import os, sys, traceback, re, json, threading, time, shutil, fnmatch, glob
from datetime import datetime, timedelta

from framework import db, app, path_data
from sqlalchemy import or_, and_, func, not_, desc
from plugin import ModelBase

# 패키지
from .plugin import P, logger, package_name, ModelSetting, EPG_DATA_DB_BIND_KEY

    
class ModelEpg2Channel(ModelBase):
    __tablename__ = f'{package_name}_channel'
    __bind_key__ = EPG_DATA_DB_BIND_KEY

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    #############################################
    name = db.Column(db.String)
    category = db.Column(db.String)
    aka = db.Column(db.String)
    epg_from = db.Column(db.String)
    icon = db.Column(db.String)

    daum_name = db.Column(db.String)
    daum_id = db.Column(db.String)
    wavve_name = db.Column(db.String)
    wavve_id = db.Column(db.String)
    tving_name = db.Column(db.String)
    tving_id = db.Column(db.String)
    seezn_name = db.Column(db.String)
    seezn_id = db.Column(db.String)
    skb_name = db.Column(db.String)
    skb_id = db.Column(db.String)
    kt_name = db.Column(db.String)
    kt_id = db.Column(db.String)
    lgu_name = db.Column(db.String)
    lgu_id = db.Column(db.String)
    hcn_name = db.Column(db.String)
    hcn_id = db.Column(db.String)
    spotv_id = db.Column(db.String)
    cable_name = db.Column(db.String)
    memo = db.Column(db.String)
    programs = db.relationship('ModelEpg2Program', backref='channel', lazy=True)

    def __init__(self):
        self.created_time = datetime.now()
    
    def update(self, sheet_item):
        self.name = sheet_item['이름']
        self.category = sheet_item['카테고리']
        self.aka = sheet_item['이름'] + '\n' + sheet_item['AKA']
        self.icon = sheet_item['최종 로고']

        self.daum_name = sheet_item['DAUM 이름']
        self.daum_id = sheet_item['DAUM ID']
        self.wavve_name = sheet_item['웨이브 이름']
        self.wavve_id = sheet_item['웨이브 ID']
        self.tving_name = sheet_item['티빙 이름']
        self.tving_id = sheet_item['티빙 ID']
        self.seezn_name = sheet_item['시즌 이름']
        self.seezn_id = sheet_item['시즌 ID']
        self.skb_name = sheet_item['SKB 이름']
        self.skb_id = sheet_item['SKB ID']
        self.kt_name = sheet_item['KT 이름']
        self.kt_id = sheet_item['KT ID']
        self.lgu_name = sheet_item['LGU 이름']
        self.lgu_id = sheet_item['LGU ID']
        self.hcn_name = sheet_item['HCN 이름']
        self.hcn_id = sheet_item['HCN ID']
        self.spotv_id = sheet_item['SPOTV ID']
        self.cable_name = sheet_item['케이블 이름']
        self.memo = sheet_item['메모']
        #self.json = sheet_item
        self.save()









    @classmethod
    def get_by_name(cls, name):
        return db.session.query(cls).filter_by(name=name).first()


    @classmethod
    def get_by_source_id(cls, source, source_id):
        if source == 'spotv':
            return db.session.query(cls).filter_by(spotv_id=str(source_id)).first()
        elif source == 'tving':
            return db.session.query(cls).filter_by(tving_id=str(source_id)).first()

    @classmethod
    def get_channel_list_by_source(cls, source):
        if source == 'tving':
            return db.session.query(cls).filter(cls.tving_id != '').all()
    
    @classmethod
    def util_get_search_name(cls, s):
        return s.lower().strip().replace('-', '').replace(' ', '').upper()

    @classmethod
    def get_by_prefer(cls, name):
        channel_list = cls.get_list()
        for ch in channel_list:
            aka = [cls.util_get_search_name(x) for x in ch.aka.split('\n')]
            if cls.util_get_search_name(name) in aka:
                return ch





    















    @staticmethod
    def get_instance_by_name(name):
        try:
            return db.session.query(ModelEpgMakerChannel).filter_by(name=name).first()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_channel_list():
        try:
            channel_list = db.session.query(ModelEpgMakerChannel).all()
            #ret = [x.as_dict() for x in channel_list]
            return channel_list
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    












# 실제 EPG 내용이다
# 아래 테이블은 EPG에서 daum_info 로 참조한다.
class ModelEpg2Program(ModelBase):
    __tablename__ = f'{package_name}_program'
    __bind_key__ = EPG_DATA_DB_BIND_KEY

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    #############################################

    channel_name = db.Column(db.Integer, db.ForeignKey(f'{package_name}_channel.name'))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    title = db.Column(db.String)
    episode_number = db.Column(db.String)
    part_number = db.Column(db.String)
    rate = db.Column(db.String)
    #tv_mpaa_map = {'CPTG0100' : u'모든 연령 시청가', 'CPTG0200' : u'7세 이상 시청가', 'CPTG0300' : u'12세 이상 시청가', 'CPTG0400' : u'15세 이상 시청가', 'CPTG0500' : u'19세 이상 시청가'}

    re = db.Column(db.Boolean)

    is_movie = db.Column(db.Boolean)
    content_id = db.Column(db.String, db.ForeignKey(f'{package_name}_content.content_id' ))
    content_info = db.relationship('ModelEpg2Content', backref='programs', lazy=True)

    
    # 다음과 티빙은 ModelEpg2Content 사용
    # 티빙 episode_plot 사용
    is_movie = db.Column(db.Boolean)
    poster = db.Column(db.String)
    desc = db.Column(db.String)
    genre = db.Column(db.String)
    actor = db.Column(db.String)
    director = db.Column(db.String)
    producer = db.Column(db.String)
    writer = db.Column(db.String)


    def __init__(self):
        self.created_time = datetime.now()
        self.is_movie = False
        self.re = False



    @classmethod
    def delete_by_channel_name(cls, channel_name):
        db.session.query(cls).filter(cls.channel_name == channel_name).delete()
        db.session.commit()






    @staticmethod
    def save(data):
        try:
            data = data['list']
            for d in data:
                c = ModelEpgMakerChannel(d)
                db.session.add(c)
            db.session.commit()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc()) 
















class ModelEpg2Content(ModelBase):
    __tablename__ = f'{package_name}_content'
    __bind_key__ = EPG_DATA_DB_BIND_KEY

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    json = db.Column(db.JSON)
    #############################################
    
    is_movie = db.Column(db.Boolean)
    content_title = db.Column(db.String)
    content_id = db.Column(db.String)

    poster = db.Column(db.String)
    desc = db.Column(db.String)
    genre = db.Column(db.String)

    actor = db.Column(db.String)
    director = db.Column(db.String)
    producer = db.Column(db.String)
    writer = db.Column(db.String)

    def __init__(self):
        self.created_time = datetime.now()




    @classmethod
    def person_to_line(cls, data, attr):
        if attr in data:
            persons = []
            for tmp in data[attr]:
                if tmp['name'] == '' or tmp['role'] in ['작가', '극본', '각본', '감독', '연출', '제작', '기획']:
                    continue
                persons.append(tmp['name'])
            return '|'.join(persons)

    @classmethod
    def append_by_daum(cls, title, code, is_movie=False):
        try:
            entity = db.session.query(cls).filter(cls.content_id == code).first()
            if entity is not None:
                #logger.debug(f"{title} exists..")
                return code

            from metadata import Logic as MetadataLogic
            m = ModelEpg2Content()
            
            m.content_id = code
            m.is_movie = is_movie
            if is_movie:
                data = MetadataLogic.get_module('movie').info(code)
                posters = sorted(data['art'], key=lambda k: k['score'], reverse=True) 
                m.actor = cls.person_to_line(data, 'actor')
                m.director = '|'.join(data['director'])
                m.writer = '|'.join(data['credits'])
                m.producer = '|'.join(data['producers'])
            else:
                data = MetadataLogic.get_module('ktv').info(code, title)
                posters = sorted(data['thumb'], key=lambda k: k['score'], reverse=True) 
                m.actor = cls.person_to_line(data, 'actor')
                m.director = cls.person_to_line(data, 'director')
                m.writer = cls.person_to_line(data, 'credits')
        
            for tmp in posters:
                if tmp['aspect'] == 'poster':
                    m.poster = tmp['value']
                    break
            m.content_title = data['title']
            m.desc = data['plot']
            m.genre = '|'.join(data['genre'])
            m.save()
            return code
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())



    @classmethod
    def append_by_tving(cls, data):
        try:
            entity = db.session.query(cls).filter(cls.content_id == data['code']).first()
            if entity is not None:
                return data['code']

            m = ModelEpg2Content()
            m.content_id = data['code']
            m.content_title = data['name']['ko']
            m.desc = data['synopsis']['ko']
            m.genre = data['category1_name']['ko']
            m.actor = '|'.join(data['actor'])
            m.director = '|'.join(data['director'])

            for idx, img in enumerate(data['image']):
                if img['code'] in ['CAIP0900', 'CAIP2300', 'CAIP2400']: #poster
                    m.poster = 'https://image.tving.com' + img['url']
                    break
            m.save()
            return data['code']
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())