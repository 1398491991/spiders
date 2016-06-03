# -*- coding: utf-8 -*-
import re
from spidersSet.items import SpiderssetItem
from scrapy.spider import Request
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from spidersSet.publicProcedureSet import kaipanTimeParse
from spidersSet.publicProcedureSet import judgeAreaName,judgeCityName,judgeNewCommunity
from spidersSet.publicProcedureSet import normCityAreaName
from spidersSet.publicProcedureSet import connectDataBase
from spidersSet.publicProcedureSet import createSaveHouseImgPath

class QfangwangSpider(CrawlSpider):
    name = "Qfangwang"
    # allowed_domains = ["shanghai.qfang.com"]
    comNumber=16 #网站编号
    start_urls = (
        'http://shanghai.qfang.com/newhouse/list',
        # 'http://shanghai.qfang.com/',
    )

    rules = (
        #  没有callback意味着follow默认为True
        Rule(LinkExtractor(allow=('http:/\w+\.qfang.com', ))),  ## 匹配每一个城市的  http://shanghai.qfang.com/newhouse/list

        Rule(LinkExtractor(allow=('/newhouse/desc/\d+', )),callback="parse_item"),
        # 匹配该的楼盘列表 http://shanghai.qfang.com/newhouse/desc/4060247

        Rule(LinkExtractor(allow=('/newhouse/list/n\d+', ))),  #下一页
    )
    if not isinstance(comNumber,int):
        raise Exception(u'------------- 没有设置网站编号----- comNumber ----------------- ')
    conn=connectDataBase()
    createSaveHouseImgPath(name)
    ###文件夹创建失败  结束爬虫


    def parse_item(self, response):

        cityName=response.xpath('//div[@id="curCity"]/span[1]/text()').extract_first()
        cityName=normCityAreaName(cityName)
        if not cityName or not judgeCityName(self.conn.cursor(),cityName):
            return
        cityAreaName=response.xpath('//div[@class="newhouse_details fl "]/ul/li[3]/text()').extract_first('')
        cityAreaName=normCityAreaName(cityAreaName.split(' ')[0])
        if not cityAreaName or not judgeAreaName(self.conn.cursor(),cityAreaName):
            return

        communityName=response.xpath('//div[@class="house_title"]/h1/text()').extract_first()
        communityCoverUrl=response.xpath('//div[@class="album_detail fl"]/a/img/@src').extract_first()
        if not communityName or not communityCoverUrl:
            return

        communityAreaData=judgeNewCommunity(self.conn.cursor(),communityName,cityAreaName,cityName,
                                            communityHomeUrl=response.url)
        if not communityAreaData:
            return

        kaipanTime=response.xpath('//div[@class="discription_more p_15"]/p[3]/text()').extract_first()
        kaipanTime=kaipanTimeParse(kaipanTime)
        if kaipanTime is False:
            return
        dizhi=response.xpath('//div[@class="discription_more p_15"]/p[last()]/em/text()').extract_first('').strip()
        wuye=response.xpath('//div[@class="discription_more p_15"]/p[last()-1]/em/text()').extract_first('').strip()
        kaifashang=response.xpath('//div[@class="discription_more p_15"]/p[5]/text()').extract_first('').strip()
        jieshao=response.xpath('//div[@id="lightspot"]/@content').extract_first('').strip()
        items = SpiderssetItem()
        items['communityAreaData']=communityAreaData
        items['communityCoverUrl']=re.sub('\d{3}x\d{3}','600x450',communityCoverUrl).strip()  # 这个链接有 \n \r 等
        items['comNumber']=self.comNumber
        items['spidersName']=self.name
        items['communityName']=communityName
        items['cityName']=cityName
        items['cityAreaName']=cityAreaName
        items['kaipanTime']=kaipanTime
        items['dizhi']=dizhi
        items['wuye']=wuye
        items['kaifashang']=kaifashang
        items['jieshao']=jieshao
        items['communityHomeUrl']=response.url
        communityHouseTypeUrl=response.xpath('//li[@id="noCur"]/a/@href').extract_first()
        if communityHouseTypeUrl:
            communityHouseTypeUrl=response.urljoin(communityHouseTypeUrl)
            items['communityHouseTypeUrl']=communityHouseTypeUrl
            items['houseImgUrl_list']=[]
            items['houseType_list']=[]
            items['houseArea_list']=[]
            yield Request(communityHouseTypeUrl,callback=self.communityHouseTypeParse,meta={'items':items})
        else:
            yield items

    def communityHouseTypeParse(self,response):
        items=response.meta['items']
        houseImgUrl_list=response.xpath('//div[@class="list_view"]/p[@class="img_con"]/img/@src').extract()
        houseImgUrl_list=map(lambda x:re.sub('\d{3}x\d{3}','800x600',x.strip()),houseImgUrl_list)
        #例如  http://is50.qfangimg.com/shanghai/community/chongmingqita/lvdizhangdao/ht/800x600/ad46592f-8f54-4d47-9324-7a7abcf4fc0e.jpg
        houseType_list=response.xpath('//div[@class="list_view"]/p[@class="img_description"]/text()').extract()
        # houseArea_list=houseType_list #重复了
        items['houseImgUrl_list'].extend(houseImgUrl_list)
        items['houseType_list'].extend(houseType_list)
        items['houseArea_list'].extend(houseType_list)
        houseNextPage=response.xpath('//a[@class="turnpage_next fr"]/@href').extract_first()
        if houseNextPage:
            yield Request(response.urljoin(houseNextPage),callback=self.communityHouseTypeParse,meta={'items':items})
        else:
            yield items