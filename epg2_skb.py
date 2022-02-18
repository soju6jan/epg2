import os, sys, traceback, requests, lxml.html, re
from datetime import datetime, timedelta
from .plugin import P, logger, db, d
from .model import ModelEpg2Program
from support.base.util import default_headers



class Epg2Skb(object):
    @classmethod
    def make_epg(cls, channel):
        try:
            url = f'https://skbroadband.com/content/realtime/Channel_List_Ajax.do?key_depth1=7800&key_depth2={channel.skb_id}'

            day_data = []
            html = requests.get(url, headers=default_headers).text
            #logger.debug(html)
            root = lxml.html.fromstring(html)
            today = root.xpath('//div/table/thead/tr/th[2]')[0].text.strip()
            current_dt = datetime.now()
            for day in range(7):
                param_dt = current_dt + timedelta(days=day) 
                day_data.append({
                    'date': param_dt.strftime('%Y-%m-%d'),
                    'epg_data':[]
                })
            tr_tags = root.xpath('//div/table/tbody/tr')
            for tr in tr_tags:
                hour = tr.xpath('th')[0].text.replace('시', '')
                for day_index, td in enumerate(tr.xpath('td')):
                    for dl in td.xpath('dl'):
                        minute = dl.xpath('dt')[0].text 
                        if minute != None:
                            entity = {
                                'start_time' : f"{hour}:{minute.replace('분','').strip()}"
                            }
                            entity['title'] = dl.xpath('dd[@class="title"]')[0].text
                            tmp = dl.xpath('dd[2]/span')
                            for t in tmp:
                                if 'flag8' in t.attrib['class']:
                                    entity['age'] = '12세 이상 시청가'
                                    break
                                elif 'flag9' in t.attrib['class']:
                                    entity['age'] = '15세 이상 시청가'
                                    break
                                elif 'flag10' in t.attrib['class']:
                                    entity['age'] = '19세 이상 시청가'
                                    break
                            day_data[day_index]['epg_data'].append(entity)
            epg_data = []
            for day in day_data:
                for item in day['epg_data']:
                    item['start_time'] = f"{day['date']} {item['start_time']}"
                    epg_data.append(item)
                
            for idx, item in enumerate(epg_data):
                p = ModelEpg2Program()
                p.channel = channel
                p.start_time = datetime.strptime(item['start_time'], '%Y-%m-%d %H:%M')
                if idx == len(epg_data)-1:
                    p.end_time = datetime.strptime(p.start_time.strftime('%Y-%m-%d') + ' 23:59', '%Y-%m-%d %H:%M')
                else:
                    p.end_time = datetime.strptime(epg_data[idx+1]['start_time'], '%Y-%m-%d %H:%M')
                match = re.match(r'(?P<title>.*?)\s\<(?P<part>\d+)부\>', item['title'])
                if match:
                    p.title = match.group('title').strip()
                    p.part_number = match.group('part')
                else:
                    tmp = item['title']
                    if '(재)' in item['title']:
                        p.re = True
                        tmp = tmp.replace('(재)', '').strip()
                    
                    match = re.match(r'(?P<title>.*?)\s\((?P<part>\d+)회\)', item['title'])
                    if match:
                        p.title = match.group('title').strip()
                        p.episode_number = match.group('part')
                    else:
                        p.title = item['title']
                if 'age' in item:
                    p.rate = item['age']
                db.session.add(p)
            logger.warning(f"SKB {channel.name} {len(epg_data)}개 추가")
            return True
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return False

