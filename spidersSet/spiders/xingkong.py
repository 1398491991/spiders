# -*- coding: utf-8 -*-
# import scrapy

from spidersSet.items import SpiderssetItem
# import re
import copy
from scrapy.http import Request
from spiderBase import spiderBase
from spidersSet.publicProcedureSet import kaipanTimeParse
from spidersSet.publicProcedureSet import createSaveHouseImgPath
from spidersSet.publicProcedureSet import connectDataBase
from spidersSet.publicProcedureSet import judgeCityName,judgeAreaName,judgeNewCommunity
from spidersSet.publicProcedureSet import myGetHtml,my_extract_first
from lxml import etree
from spidersSet.publicProcedureSet import normCityAreaName
class XingkongSpider(spiderBase):
    name = "xingkong"
    # allowed_domains = ["http://www.xkhouse.com/"]
    comNumber=13  # 网站的编号
    start_urls = (
        'http://www.xkhouse.com/',
    )

    def parse(self, response):
        if not isinstance(self.comNumber,int):
            raise Exception(u'---------- 没有设置网站编号 comNumber 参数 ----------------- ')
        self.conn=connectDataBase()
        if not createSaveHouseImgPath(self.name):
            ###文件夹创建失败  结束爬虫
            return

        # 解析给网站的所有城市以及Url
        cityName_list=response.xpath('//div[@class="topnav-sub city"][1]/a/text()').extract()
        cityStartUrl_list=response.xpath('//div[@class="topnav-sub city"][1]/a/@href').extract()
        # cityStartUrl_list=filter(lambda x:'xkhouse' in x,cityStartUrl_list)
        if len(cityName_list)!=len(cityStartUrl_list):
            print 'len(cityName_list)!=len(cityStartUrl_list)'
            return
        N=len(cityName_list)
        for i in range(N):
            cityName=normCityAreaName(cityName_list[i])
            if not judgeCityName(self.conn.cursor(),cityName_list[i]):  # 判断是否存在这个城市
                continue
            items=SpiderssetItem()
            items['cityName']=cityName
            cityStartUrl=cityStartUrl_list[i].replace('://','://newhouse.')+'loupan/'
            items['cityStartUrl']=cityStartUrl
            yield Request(cityStartUrl,callback=self.cityAreaParse,meta={'items':items})

    def cityAreaParse(self,response):
        # 解析摸个城市的所有区域的Url
        cityAreaName_list=response.xpath('//div[@class="filter"]/dl[1]/dd/a/text()').extract()
        cityAreaStartUrl_list=response.xpath('//div[@class="filter"]/dl[1]/dd/a/@href').extract()
        N=len(cityAreaName_list)
        if N!=len(cityAreaStartUrl_list):
            return
        items= response.meta["items"]
        for i in range(N):
            cityAreaName=normCityAreaName(cityAreaName_list[i])
            if not judgeAreaName(self.conn.cursor(),cityAreaName_list[i]):
                continue
            items['cityAreaName']=cityAreaName  #  例如  杨浦
            cityAreaStartUrl=response.urljoin(cityAreaStartUrl_list[i])
            items['cityAreaStartUrl']=cityAreaStartUrl #  http://newhouse.sh.xkhouse.com/loupan/a1670/
            yield Request(cityAreaStartUrl,callback=self.communityParse,meta={'items':items})

    def communityParse(self,response):

        nextPageUrl=response.xpath('//div[@class="page_turning"]//a[@class="next"]/@href').extract_first()
        communityCoverUrl_list=response.xpath('//@data-original').extract() #封面
        communityHomeUrl_list=response.xpath('//div[@class="loupan_tit"]/h3/a/@href').extract()##具体Url
        communityName_list=response.xpath('//div[@class="loupan_tit"]/h3/a/text()').extract() ##楼盘名称

        items=response.meta['items']
        itemsNextPage=copy.deepcopy(items)##用于下一页的item
        cityName=items[u'cityName']
        cityAreaName=items[u'cityAreaName']
        for i,communityName in enumerate(communityName_list):
            try:
                communityAreaData=judgeNewCommunity(self.conn.cursor(),communityName,cityAreaName,cityName,
                                                    communityHomeUrl=communityHomeUrl_list[i])
                if not communityAreaData: # 不是新楼盘
                    continue
                items['communityAreaData']=communityAreaData   # 是新的楼盘 返回区域的id和区域名称
                items['communityName']=communityName
                items['communityCoverUrl']=communityCoverUrl_list[i]
                communityHomeUrl=response.urljoin(communityHomeUrl_list[i])
                items['communityHomeUrl']=communityHomeUrl #例如 http://newhouse.sh.xkhouse.com/600000718/
                items['communityDetailUrl']=communityHomeUrl+'gaikuang.html' #http://newhouse.sh.xkhouse.com/600000718/gaikuang.html
                items['communityHouseTypeUrl']=communityHomeUrl+'huxing.html' # http://newhouse.sh.xkhouse.com/600000718/huxing.html
                yield Request(items['communityDetailUrl'],callback=self.communityDetailParse,meta={'items':items})
            except:
                continue
        if  nextPageUrl:
            print '\n---------------- NextUrl : %s ---------------\n'%response.urljoin(nextPageUrl)
            yield Request(response.urljoin(nextPageUrl),callback=self.communityParse,meta={'items':itemsNextPage})

    def communityDetailParse(self,response):

        kaipanTime=response.xpath('//div[@class="info_cheap"]/dl/dd[2]/text()').extract_first()

        kaipanTime=kaipanTimeParse(kaipanTime)
        if kaipanTime is False:
            print u'------------------------------ 错误的开盘时间 --------------------------'
            return
        dizhi=response.xpath('//div[@class="wrap mb20"]/div[1]/div[1]/table/tr[1]/td[2]/text()').extract_first('').strip()
        wuye=response.xpath('//div[@class="wrap mb20"]/div[1]/div[2]/table/tr[7]/td[1]/text()').extract_first('').strip()
        kaifashang=response.xpath('//div[@class="wrap mb20"]/div[1]/div[1]/table/tr[3]/td[2]/text()').extract_first('').strip()
        jieshao=response.xpath('//div[@class="wrap mb20"]/div[1]/div[5]/table/tr/td/p/text()').extract_first('').strip()

        items=response.meta['items']
        items['kaipanTime']=kaipanTime
        items['dizhi']=dizhi
        items['wuye']=wuye
        items['kaifashang']=kaifashang
        items['jieshao']=jieshao
        yield Request(items['communityHouseTypeUrl'],callback=self.communityHouseTypeParse,meta={'items':items})


    def communityHouseTypeParse(self,response):
        houseImgSubUrl_list=map(lambda x:response.url+x,response.xpath('//ul[@class="picList clearfix"]/li/a/@href').extract())
        ### ['?type=0&tId=73446', '?type=0&tId=73447', '?type=0&tId=73448']
        items=response.meta['items']
        items['houseImgUrl_list']=[]
        items['houseType_list']=[]
        items['houseArea_list']=[]
        for url in houseImgSubUrl_list:
            html=myGetHtml(url)
            if not html:
                continue
            (houseImgUrl,houseType,houseArea)=self.communityHouseTypeSubParse(etree.HTML(html),
                                                                              response.meta['items']['communityName'])
            if houseImgUrl:
                items['houseImgUrl_list'].append(houseImgUrl)
                items['houseType_list'].append(houseType)
                items['houseArea_list'].append(houseArea)


        items['spidersName']=self.name
        items['comNumber']=self.comNumber
        print items
        yield items
    def communityHouseTypeSubParse(self,response,communityName):

        return (my_extract_first(response.xpath('//div[@class="huxing_list"]/a/img/@src')),
                my_extract_first(response.xpath('//div[@class="huxing_mation"]/ul/li[1]/text()'),communityName),
                my_extract_first(response.xpath('//div[@class="huxing_mation"]/ul/li[2]/text()')),)





