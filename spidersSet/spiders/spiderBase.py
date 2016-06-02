#coding=utf-8
from scrapy import Spider
class spiderBase(Spider):

    comNumber=None  # 网站的编号
    def parse(self, response):
        raise NotImplementedError

    def cityAreaParse(self,response):
        raise NotImplementedError

    def communityParse(self,response):
        raise NotImplementedError

    def communityDetailParse(self,response):
        raise NotImplementedError

    def communityHouseTypeParse(self,response):
        raise NotImplementedError
