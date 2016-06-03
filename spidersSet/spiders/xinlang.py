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
from spidersSet.publicProcedureSet import my_extract_first
from spidersSet.publicProcedureSet import normCityAreaName
class XinlangSpider(spiderBase):
    name = "xinlang"
    comNumber=15  # 网站的编号
    # allowed_domains = ["xinglang"]
    start_urls = (
        'http://bj.house.sina.com.cn/cityguide/',
    )

    def parse(self, response):
        if not isinstance(self.comNumber,int):
            raise Exception('---------- 没有设置网站编号----- comNumber ----------------- ')
        self.conn=connectDataBase()
        if not createSaveHouseImgPath(self.name):
            ###文件夹创建失败  结束爬虫
            return

        # 解析给网站的所有城市以及Url
        cityName_list=response.xpath('//div[@class="leter_list clearfix"]/ul/li/a/text()').extract()
        cityStartUrl_list=response.xpath('//div[@class="leter_list clearfix"]/ul/li/a/@href').extract()
        if len(cityName_list)!=len(cityStartUrl_list):
            print 'len(cityName_list)!=len(cityStartUrl_list)'
            return
        # N=len(cityName_list)
        for i,cityName in enumerate(cityName_list):
            cityName=normCityAreaName(cityName)
            if not judgeCityName(self.conn.cursor(),cityName):  # 判断是否存在这个城市
                continue
            items=SpiderssetItem()
            items['cityName']=cityName
            items['spidersName']=self.name
            items['comNumber']=self.comNumber
            # cityStartUrl=cityStartUrl_list[i]+'/loupan/'
            # items['cityStartUrl']=cityStartUrl
            yield Request(cityStartUrl_list[i],callback=self.communityListUrlParse,meta={'items':items})
            ### 这里不能直接匹配出 真真的 楼盘列表的网址  所以在此解析  http://maoming.house.sina.com.cn/ 这样的 link
            ## 作为中间件 self.communityListUrlParse
    def communityListUrlParse(self,response):
        cityStartUrl=response.xpath('//div[@id="con_search_1"]/form/@action').extract_first()
        if not cityStartUrl:
            return
        items=response.meta['items']
        items['cityStartUrl']=cityStartUrl
        yield Request(cityStartUrl,callback=self.cityAreaParse,meta={'items':items})

    def cityAreaParse(self,response):
        # 解析摸个城市的所有区域的Url
        cityAreaName_list=response.xpath('//div[@id="dict_key"]/dl[1]/dd/ul[1]/li/a/text()').extract()
        cityAreaStartUrl_list=response.xpath('//div[@id="dict_key"]/dl[1]/dd/ul[1]/li/a/@href').extract()
        if len(cityAreaName_list)!=len(cityAreaStartUrl_list):
            return
        items= response.meta["items"]
        for i,cityAreaName in enumerate(cityAreaName_list):
            cityAreaName=normCityAreaName(cityAreaName)
            if not judgeAreaName(self.conn.cursor(),cityAreaName):
                continue
            items['cityAreaName']=cityAreaName   #  例如  松江区
            cityAreaStartUrl=cityAreaStartUrl_list[i]
            items['cityAreaStartUrl']=cityAreaStartUrl #  http://sh.jiwu.com/loupan/list-qa14137.html
            yield Request(cityAreaStartUrl,callback=self.communityParse,meta={'items':items})



    def communityParse(self,response):

        nextPageUrl=response.xpath('//div[@id="t_leftCont"]//a[@class="next"]/@href').extract_first()
        communityCoverUrl_list=response.xpath('//img[@class="p_a_house"]/@lsrc').extract() #封面
        communityCoverUrl_list=map(lambda x:re.sub('\d{3}X\d{3}','',x),communityCoverUrl_list)
        # 'http://src.house.sina.com.cn/imp/imp/deal/3d/f4/8/5b8acefd149f65d4e63d6e4925e_p7_mk7_os94a95e_cm320X240.jpg'
        # http://src.house.sina.com.cn/imp/imp/deal/3d/f4/8/5b8acefd149f65d4e63d6e4925e_p7_mk7_os94a95e_cm.jpg

        communityHomeUrl_list=response.xpath('//div[@class="p_tit"]/a/@href').extract()##具体Url
        communityName_list=response.xpath('//div[@class="p_tit"]/a/text()').extract() ##楼盘名称
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
                items['communityHomeUrl']=communityHomeUrl_list[i] #例如 http://data.house.sina.com.cn/sh131543/#wt_source=search_nr_bt06
                # items['communityDetailUrl']=re.sub('#wt_source=search_nr_bt\d+','xinxi/#wt_source=nlpxq_dh2_xxxx',communityHomeUrl)
                #http://data.house.sina.com.cn/sh131543/xinxi/#wt_source=nlpxq_dh2_xxxx
                # items['communityHouseTypeUrl']=re.sub('#wt_source=search_nr_bt\d+','pic/#wt_source=nlpxq_dh2_zxtp',communityHomeUrl)
                # http://data.house.sina.com.cn/sh131543/pic/#wt_source=nlpxq_dh2_zxtp
                yield Request(communityHomeUrl_list[i],callback=self.communityHomeParse,meta={'items':items})
            except:
                continue
        if  nextPageUrl:
            nextPageUrl=response.urljoin(nextPageUrl)
            print '\n---------------- NextUrl : %s ---------------\n'%nextPageUrl
            yield Request(nextPageUrl,callback=self.communityParse,meta={'items':itemsNextPage},priority=-10)

    def communityHomeParse(self,response):
        items=response.meta['items']
        items['communityDetailUrl']=response.xpath('//div[@class="w_header03"]/ul[1]/li[2]/a/@href').extract_first()
        #http://data.house.sina.com.cn/sh131543/xinxi/#wt_source=nlpxq_dh2_xxxx
        items['communityHouseTypeUrl']=response.xpath('//div[@class="w_header03"]/ul[1]/li[4]/a/@href').extract_first()
        # http://data.house.sina.com.cn/sh131543/pic/#wt_source=nlpxq_dh2_zxtp
        if not items['communityDetailUrl']:
            return

        yield Request(items['communityDetailUrl'],callback=self.communityDetailParse,meta={'items':items})



    def communityDetailParse(self,response):

        kaipanTime=response.xpath('//div[@id="cTab1_con1"]/div[1]/ul/li[6]/span[2]/text()').extract_first()
        ruzhuTime=response.xpath('//div[@id="cTab1_con1"]/div[1]/ul/li[8]/span[2]/text()').extract_first()
        kaipanTime=kaipanTimeParse(kaipanTime)
        ruzhuTime=kaipanTimeParse(ruzhuTime)
        if kaipanTime is False or ruzhuTime is False:
            print u'------------------------- 不符合阈值的 开盘时间 或者 入住时间 --------------------------'
            return
        dizhi=response.xpath('//div[@id="cTab1_con1"]/div[1]/ul/li[1]/span[2]/text()').extract_first('').strip()
        wuye=''  # 这个网站貌似没有物业公司信息
        jiaotong_bus=response.xpath('//div[@id="cTab1_con1"]/div[1]/ul/li[17]/span[2]/text()').extract_first('').strip()
        kaifashang=response.xpath('//div[@id="cTab1_con1"]/div[1]/ul/li[14]/span[2]/text()').extract_first('').strip()
        jieshao=response.xpath('//div[@id="cTab1_con2"]/div[1]/ul[5]/p/text()').extract_first('').strip()

        items=response.meta['items']
        items['kaipanTime']=kaipanTime
        items['ruzhuTime']=ruzhuTime
        items['dizhi']=dizhi
        items['wuye']=wuye
        items['jiaotong_bus']=jiaotong_bus
        items['kaifashang']=kaifashang
        items['jieshao']=jieshao
        if not  items['communityHouseTypeUrl']:
            print items
            yield items
        else:
            yield Request(items['communityHouseTypeUrl'],callback=self.communityHouseTypeParse,meta={'items':items})


    def communityHouseTypeParse(self,response):
        communityHouseTypeSubUrl_list=response.xpath('//div[@class="housingNav w"]//a/@href').extract()
        """
        ['http://data.house.sina.com.cn/sh4653/pic/#wt_source=data6_tpdh_all',
         'http://data.house.sina.com.cn/sh4653/shequ/#wt_source=data6_tpdh_sqsj',
         'http://data.house.sina.com.cn/sh4653/huxing/#wt_source=data6_tpdh_hxt',]  类似这样的 一个列表
         主要是图片有很多选项  具体参考 http://data.house.sina.com.cn/sh131552/pic/#wt_source=nlpxq_dh2_zxtp
        """
        communityHouseTypeSubUrl=my_extract_first(filter(lambda x:'huxing' in x,communityHouseTypeSubUrl_list))
        if not communityHouseTypeSubUrl:
            return
        yield Request(communityHouseTypeSubUrl,callback=self.communityHouseTypeSubParse,meta={'items':response.meta['items']})


    def communityHouseTypeSubParse(self,response):
        houseImgUrl_list=map(lambda x:re.sub('\d{3}X\d{3}','',x),
                             response.xpath('//a[@class="showImg"]/img/@src').extract())
        #例如 http://src.house.sina.com.cn/imp/imp/deal/99/1b/d/1d7e2081ce5364c8aa68fc04b53_p7_mk7_osf5ee74_cm240X180.jpg

        houseType_list=response.xpath('//span[@class="infoSpan"]/span[last()]/text()').extract()
        houseArea_list=response.xpath('//a[@class="showImg"]/img/@title').extract()
        items=response.meta['items']
        items['houseImgUrl_list']=houseImgUrl_list
        items['houseType_list']=houseType_list
        items['houseArea_list']=houseArea_list
        print items
        yield items


