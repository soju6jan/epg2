import os, sys, traceback, json, urllib.parse, requests, argparse, yaml, platform, time, re
if __name__ == '__main__':
    if platform.system() == 'Windows':
        sys.path += ["C:\SJVA3\lib2", "C:\SJVA3\data\custom", "C:\SJVA3_DEV"]
    else:
        sys.path += ["/root/SJVA3/lib2", "/root/SJVA3/data/custom"]

from support.base import get_logger, d, default_headers, SupportFile, SupportString, SupportDiscord
from support.base.util import default_headers
from support.tool import GoogleSheetBase

logger = get_logger()
from urllib.parse import urlencode, unquote, quote
from datetime import datetime

class CliMakeSheet:

    def __init__(self):
        self.sheet = EPG_Sheet()

    def daum(self):
        # 카테고리는 수동으로 넣는 걸로 하고 여기서는 채널만 삽입
        # 전체채널이 없는 종편 4개는 수동
        #keywords = ['지상파 편성표', '해외위성 편성표']
        compare_sheet_data = self.sheet.get_sheet_data()
        #logger.debug(sheet_data)
        keywords = ['지상파 편성표', '케이블 편성표', '케이블 편성표', 'SKYLIFE 편성표', '해외위성 편성표', '라디오 편성표']
        #keywords = ['지상파 편성표']#, '케이블 편성표', '케이블 편성표', 'SKYLIFE 편성표', '해외위성 편성표', '라디오 편성표']
        for keyword in keywords:
            sheet_data = self.sheet.get_sheet_data()
            url = f"https://search.daum.net/search?DA=B3T&w=tot&rtmaxcoll=B3T&q={keyword}"
            text = requests.get(url, headers=default_headers).text
            match = re.finditer(r'<li><a href="\??DA=B3T&w=tot&rtmaxcoll=B3T&q=(?P<search>[^"]+)" onclick="[^"]+" class="[^"]+">(?P<name>.*?)<\/a>', text)
            for m in match:
                name = m.group('name')
                daumid = unquote(m.group('search'))
                if keyword == 'SKYLIFE 편성표' and name.startswith('HD'):
                    name = name.replace('HD', '').strip()
                    find = False
                    for sheet_item in sheet_data:
                        if name in sheet_item['DAUM 이름'].split('\n'):
                            logger.warning(name)
                            find = True
                            break
                    if find:
                        continue

                logger.debug(m.group('name'))
                target = None
                for sheet_item in sheet_data:
                    if name in sheet_item['DAUM 이름'].split('\n'):
                        target = sheet_item
                        break
                if target == None:
                    target = {'이름':name, 'DAUM ID':daumid, 'DAUM 이름':name}
                    self.sheet.write_data(compare_sheet_data, target)
                
                

            #tmps = text.split('<li><a href="?DA=')
            #logger.debug(tmps[0][:100])
            #logger.debug(len(tmps))
        #logger.debug(d(data))

    def wavve(self):
        def live_all_channels(genre='all'):
            try:
                param = {
                    'apikey' : 'E5F3E0D30947AA5440556471321BB6D9',
                    'credential' : 'none',
                    'device' : 'pc',
                    'partner' : 'pooq',
                    'pooqzone' : 'none',
                    'region' : 'kor',
                    'drm' : 'wm',
                    'targetage' : 'auto',
                    'genre' : genre,
                    'type' : 'all',
                    'offset' : 0,
                    'limit' : 999,
                }
                url = f"https://apis.wavve.com/live/all-channels?{urlencode(param)}"
                response = requests.get(url, headers=default_headers)
                data = response.json()
                if response.status_code == 200:
                    return data
                else:
                    if 'resultcode' in data:
                        logger.debug(data['resultmessage'])
            except Exception as exception:
                logger.error('Exception:%s', exception)
                logger.error(traceback.format_exc()) 

        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        live_data = live_all_channels()

        ch_list = []
        for item in live_data['list']:
            img = 'https://' + item['tvimage'].replace(' ', '%20') if item['tvimage'] != '' else ''
            ch_list.append({'name':item['channelname'], 'id':item['channelid'], 'img':img})
        
        logger.warning(f"웨이브 채널 : {len(ch_list)}")
        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        logger.debug(date)
        url = f"https://apis.wavve.com/live/epgs?enddatetime={date}%2022%3A00&genre=all&limit=200&offset=0&startdatetime={date}%2019%3A00&apikey=E5F3E0D30947AA5440556471321BB6D9&credential=aiqk%2FPx6%2BLfWxuBH87cit5tcwp0q7JgdnzOEderjAOwwE4eDqp1fyzQneksz3IIo0RzrnMD4cATNlVVKPn4aZ9lDj54SE87ue%2B5%2BUK44pRCt2KwmzrGWSbNGex%2FOJg5MDm7gVP7OCCvdbtj84dPbThj2A%2FjRjXuRQdm1wuixUzZAJUYrF3R5ZGm%2BSpOTL9s6FPek8%2FeFnIkAe31L1OVj0mCiuWaRNNJI7JF2xV8M7eQXzrYcWUwUDnF1i351GfNKf2mWJ74s7y%2FVMu2wA9hDeJYscxF%2BHC0%2B28dVdRyC5L8%3D&device=pc&drm=wm&partner=pooq&pooqzone=none&region=kor&targetage=all"
        epg_data = requests.get(url, headers=default_headers).json()
        #logger.debug(epg_data)

        for item in epg_data['list']:
            for ch in ch_list:
                if ch['name'] == item['channelname'] and ch['id'] == item['channelid']:
                    logger.debug(ch['name'])
                    ch['img2'] = 'https://' + item['channelimage']
                    break
            else:
                logger.warning("없음")
                logger.warning(item['channelname'])

        for ch in ch_list:
            if 'img2' not in ch:
                logger.error(ch['name'])
                ch['img2'] = ch['img']
             
            data = self.find_in_sheet(sheet_data, ch['name'])
            if data == None:
                data = {}
                data['이름'] = ch['name']
                data['FROM'] = '웨이브'
            if data['로고'] == '':
                data['로고'] = ch['img2']
            data['웨이브 ID'] = ch['id']
            data['웨이브 이름'] = ch['name']
            data['웨이브 로고1'] = ch['img']
            if data['웨이브 로고2'] == '':
                data['웨이브 로고2'] = ch['img2']
            self.sheet.write_data(compare_sheet_data, data)

        #logger.warning(len(live_data['list']))    

    def tving(self):
        from support.site.tving import SupportTving
        data = SupportTving().get_live_list(include_drm=True)
        
        #logger.debug(d(data))
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for item in data:
            data = self.find_in_sheet(sheet_data, item['title'])
            if data == None:
                data = {}
                data['이름'] = item['title']
                data['FROM'] = '티빙'
            if '로고' not in data or data['로고'] == '':
                data['로고'] = item['img']
            data['티빙 ID'] = item['id']
            data['티빙 이름'] = item['title']
            data['티빙 로고'] = item['img']
            self.sheet.write_data(compare_sheet_data, data)


    def seezn(self):
        def get_channel_list():

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
            header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                'Host': 'api.seezntv.com',
                'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                'sec-ch-ua-mobile': '?0',
                'HTTP_CLIENT_IP': 'undefined',
                'X-APP-VERSION': '92.0.4515.131',
                'X-OS-VERSION': 'NT 10.0',
                'X-OS-TYPE': 'Windows',
                'X-DEVICE-MODEL': 'Chrome',
                'Accept': 'application/json',
                'Access-Control-Allow-Headers': 'Authentication',
                'Origin': 'https://www.seezntv.com',
                'Sec-Fetch-Site': 'same-site',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': 'https://www.seezntv.com/'
            }
            header['timestamp'] = timestamp
            header['transactionid'] = timestamp+'000000000000001'
            # logger.debug(header)
            ret = []
            data = requests.get('https://api.seezntv.com/svc/menu/app6/api/epg_chlist?category_id=1', headers=header).json()
            return data['data']['list'][0]['list_channel']
        
        #logger.debug(d(data))
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for item in get_channel_list():
            #logger.debug(d(item))
            #return
            data = self.find_in_sheet(sheet_data, item['service_ch_name'])
            if data == None:
                data = {}
                data['이름'] = item['service_ch_name']
                data['FROM'] = '시즌'
            if '로고' not in data or data['로고'] == '':
                data['로고'] = item['ch_image_detail']
            data['시즌 ID'] = item['ch_no']
            data['시즌 이름'] = item['service_ch_name']
            data['시즌 로고'] = item['ch_image_detail']
            self.sheet.write_data(compare_sheet_data, data)

    

    def skb(self):
        def get_skb_list():
            cate_list = [5100, 7800, 6600, 5600, 5800, 6300, 6700, 7200, 6000, 6400, 5900, 5300, 5700, 7400, 7600, 6900, 7300, 7700, 6501]
            #
            ret = []
            for cate in cate_list:
                url = 'http://m.skbroadband.com/content/realtime/Channel_List.do?key_depth1=%s&key_depth2=&key_depth3=' % cate
                logger.debug(url)
                #res = requests.post(url, data=data)
                res = requests.get(url)
                html = res.text
                tmp = re.compile(r'\<option\svalue=\"(?P<id>\d+)\".*?\>(?P<name>.*?)\<').finditer(html)
                for t in tmp:
                    ret.append([t.group('name').replace('&amp;', '&'), t.group('id')])

            return ret

        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for item in get_skb_list():
            logger.debug(item)
            data = self.find_in_sheet(sheet_data, item[0])
            if data == None:
                data = {}
                data['이름'] = item[0]
                data['FROM'] = 'SKB'
            data['SKB ID'] = item[1]
            data['SKB 이름'] = item[0]
            self.sheet.write_data(compare_sheet_data, data)

    def kt(self):
        def py_unicode(v):
            return str(v)
        def get_kt_list():
            ret = []
            url = 'https://tv.kt.com/tv/channel/pChInfo.asp'
            res = requests.get(url, headers=default_headers)
            res.encoding = res.apparent_encoding
            html = res.text
            tmp = re.compile(r'^\s+(?P<id>\d+)\&nbsp\;(?P<name>.*?)($|\&nbsp;\<)', re.MULTILINE).finditer(html)
            for t in tmp:
                ret.append([t.group('name').strip().replace('&amp;', '&') , t.group('id')])
            return ret

        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for item in get_kt_list():
            data = self.find_in_sheet(sheet_data, item[0])
            if data == None:
                data = {}
                data['이름'] = item[0]
                data['FROM'] = 'KT'
            data['KT ID'] = item[1]
            data['KT 이름'] = item[0]
            self.sheet.write_data(compare_sheet_data, data)

    def kt_logo(self):
        url = 'https://tv.kt.com/tv/channel/pSchedule.asp'
        data = {'ch_type': '3', 'view_type': '1'}
        #service_ch_no: 155
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()

        for item in sheet_data:
            if item['KT ID'] == '':
                continue
            if item['KT 로고'] != '':
                continue
            data['service_ch_no'] = item['KT ID']
            res = requests.post(url, headers=default_headers, data=data)
            text = res.text
            #logger.debug(res.text)
            match = re.search(r'<h5 class="b_logo"><img src=\'(?P<logo>[^\']+)\' alt=\'(?P<name>[^\']+)\'', text)
            if match and match.group('name').strip() == item['KT 이름']:
                item['KT 로고'] = 'https://tv.kt.com' + match.group('logo')
                item['로고'] = item['KT 로고']
                self.sheet.write_data(compare_sheet_data, item)
            else:
                logger.error(item['이름'])




    def lgu(self):
        def get_lgu_list():
            ret = []
            for i in range(10):
                url = 'https://www.uplus.co.kr/css/chgi/chgi/RetrieveTvChannel.hpi'
                #https://www.uplus.co.kr/css/chgi/chgi/RetrieveTvContentsMFamily.hpi
                #https://www.uplus.co.kr/css/chgi/chgi/RetrieveTvChannel.hpi

                data = {"code":"12810", 'category':'0%s' % i}
                logger.debug(data)
                res = requests.post(url, data=data, verify=False)
                html_data = res.text
                html = html_data

                tmp = re.compile(r'\<a\shref.*?\(\'(?P<id>\d+).*?\>(?P<name>.*?)\(').finditer(html)
                for t in tmp:
                    ret.append([t.group('name'), t.group('id')])
           
            #logger.debug(ret)
            return ret
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for item in get_lgu_list():
            data = self.find_in_sheet(sheet_data, item[0])
            if data == None:
                data = {}
                data['이름'] = item[0]
                data['FROM'] = 'LGU'
            data['LGU ID'] = item[1]
            data['LGU 이름'] = item[0]
            self.sheet.write_data(compare_sheet_data, data)


    def hcn(self):
        url = 'https://www.hcn.co.kr/user/channel/BD_ChannelInfoList.do'
        res = requests.get(url, headers=default_headers)
        res.encoding = res.apparent_encoding
        text = res.text
        match = re.finditer(r'<td onclick="goProgramInfo\(\d+,\'[^\']+\',\'[^\']+\',(?P<code>\d+)\);" style="cursor: pointer;">(?P<name>[^\']+)<span class="pgs_s1', text)
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for m in match:
            name = m.group('name').split('<')[0].strip()
            code = m.group('code').strip()
            data = self.find_in_sheet(sheet_data, name)
            if data == None:
                data = {}
                data['이름'] = name
                data['FROM'] = 'HCN'
            data['HCN ID'] = code
            data['HCN 이름'] = name
            self.sheet.write_data(compare_sheet_data, data)


    def cmb(self):
        url = 'http://cmb-shop.co.kr/cmb_channel.php'
        res = requests.get(url, headers=default_headers)
        res.encoding = res.apparent_encoding
        text = res.text
        match = re.finditer(r'class="chtxt02">(?P<ch>[^"]+)<\/td>', text)
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for m in match:
            name = m.group('ch').strip()
            data = self.find_in_sheet(sheet_data, name)
            if data == None:
                logger.warning(f"NOT FIND : {name}")
            else:
                if data['케이블 이름'] == '':
                    data['케이블 이름'] = name
                else:
                    tmp = data['케이블 이름'].split('\n')
                    if name not in tmp:
                        data['케이블 이름'] = data['케이블 이름'] + '\n' + name
                self.sheet.write_data(compare_sheet_data, data)


    def kctv(self):
        url = 'https://www.kctv.co.kr/channel/digital_channel.php'
        res = requests.get(url, headers=default_headers)
        res.encoding = res.apparent_encoding
        text = res.text
        match = re.finditer(r'class="txt_lf">(?P<ch>[^<]+)<\/td>', text)
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for m in match:
            name = m.group('ch').strip()
            data = self.find_in_sheet(sheet_data, name)
            if data == None:
                logger.warning(f"NOT FIND : {name}")
            else:
                if data['케이블 이름'] == '':
                    data['케이블 이름'] = name
                else:
                    tmp = data['케이블 이름'].split('\n')
                    if name not in tmp:
                        data['케이블 이름'] = data['케이블 이름'] + '\n' + name
                self.sheet.write_data(compare_sheet_data, data)


    def last_logo(self):
        sheet_data = self.sheet.get_sheet_data()
        compare_sheet_data = self.sheet.get_sheet_data()
        for item in sheet_data:
            if item['최종 로고'] != '' or item['카테고리'] in ['', '미사용'] or item['로고'] == '':
                continue
            # URL이 김
            # https://images-ext-1.discordapp.net/external/grWjdO6f-ted630snPcSGawPt45dvjxv_pJm-luBQLU/https/tv.kt.com/relatedmaterial/ch_logo/live/5.png
            #item['최종 로고'] = SupportDiscord.discord_proxy_image(item['로고'])
            tmp = requests.get(item['로고'], headers=default_headers).content
            item['최종 로고'] = SupportDiscord.discord_proxy_image_bytes(tmp)

            self.sheet.write_data(compare_sheet_data, item)
            #return
    


    def util_get_search_name(self, s):
        return s.strip().replace('-', '').replace(' ', '').upper()

    def find_in_sheet(self, sheet_data, name):
        for sheet_item in sheet_data:
            if self.util_get_search_name(sheet_item['이름']) == self.util_get_search_name(name):
                return sheet_item
            #logger.debug(sheet_item['이름'])
            if 'AKA' in sheet_item:
                akas = [self.util_get_search_name(x.strip()) for x in self.util_get_search_name(sheet_item['AKA']).splitlines()]
                if self.util_get_search_name(name) in akas:
                    return sheet_item

            #logger.debug(akas)
            

    def all(self):
        self.daum()
        self.wavve()
        self.tving()
        self.seezn()
        self.skb()
        self.kt()
        self.lgu()
        self.cmb()
        self.kctv()
        self.hcn()
        self.kt_logo()
        self.last_logo()
        logger.debug("종료")


    def log(self):
        data = [
            ['티빙', 0, 0],
            ['SPOTV', 0, 0],
            ['DAUM', 0, 0],
            ['웨이브', 0, 0],
            ['HCN', 0, 0],
            ['LGU', 0, 0],
            ['KT', 0, 0],
            ['SKB', 0, 0],
            ['시즌', 0, 0],
        ]
        count = 0
        sheet_data = self.sheet.get_sheet_data()
        for sheet_item in sheet_data:
            if sheet_item['카테고리'] in ['', '미사용']:
                continue
            #if sheet_item['웨이브 ID'] == '' and sheet_item['티빙 ID'] == '' and sheet_item['시즌 ID'] == '' and sheet_item['케이블 이름'] != '':
            #    continue

            count += 1
            for tmp in data:
                if sheet_item[f"{tmp[0]} ID"] != '':
                    tmp[1] += 1
            for tmp in data:
                if sheet_item[f"{tmp[0]} ID"] != '':
                    tmp[2] += 1
                    break
        
        for tmp in data:
            print(tmp)
            #logger.debug(d(data))

        count = 0
        for sheet_item in sheet_data:
            if sheet_item['카테고리'] == '미사용':
                continue
            if sheet_item['시즌 ID'] != '' and sheet_item['DAUM ID'] == '' and sheet_item['웨이브 ID'] == '' and sheet_item['티빙 ID'] == '' and sheet_item['SKB ID'] == '' and sheet_item['KT ID'] == '' and sheet_item['LGU ID'] == '' and sheet_item['HCN ID'] == '' and sheet_item['SPOTV ID'] == '':
                count += 1
        logger.debug(f"시즌 : {count}")

        count = 0
        for sheet_item in sheet_data:
            if sheet_item['카테고리'] == '미사용':
                continue
            if sheet_item['SKB ID'] != '' and sheet_item['DAUM ID'] == '' and sheet_item['웨이브 ID'] == '' and sheet_item['티빙 ID'] == '' and sheet_item['시즌 ID'] == '' and sheet_item['KT ID'] == '' and sheet_item['LGU ID'] == '' and sheet_item['HCN ID'] == '' and sheet_item['SPOTV ID'] == '':
                count += 1
        logger.debug(f"SKB : {count}")

        count = 0
        for sheet_item in sheet_data:
            if sheet_item['카테고리'] == '미사용':
                continue
            if sheet_item['KT ID'] != '' and sheet_item['DAUM ID'] == '' and sheet_item['웨이브 ID'] == '' and sheet_item['티빙 ID'] == '' and sheet_item['시즌 ID'] == '' and sheet_item['SKB ID'] == '' and sheet_item['LGU ID'] == '' and sheet_item['HCN ID'] == '' and sheet_item['SPOTV ID'] == '':
                count += 1
        logger.debug(f"KT : {count}")

        count = 0
        for sheet_item in sheet_data:
            if sheet_item['카테고리'] == '미사용':
                continue
            if sheet_item['LGU ID'] != '' and sheet_item['DAUM ID'] == '' and sheet_item['웨이브 ID'] == '' and sheet_item['티빙 ID'] == '' and sheet_item['시즌 ID'] == '' and sheet_item['KT ID'] == '' and sheet_item['SKB ID'] == '' and sheet_item['HCN ID'] == '' and sheet_item['SPOTV ID'] == '':
                logger.debug(sheet_item['이름'])
                count += 1
        logger.debug(f"LGU : {count}")





        logger.warning(count)



class EPG_Sheet(GoogleSheetBase):
    def __init__(self):
        super(EPG_Sheet, self).__init__('1bDjth4cWMNpLC62tRKsd3oaU3SqDDaMfuKwR8Lt31D4', os.path.join(os.path.dirname(__file__), 'file', 'cred'), 0, '이름')

if __name__ == '__main__':
    ins = CliMakeSheet()
    #ins.all()
    ins.log()
