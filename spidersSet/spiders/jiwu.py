# -*- coding: utf-8 -*-

from spidersSet.items import SpiderssetItem
import re
import copy
from scrapy.http import Request
from spiderBase import spiderBase
from spidersSet.publicProcedureSet import kaipanTimeParse
from spidersSet.publicProcedureSet import createSaveHouseImgPath
from spidersSet.publicProcedureSet import judgeCityName,judgeAreaName,judgeNewCommunity
from spidersSet.publicProcedureSet import connectDataBase
from spidersSet.publicProcedureSet import normCityAreaName
class JiwuSpider(spiderBase):
    name = "jiwu"
    comNumber=7  # 网站的编号
    allowed_domains = ["jiwu.com"]
    start_urls = (
        'http://www.jiwu.com/',
    )

    def parse(self, response):
        if not isinstance(self.comNumber,int):
            raise Exception('---------- 没有设置网站编号----- comNumber ----------------- ')
        self.conn=connectDataBase()
        if not createSaveHouseImgPath(self.name):
            ###文件夹创建失败  结束爬虫
            return

        # 解析给网站的所有城市以及Url
        cityName_list=response.xpath('//ul[@class="section-four-a2"]/li/a/text()').extract()
        cityStartUrl_list=response.xpath('//ul[@class="section-four-a2"]/li/a/@href').extract()
        if len(cityName_list)!=len(cityStartUrl_list):
            print 'len(cityName_list)!=len(cityStartUrl_list)'
            return
        N=len(cityName_list)
        for i in range(N):
            cityName=normCityAreaName(cityName_list[i])
            if not judgeCityName(self.conn.cursor(),cityName):  # 判断是否存在这个城市
                continue
            items=SpiderssetItem()
            items['cityName']=cityName
            cityStartUrl=cityStartUrl_list[i]+'/loupan/'
            items['cityStartUrl']=cityStartUrl
            yield Request(cityStartUrl,callback=self.cityAreaParse,meta={'items':items})



    def cityAreaParse(self,response):
        # 解析摸个城市的所有区域的Url
        cityAreaName_list=response.xpath('//div[@id="qy"]/div[@class="lp-pb-s2"]/ul/li/a/text()').extract()
        cityAreaStartUrl_list=response.xpath('//div[@id="qy"]/div[@class="lp-pb-s2"]/ul/li/a/@href').extract()
        N=len(cityAreaName_list)
        if N!=len(cityAreaStartUrl_list):
            return

        items= response.meta["items"]
        for i in range(N):
            cityAreaName=re.sub('\(\d+\)','',cityAreaName_list[i])#替换 例如 嘉兴(296) 变成 嘉兴
            cityAreaName=normCityAreaName(cityAreaName)
            if not judgeAreaName(self.conn.cursor(),cityAreaName):
                continue
            items['cityAreaName']=cityAreaName   #  例如  松江区
            cityAreaStartUrl=cityAreaStartUrl_list[i]
            items['cityAreaStartUrl']=cityAreaStartUrl #  http://sh.jiwu.com/loupan/list-qa14137.html
            yield Request(cityAreaStartUrl,callback=self.communityParse,meta={'items':items})


    def communityParse(self,response):

        nextPageUrl=response.xpath('//a[@class="tg-rownum-next index-icon"]/@href').extract_first()
        communityCoverUrl_list=response.xpath('//div[@class="index-scale loupan-list1-box1"]/a/img/@src').extract() #封面
        communityHomeUrl_list=response.xpath('//div[@class="index-scale loupan-list1-box1"]/a/@href').extract()##具体Urk
        communityName_list=response.xpath('//div[@class="index-scale loupan-list1-box1"]/a/img/@alt').extract() ##楼盘名称

        items=response.meta['items']
        itemsNextPage=copy.deepcopy(items)##用于下一页的item
        cityName=items[u'cityName']
        cityAreaName=items[u'cityAreaName']
        for i,communityName in enumerate(communityName_list):
            try:
                communityAreaData=judgeNewCommunity(self.conn.cursor(),communityName_list,cityAreaName,cityName,
                                                    communityHomeUrl=communityHomeUrl_list[i])
                if not communityAreaData: # 不是新楼盘
                    continue
                items['communityAreaData']=communityAreaData   # 是新的楼盘 返回区域的id和区域名称
                items['communityName']=communityName_list
                items['communityCoverUrl']=communityCoverUrl_list[i].replace('_s.jpg','.jpg')
                communityHomeUrl=communityHomeUrl_list[i]
                items['communityHomeUrl']=communityHomeUrl #例如 http://sh.jiwu.com/loupan/272225.html
                items['communityDetailUrl']=communityHomeUrl.replace('loupan','detail') #http://sh.jiwu.com/detail/272225.html
                items['communityHouseTypeUrl']=communityHomeUrl.replace('loupan/','huxing/list-loupan') #http://sh.jiwu.com/huxing/list-loupan272225.html
                yield Request(items['communityDetailUrl'],callback=self.communityDetailParse,meta={'items':items})
            except:
                continue
        if  nextPageUrl:
            print '\n---------------- NextUrl : %s ---------------\n'%nextPageUrl
            yield Request(nextPageUrl,callback=self.communityParse,meta={'items':itemsNextPage})

    def communityDetailParse(self,response):

        kaipanTime=response.xpath('//table[@class="lpm-section4-table mt30"]/tr[1]/td[4]/text()').extract_first()

        kaipanTime=kaipanTimeParse(kaipanTime)
        if kaipanTime is False:
            print u'------------------------- 错误的开盘时间 --------------------------'
            return
        dizhi=response.xpath('//table[@class="lpm-section4-table mt30"]/tr[2]/td[4]/span/text()').extract_first('').strip()
        wuye=response.xpath('//table[@class="lpm-section4-table mt30"]/tr[6]/td[2]/text()').extract_first('').strip()
        kaifashang=response.xpath('//table[@class="lpm-section4-table mt30"]/tr[7]/td[2]/span/text()').extract_first('').strip()
        jieshao=response.xpath('//div[@class="container-super lpxq"]/p/text()').extract_first('').strip()

        items=response.meta['items']
        items['kaipanTime']=kaipanTime
        items['dizhi']=dizhi
        items['wuye']=wuye
        items['kaifashang']=kaifashang
        items['jieshao']=jieshao
        yield Request(items['communityHouseTypeUrl'],callback=self.communityHouseTypeParse,meta={'items':items})

    def communityHouseTypeParse(self,response):

        houseImgUrl_list=response.xpath('//img[@class="fl trs lpm-section3-img"]/@src').extract()
        #例如  http://imgs.jiwu.com/attachment/housepic/2015/10/30/2007007_s.jpg
        houseType_list=response.xpath('//p[@class="house-type-s2"]/a/text()').extract()
        houseArea_list=response.xpath('//p[@class="house-type-s3"]/text()').extract()
        items=response.meta['items']

        items['houseImgUrl_list']=map(lambda x:x.replace(u"_s.jpg",u".jpg"),houseImgUrl_list)
        items['houseType_list']=houseType_list
        items['houseArea_list']=houseArea_list
        items['spidersName']=self.name
        items['comNumber']=self.comNumber
        print items
        yield items
