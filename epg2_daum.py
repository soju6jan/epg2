import os, sys, traceback, requests, re, lxml.html, urllib.parse
from datetime import datetime
from .plugin import P, logger, db
from .model import ModelEpg2Program, ModelEpg2Content


class EntityDay(object):
    def __init__(self, int_year, str_month, str_day):
        self.dt = datetime(int_year, int(str_month), int(str_day))
        self.program_list = []

    def __repr__(self):
        return self.dt.strftime('%Y-%m-%d %H:%M:%S')

class EntityProgram(object):
    def __init__(self, entity_day, hour, dl):
        try:
            #self.dt = datetime(int_year, int(str_month), int(str_day))
            self.daum_title = None
            self.daum_id = None
            self.title = None
            self.episode_number = None
            self.rate = None
            self.re = None
            self.hd = None
            self.extra = []
            self.episode_number = None
            self.href = None
            self.part_number = None
            self.is_movie= None
            self.end_dt = None
            #self.daum_info = None

            minute = int(dl.xpath('dt')[0].text.strip())
            dd = dl.xpath('dd')[0]
            a_tag = dd.xpath('a')
            if a_tag:
                a_tag = a_tag[0]
                self.href = a_tag.attrib['href']
                self.title = a_tag.text.strip()
                match = re.compile(r'q\=(?P<daum_title>.*?)\&.*?\&irk\=(?P<daum_id>\d+)\&').search(self.href)
                if match:
                    self.is_movie = False
                    self.daum_id = 'KD' + match.group('daum_id')
                    self.daum_title = urllib.parse.unquote(match.group('daum_title'))
                match = re.compile(r'q\=(?P<daum_title>.*?)\&.*?\&scckey\=MV\|\|(?P<daum_id>\d+)').search(self.href)
                if match:
                    self.is_movie = True
                    self.daum_id = 'MD' + match.group('daum_id')
                    self.daum_title = urllib.parse.unquote(match.group('daum_title'))
                                
            span_tag = dd.xpath('span')
            
            for span in span_tag:
                if span.attrib['class'] == '':
                    self.title = span.text
                elif span.attrib['class'].find('ico_rate') != -1:
                    self.rate = int(span.attrib['class'].split('ico_rate')[1])
                elif span.attrib['class'].find('ico_re') != -1:
                    self.re = True
                #elif span.attrib['class'].find('ico_hd') != -1:
                #    self.hd = True
                else:
                    self.extra.append(span.text.strip())

            match = re.compile(r'^(?P<title>.*?)\s(?P<number>\d+)회$').search(self.title)
            if match:
                self.episode_number = match.group('number')
            match = re.compile(r'^(?P<title>.*?)\s\<(?P<number>\d+\-\d+)\>$').search(self.title)
            if match:
                self.episode_number = match.group('number')
            match = re.compile(r'^(?P<title>.*?)\s\<?(?P<number>\d+)부\>?$').search(self.title)
            if match:
                self.part_number = match.group('number')

            self.dt = datetime(entity_day.dt.year, entity_day.dt.month, entity_day.dt.day, hour, minute)
            entity_day.program_list.append(self)
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())

    

class Epg2Daum(object):
    @classmethod
    def make_epg(cls, channel):
        current_dt = datetime.now()
        try:
            #url = u'https://search.daum.net/search?DA=B3T&w=tot&rtmaxcoll=B3T&q=%s' % channel.daum_id
            url = u'https://search.daum.net/search?DA=B3T&w=tot&rtmaxcoll=B3T&q=%s' % urllib.parse.quote(channel.daum_id)
            from system.logic_site import SystemLogicSite
            res = SystemLogicSite.get_response_daum(url)
           
            root = lxml.html.fromstring(res.text)
            head = root.xpath("//div[contains(@class, 'tbl_head head_type2')]")[0]
            tmp = re.compile(r'(?P<month>\d{2})\.(?P<day>\d{2})\s[%s]' % u'월|화|수|목|금|토|일').finditer(head.text_content())
            day_list = []

            # 4일  현시간부터 오늘 자정까지 0.X일 + 3일
            for m in tmp:
                year = current_dt.year
                if int(m.group('month')) > current_dt.month:
                    if current_dt == 1:
                        year += -1
                elif int(m.group('month')) < current_dt.month:
                    if current_dt == 12:
                        year += 1
                day_list.append(EntityDay(year, m.group('month'), m.group('day')))
            root = root.xpath("//div[contains(@class, 'g_comp')]")
            area = None
            for t in root:
                if 'disp-attr' in t.attrib and t.attrib['disp-attr'] == 'B3T':
                    area = t
                    break
            if area is None:
                return
            
            time_tag = area.xpath('//*[@id="tvProgramListWrap"]/table/tbody/tr')
            
            #logger.debug(len(day_list))
            for time_tr in time_tag:
                hour = int(time_tr.xpath('th')[0].text.strip().replace(r'시', ''))
                #logger.debug('Hour : %s', hour)
                time_day_td = time_tr.xpath('td')
                #logger.debug('time_day_dl tag:%s', len(time_day_td))
                for index, td in enumerate(time_day_td): #시간별, 날짜별 한칸
                    dl_list = td.xpath('dl')
                    for dl in dl_list: # 한칸중 분별로 방송
                        EntityProgram(day_list[index], hour, dl)
            ret = []
            for t in day_list:
                for tt in t.program_list:
                    if len(ret) != 0:
                        ret[-1].end_dt = tt.dt
                    if tt.daum_title is not None:
                        #get_daum_info_ret = self.get_daum_info(tt.daum_title, tt.daum_id, tt.href, tt.is_movie)
                        code = ModelEpg2Content.append_by_daum(tt.daum_title, tt.daum_id, is_movie=tt.is_movie)
                        if code == None:
                            logger.debug('CCCCCCCCCCCCRRRRRRRRRRRTTTTTTTTTTTT!!!')
                            logger.debug('%s %s %s %s', tt.daum_title, tt.daum_id, tt.href, tt.is_movie)
                    ret.append(tt)
            ret[-1].end_dt = datetime(ret[-1].dt.year, ret[-1].dt.month, ret[-1].dt.day, 23, 59, 59)

            for tt in ret:
                p = ModelEpg2Program()
                p.channel = channel
                p.start_time = tt.dt
                p.end_time = tt.end_dt
                p.title = tt.title
                p.episode_number = tt.episode_number
                p.part_number = tt.part_number
                p.rate = tt.rate
                if p.rate == None:
                    p.rate = f'{p.rate}세 이상 시청가'
                else:
                    p.rate = f'모든 연령 시청가'
                p.re = tt.re
                p.content_id = tt.daum_id
                p.is_movie = tt.is_movie
                db.session.add(p)
            logger.debug(u'- %s개 저장', len(ret))
            return True
        except Exception as e: 
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            logger.debug(url)
            return False

