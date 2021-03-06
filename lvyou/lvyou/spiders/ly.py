# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request, FormRequest
from scrapy.selector import Selector
from utils.htmlutils import remove_tags
import json
import re

class LYSpider(scrapy.Spider):
    name = "ly_gonglue"

    custom_settings = {
        'DOWNLOAD_TIMEOUT' : 10,
        'DOWNLOAD_DELAY' : 0.3
    }

    gonglue_api = ('http://go.ly.com/ajax/GetNewRaiderInfo?type=2&desItemId=&desItemKind=&travelway=&pageSize=12&pageindex=%d&startTime=-1&endTime=&viewtype=1&iid=0.8534178737842524', 28)

    HEADERS = {
        'Host' : 'go.ly.com',
        'Accept' : '*/*',
        'Accept-Encoding' : 'gzip, deflate, sdch',
        'Accept-Language' : 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2,ja;q=0.2',
        'Referer' : 'http://go.ly.com/'
    }

    def start_requests(self):
        for page in range(self.gonglue_api[1]):
            yield Request(self.gonglue_api[0] % (page), headers=self.HEADERS, dont_filter=True, callback=self.parse_gonglue)

    def parse_gonglue(self, response):
        selector = Selector(response)
        for gonglue in selector.xpath('//ul[@class="youjiList clearfix"]/li'):
            title = gonglue.xpath('./a[@class="youjiNameTit"]/@title').extract_first()
            author = gonglue.xpath('./div[@class="youjiSource clearfix"]/a[@class="personName"]/@title').extract_first()
            view_count = gonglue.xpath('./div[@class="youjiSource clearfix"]/span[@class="lookNub"]/text()').extract_first()
            like_count = gonglue.xpath('./div[@class="youjiSource clearfix"]/span[@class="likeNub"]/text()').extract_first()
            url = gonglue.xpath('./a[@class="youjiPic"]/@href').extract_first()


            if not title or not author or not view_count:
                title = gonglue.xpath('.//a[@class="yj-name"]/text()').extract_first()
                #author = gonglue.xpath('.//a[class="autor-name"]/text()').extract_first()
                author = gonglue.xpath('.//div[@class="pinfo"]/a[1]/text()').extract_first()
                view_count = gonglue.xpath('.//p[@class="viewlike clearfix"]/span[1]/text()').extract_first()
                like_count = gonglue.xpath('.//p[@class="viewlike clearfix"]/span[2]/text()').extract_first()
                url = gonglue.xpath('.//a[@class="yj-name"]/@href').extract_first()
            result = {
                'title' : title,
                'author' : author,
                'view_count' : view_count,
                'like_count' : like_count,
                'url' : url,
            }
            #self.logger.info('lv gonglue : %s' % json.dumps(result, ensure_ascii=False).encode('utf-8'))
            meta = response.meta.copy()
            meta['result'] = result
            #yield Request(url, headers=self.HEADERS, meta=meta, dont_filter=True, callback=self.parse_content)
            self.logger.info('lv gonglue : %s' % json.dumps(result, ensure_ascii=False).encode('utf-8'))

    def parse_content(self, response):
        selector = Selector(response)
        date = selector.xpath('//span[@id="subtime"]/text()').extract_first().replace(u'发表时间：', '').strip(' \n\r')+':00'
        content = ''.join(selector.xpath('//div[@id="content"]/node()').extract())
        content = remove_tags(content).replace('\r\n', '')
        content = re.sub('\s*\r\n\s*', '', content)
        content = re.sub('\s*', '', content)

        result = response.meta['result']
        result['date'] = date
        result['content'] = content
        self.logger.info('lv gonglue : %s' % json.dumps(result, ensure_ascii=False).encode('utf-8'))


class LYYoujiSpider(LYSpider):
    name = 'ly_youji'

    youji_api = ('http://go.ly.com/ajax/GetNewRaiderInfo', 138)

    POST_HEADERS = {
        'Host' : 'go.ly.com',
        'Accept' : '*/*',
        'Origin' : 'http://go.ly.com',
        'X-Requested-With' : 'XMLHttpRequest',
        'Content-Type' : 'application/x-www-form-urlencoded',
        'Referer' : 'http://go.ly.com/youji/',
        'Accept-Encoding' : 'gzip, deflate',
        'Accept-Language' : 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2,ja;q=0.2'
    }

    def start_requests(self):
        for page in range(self.youji_api[1]):
            formdata = {
                'type' : '1',
                'destItemId' : '',
                'destItemKind' : '',
                'travelWay' : '',
                'pageIndex' : str(page+1),
                'pageSize' : '15'
            }
            yield FormRequest(self.youji_api[0], formdata=formdata, headers=self.POST_HEADERS, callback=self.parse_gonglue)
