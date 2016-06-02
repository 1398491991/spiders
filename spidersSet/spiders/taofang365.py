# -*- coding: utf-8 -*-

from spidersSet.items import SpiderssetItem
# import re
import copy
from scrapy.http import Request
from spiderBase import spiderBase
# from spidersSet.publicProcedureSet.dataStreamParse import getReListElement
from spidersSet.publicProcedureSet import kaipanTimeParse
from spidersSet.publicProcedureSet import createSaveHouseImgPath
from spidersSet.publicProcedureSet import judgeCityName,judgeAreaName,judgeNewCommunity
from spidersSet.publicProcedureSet import connectDataBase
from spidersSet.publicProcedureSet import normCityAreaName
class Taofang365Spider(spiderBase):
    name = "taofang365"
    # allowed_domains = ["nj.house365"]
    comNumber=13  # 网站的编号
    start_urls = (
        'http://nj.house365.com/',
    )


    def parse(self, response):
        if not isinstance(self.comNumber,int):
            raise Exception(u'---------- 没有设置网站编号----- comNumber ----------------- ')
        self.conn=connectDataBase(self.name)
        if not createSaveHouseImgPath(self.name):
            ###文件夹创建失败  结束爬虫
            return

        # 解析给网站的所有城市以及Url
        cityName_list=response.xpath('//div[@class="sm_station_hot"]/a/text()').extract()
        cityStartUrl_list=response.xpath('//div[@class="sm_station_hot"]/a/@href').extract()
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
            cityStartUrl=cityStartUrl_list[i].replace('://','://newhouse.').replace('index.html','house/')
            #http://newhouse.nj.house365.com/house/

            items['cityStartUrl']=cityStartUrl
            yield Request(cityStartUrl,callback=self.cityAreaParse,meta={'items':items})


    def cityAreaParse(self,response):
        # 解析摸个城市的所有区域的Url
        cityAreaName_list=response.xpath('//a[@class="clickStatistics_xfsxqs"]/text()').extract()  #[1:]#第一个是 "全部"
        cityAreaStartUrl_list=response.xpath('//a[@class="clickStatistics_xfsxqs"]/@data-value').extract()#[1:]
        if len(cityAreaName_list)!=len(cityAreaStartUrl_list):
            return
        items= response.meta["items"]
        for i,cityAreaName in enumerate(cityAreaName_list):
            cityAreaName=normCityAreaName(cityAreaName)
            if not judgeAreaName(self.conn.cursor(),cityAreaName):
                continue
            items['cityAreaName']=cityAreaName   #  例如  松江区
            cityAreaStartUrl=response.url+"dist-%s_p-1"%cityAreaStartUrl_list[i]
            # 拼接 http://newhouse.nj.house365.com/house/dist-12
            items['cityAreaStartUrl']=cityAreaStartUrl #  http://sh.jiwu.com/loupan/list-qa14137.html
            yield Request(cityAreaStartUrl,callback=self.communityParse,meta={'items':items})


    def communityParse(self,response):

        communityCoverUrl_list=map(lambda x:x.replace('/thumb',''),
           response.xpath('//div[@class="img_fl fl"]/a/img/@src').extract()
        ) #封面
        communityHomeUrl_list=response.xpath('//div[@class="tit"]/h3/a/@href').extract()##具体Url
        communityName_list=response.xpath('//div[@class="tit"]/h3/a/text()').extract() ##楼盘名称
        N=len(communityName_list)
        if N!=len(communityHomeUrl_list)!=len(communityCoverUrl_list):
            return

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
                items['communityName']=communityName
                items['communityCoverUrl']=communityCoverUrl_list[i]
                items['communityAreaData']=communityAreaData   # 是新的楼盘 返回区域的id和区域名称
                communityHomeUrl=communityHomeUrl_list[i]
                items['communityHomeUrl']=communityHomeUrl #例如 http://changjiangfengjing.house365.com/
                items['communityDetailUrl']=communityHomeUrl+'/intro/'  # http://changjiangfengjing.house365.com/intro/
                items['communityHouseTypeUrl']=communityHomeUrl+'/hx/' # http://changjiangfengjing.house365.com/hx/
                yield Request(communityHomeUrl,callback=self.communityHomeParse,meta={'items':items})
            except:
                continue

        try:
            if  'searchNone' not in response.body:  # 这是一个不好的方法  但是没有办法
                nextPageUrl_list=response.url.split('-')
                nextPageUrl='-'.join(nextPageUrl_list[:-1])+'-%s'%(int(nextPageUrl_list[-1])+1)
                print '\n---------------- NextUrl : %s ---------------\n'%nextPageUrl
                yield Request(nextPageUrl,callback=self.communityParse,meta={'items':itemsNextPage})
        except Exception:
            return

    def communityHomeParse(self,response):
        kaipanTime=response.\
            xpath('//table[@class="business-home-table"]/tr[3]/td[2]/text()|//div[@class="w510 fr"]/div[5]/span/text()').\
            extract()
        # 由于这个网站的特殊原因  已经移动到  self.communityHomeParse 解析函数中
        # 这里可能需要好几个 xpath

        kaipanTime=kaipanTimeParse(kaipanTime)
        if kaipanTime is False:
            print u'------------------------- 错误的开盘时间 --------------------------'
            return
        items=response.meta['items']
        items['kaipanTime']=kaipanTime
        yield Request(items['communityDetailUrl'],callback=self.communityDetailParse,meta={'items':items})


    def communityDetailParse(self,response):

        # kaipanTime=response.xpath('//table[@class="lpm-section4-table mt30"]/tr[1]/td[4]/text()').extract_first()
        # 由于这个网站的特殊原因  已经移动到  self.communityHomeParse 解析函数中
        # kaipanTime=kaipanTimeParse(kaipanTime)
        # if kaipanTime is False:
        #     print u'------------------------- 错误的开盘时间 --------------------------'
        #     return
        dizhi=response.xpath('//div[@class="w720 fl"]/table[1]/tr[3]/td[last()]/text()').extract_first('').strip()
        wuye=response.xpath('//div[@class="w720 fl"]/table[3]/tr[6]/td[last()]/text()').extract_first('').strip()
        kaifashang=response.xpath('//div[@class="w720 fl"]/table[1]/tr[6]/td[last()]/text()').extract_first('').strip()
        jieshao=''.join(response.xpath('//div[@class="p10 border_ccc lh24"]/text()').extract()).strip()

        items=response.meta['items']
        # items['kaipanTime']=kaipanTime
        items['dizhi']=dizhi
        items['wuye']=wuye
        items['kaifashang']=kaifashang
        items['jieshao']=jieshao
        yield Request(items['communityHouseTypeUrl'],callback=self.communityHouseTypeParse,meta={'items':items})

    def communityHouseTypeParse(self,response):

        houseImgUrl_list=response.xpath('//li[@class="mr15"]/a/img/@src').extract()
        #例如  http://imgs.jiwu.com/attachment/housepic/2015/10/30/2007007_s.jpg
        houseType_list=response.xpath('//li[@class="mr15"]/p[2]/text()').extract()
        # houseArea_list=houseType_list # 特殊原因 两个放一起了  response.xpath('//p[@class="house-type-s3"]/text()').extract()
        items=response.meta['items']


        items['houseImgUrl_list']=houseImgUrl_list
        items['houseType_list']=houseType_list
        items['houseArea_list']=houseType_list  ## 特殊原因   houseArea_list=houseType_list=户型：4室2厅 面积：200㎡

        items['spidersName']=self.name
        items['comNumber']=self.comNumber
        print items
        yield items