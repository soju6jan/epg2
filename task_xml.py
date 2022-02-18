import os, sys, traceback, re, json, threading, time, shutil, platform
from datetime import datetime, timedelta

from support.base import get_logger, d
from .plugin import P, logger, package_name, ModelSetting, celery, db, SystemModelSetting, path_data
from .model import ModelEpg2Channel, ModelEpg2Program, ModelEpg2Content    
from lxml import etree as ET

class Task(object):

    @staticmethod 
    def get_output_filepath(plugin):
        if plugin == 'all':
            filename = os.path.join(os.path.dirname(__file__), 'file', f'xmltv_{plugin}2.xml')
        else:
            filename = os.path.join(path_data, 'output', f'xmltv_{plugin}2.xml')
        return filename

    @staticmethod
    @celery.task
    def start(*args, **kargs):
        need_make = 0
        plugin = args[0]
        mode = args[1]
        if mode == 'manual':
            need_make = 1
        output_filepath = Task.get_output_filepath(plugin)
        if need_make == False and os.path.exists(output_filepath) == False:
            need_make = 2

        if need_make == False:
            time_str = ModelSetting.get(f"user_updated_{plugin}")
            if time_str == '':
                need_make = 3
            else:
                update_dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                epg_dt = datetime.strptime(P.ModelSettingDATA.get('updated_time'), '%Y-%m-%d %H:%M:%S')
                if update_dt < epg_dt:
                    need_make = 4

        logger.info(f"EPG 생성 : {plugin} {mode} {need_make}")
        if need_make == 0:
            return

        
        if plugin == 'klive':
            try:
                import klive
                Task.make_xml('klive')
            except Exception as e: 
                logger.error('klive not installed')
        elif plugin == 'hdhomerun':
            try:
                import hdhomerun
                Task.make_xml('hdhomerun')
            except Exception as e: 
                logger.error('hdhomerun not installed')
        elif plugin == 'tvheadend':
            try:
                import tvheadend
                Task.make_xml('tvheadend')
            except Exception as e: 
                logger.error('tvheadend not installed')
        logger.debug(f'EPG {plugin} epg make start..')

    @staticmethod
    def make_xml(call_from):
        logger.warning(f"make_xml_task : {call_from}")
        if call_from == 'tvheadend':
            try:
                import tvheadend
                tvh_list = tvheadend.LogicNormal.channel_list()
                if tvh_list is None:
                    return 'not setting tvheadend'
                for tvh_ch in tvh_list['lineup']:
                    epg_entity = ModelEpg2Channel.get_by_prefer(tvh_ch['GuideName'])
                    tvh_ch['channel_instance'] = epg_entity
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())

            try:
                generated_on = str(datetime.now())
                root = ET.Element('tv')
                root.set('generator-info-name', SystemModelSetting.get('ddns'))
                for tvh in tvh_list['lineup']:
                    channel_tag = ET.SubElement(root, 'channel') 
                    channel_tag.set('id', '%s' % tvh['uuid'])
                    icon_tag = ET.SubElement(channel_tag, 'icon')
                    icon_tag.set('src', tvh['channel_instance'].icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = tvh['GuideName']
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = str(tvh['GuideNumber'])

                for tvh in tvh_list['lineup']:
                    if tvh_ch['channel_instance'] == None:
                        logger.debug('no channel_instance :%s', tvh)
                        continue
                    Task.make_channel(root, tvh['channel_instance'], tvh['uuid'])
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
                return traceback.format_exc()

        elif call_from == 'klive':
            try:
                import klive
                query = db.session.query(klive.ModelCustom)
                query = query.order_by(klive.ModelCustom.number)
                query = query.order_by(klive.ModelCustom.epg_id)
                klive_channel_list = query.all()
                root = ET.Element('tv')
                root.set('generator-info-name', SystemModelSetting.get('ddns'))
                
                for klive_channel in klive_channel_list:
                    epg_entity = ModelEpg2Channel.get_by_name(klive_channel.epg_name)
                    if epg_entity is None:
                        # 2020-06-14
                        epg_entity = ModelEpg2Channel.get_by_prefer(klive_channel.title)
                        #tmp = ModelEpgMakerChannel.get_match_name(klive_channel.epg_name)
                        #if tmp is not None :
                        #    epg_entity = ModelEpgMakerChannel.get_instance_by_name(tmp[0])
                    #if epg_entity is None:
                    #    logger.debug('no channel_instance :%s', klive_channel.title)
                    #    #continue
                    #    # 2020-06-08
                    #    # Plex dvr같은 경우 내용은 없어도 채널태그는 있어야함.
                    channel_tag = ET.SubElement(root, 'channel') 
                    channel_tag.set('id', '%s|%s' % (klive_channel.source, klive_channel.source_id))
                    if epg_entity is not None:
                        icon_tag = ET.SubElement(channel_tag, 'icon')
                        icon_tag.set('src', epg_entity.icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = klive_channel.title
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = str(klive_channel.number)
                    display_name_tag = ET.SubElement(channel_tag, 'display-number') 
                    display_name_tag.text = str(klive_channel.number)

                for klive_channel in klive_channel_list:
                    epg_entity = ModelEpg2Channel.get_by_name(klive_channel.epg_name)
                    if epg_entity is None:
                        epg_entity = ModelEpg2Channel.get_by_prefer(klive_channel.title)
                    if epg_entity is None:
                        logger.debug('no channel_instance :%s', klive_channel.title)
                        continue
                                     
                    Task.make_channel(root, epg_entity, '%s|%s' % (klive_channel.source, klive_channel.source_id), category=klive_channel.group)
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
                return traceback.format_exc()

        elif call_from == 'hdhomerun':
            try:
                import hdhomerun as hdhomerun
                channel_list = hdhomerun.LogicHDHomerun.channel_list(only_use=True)

                root = ET.Element('tv')
                root.set('generator-info-name', SystemModelSetting.get('ddns'))
                
                for channel in channel_list:
                    if channel.match_epg_name == '':
                        continue
                    epg_entity = ModelEpg2Channel.get_by_name(channel.match_epg_name)
                    channel_tag = ET.SubElement(root, 'channel') 
                    channel_tag.set('id', '%s' % channel.id)
                    
                    if epg_entity is not None:
                        icon_tag = ET.SubElement(channel_tag, 'icon')
                        icon_tag.set('src', epg_entity.icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = channel.scan_name
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = str(channel.ch_number)
                    display_name_tag = ET.SubElement(channel_tag, 'display-number') 
                    display_name_tag.text = str(channel.ch_number)

                for channel in channel_list:
                    epg_entity = ModelEpg2Channel.get_by_name(channel.match_epg_name)
                    if epg_entity is None:
                        epg_entity = ModelEpg2Channel.get_by_prefer(channel.scan_name)
                    if epg_entity is None:
                        continue
                    Task.make_channel(root, epg_entity, '%s' % channel.id)
                   
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
                return traceback.format_exc()
        
        elif call_from == 'all':
            try:
                channel_list = ModelEpg2Channel.get_list()
                root = ET.Element('tv')
                root.set('generator-info-name', SystemModelSetting.get('ddns'))
                for idx, channel in enumerate(channel_list):
                    if channel.category == '지상파' and channel.name not in ['KBS1', 'KBS2', 'MBC', 'SBS', 'EBS1', 'EBS2', 'OBS 경인TV']:
                        continue

                    channel_tag = ET.SubElement(root, 'channel') 
                    channel_tag.set('id', channel.name)
                    icon_tag = ET.SubElement(channel_tag, 'icon')
                    icon_tag.set('src', channel.icon)
                    display_name_tag = ET.SubElement(channel_tag, 'display-name') 
                    display_name_tag.text = channel.name
                    display_name_tag = ET.SubElement(channel_tag, 'display-number') 
                    display_name_tag.text = str(idx+1)
                for channel in channel_list:
                    Task.make_channel(root, channel, channel.name)
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
                return traceback.format_exc()
       
        try:
            tree = ET.ElementTree(root)
            if call_from == 'all':
                filename = os.path.join(os.path.dirname(__file__), 'file', f'xmltv_{call_from}2.xml')
            else:
                filename = os.path.join(path_data, 'output', f'xmltv_{call_from}2.xml')
            if os.path.exists(filename):
                os.remove(filename)
            tree.write(filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
            #ret = ET.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8")

            ModelSetting.set('base_updated_%s' % call_from, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            #db.session.commit()
            logger.debug('EPG2XML end....')
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

   
    @staticmethod
    def make_channel(root, channel_instance, channel_id, category=None):
        try:
            logger.debug('CH : %s', channel_instance.name)
            for program in channel_instance.programs:
                program_tag = ET.SubElement(root, 'programme')
                program_tag.set('start', program.start_time.strftime('%Y%m%d%H%M%S') + ' +0900')
                program_tag.set('stop', program.end_time.strftime('%Y%m%d%H%M%S') + ' +0900')
                program_tag.set('channel', '%s' % channel_id)
                title_tag = ET.SubElement(program_tag, 'title')
                title_tag.set('lang', 'ko')
                if program.re is not None and program.re:
                    title_tag.text = program.title + ' (재)'
                else:
                    title_tag.text = program.title

                if program.rate != None:
                    rating_tag = ET.SubElement(program_tag, 'rating')
                    rating_tag.set('system', 'MPAA')
                    value_tag = ET.SubElement(rating_tag, 'value')
                    value_tag.text = program.rate
                # desc
                if program.desc is not None:
                    desc_tag = ET.SubElement(program_tag, 'desc')
                    desc_tag.set('lang', 'ko')
                    desc_tag.text = program.desc
                elif program.content_info is not None and program.content_info.desc is not None:
                    desc_tag = ET.SubElement(program_tag, 'desc')
                    desc_tag.set('lang', 'ko')
                    desc_tag.text = program.content_info.desc
                # poster
                if program.poster is not None:
                    icon_tag = ET.SubElement(program_tag, 'icon')
                    icon_tag.set('src', program.poster)
                elif program.content_info is not None and program.content_info.poster is not None:
                    icon_tag = ET.SubElement(program_tag, 'icon')
                    icon_tag.set('src', program.content_info.poster)
                # actor
                if program.actor is not None:
                    credits_tag = ET.SubElement(program_tag, 'credits')
                    for actor in program.actor.split('|'):
                        try:
                            actor_tag = ET.SubElement(credits_tag, 'actor')
                            #logger.debug(actor)
                            #name, role = actor.split(',')
                            #actor_tag.set('role', role.strip())
                            actor_tag.text = actor.strip()
                        except:
                            pass
                elif program.content_info is not None and program.content_info.actor is not None:
                    credits_tag = ET.SubElement(program_tag, 'credits')
                    for actor in program.content_info.actor.split('|'):
                        try:
                            actor_tag = ET.SubElement(credits_tag, 'actor')
                            #logger.debug(actor)
                            #name, role = actor.split(',')
                            #actor_tag.set('role', role.strip())
                            actor_tag.text = actor.strip()
                        except:
                            pass

                category_tag = ET.SubElement(program_tag, 'category')
                category_tag.set('lang', 'ko')
                category_tag.text = category if category is not None else channel_instance.category
                # TODO 영화부터 분기, 영화가 아니라면 모두 에피소드 처리해야함
                if program.is_movie == False:
                    if program.episode_number is not None:
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'onscreen')
                        episode_num_tag.text = program.episode_number
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'xmltv_ns')
                        episode_num_tag.text = '0.%s.' % (int(program.episode_number.split('-')[0]) - 1)
                    else:
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'onscreen')
                        tmp = program.start_time.strftime('%Y%m%d')
                        episode_num_tag.text = tmp
                        episode_num_tag = ET.SubElement(program_tag, 'episode-num')
                        episode_num_tag.set('system', 'xmltv_ns')
                        episode_num_tag.text = '%s.%s.' % (int(tmp[:4])-1, int(tmp[4:]) - 1)
                
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
