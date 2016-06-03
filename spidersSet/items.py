# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SpiderssetItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    cityName=scrapy.Field()   #城市名
    cityStartUrl=scrapy.Field()  # 城市Url
    cityAreaName=scrapy.Field()  #区域名
    cityAreaStartUrl=scrapy.Field()  #区域 Url
    communityCoverUrl=scrapy.Field()  #封面Url
    communityDetailUrl=scrapy.Field()  #详情Url
    communityHomeUrl=scrapy.Field()  #主页Url
    communityHouseTypeUrl=scrapy.Field()#户型Url
    communityName=scrapy.Field() #楼盘名
    kaipanTime=scrapy.Field()#开盘时间
    ruzhuTime=scrapy.Field()
    dizhi=scrapy.Field()  #地址
    wuye=scrapy.Field() #物业
    kaifashang=scrapy.Field() #开发商
    jieshao=scrapy.Field() #介绍
    jiaotong_bus=scrapy.Field()#交通公交
    jiaotong_metro=scrapy.Field()#交通地铁
    houseImgUrl_list=scrapy.Field()
    houseType_list=scrapy.Field()
    houseArea_list=scrapy.Field()
    spidersName=scrapy.Field()
    comNumber=scrapy.Field()
    communityAreaData=scrapy.Field()
