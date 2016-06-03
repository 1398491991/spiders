# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from publicProcedureSet.dataStreamParse import connectDataBase
# from publicProcedureSet.dataStreamParse import judgeNewCommunity
from publicProcedureSet.publicConfig import ZERO_HOUSE
from publicProcedureSet.dataStreamParse import downLoadImg
from publicProcedureSet.dataStreamParse import communityTableSave,houseTableSave
from publicProcedureSet.imageStreamParse import deleteImg
from publicProcedureSet.dataStreamParse import houseTypeParse,houseAreaParse
from publicProcedureSet.dataStreamParse import acquireGeographyCoordinates
from publicProcedureSet.dataStreamParse import nowTime
from publicProcedureSet.dataStreamParse import initTableId
from publicProcedureSet.dataStreamParse import existNewCommunityTable
from publicProcedureSet.publicConfig import init_location_community_id,\
    init_ifuwo_houselayout_id,\
    init_ifuwoext_houselayoutext_id

from publicProcedureSet.publicConfig import newComunityTable  #保存楼盘信息的表

class SpiderssetPipeline(object):
    def __init__(self):
        self.conn=connectDataBase('Pipeline')  #获取数据库连接
        if not existNewCommunityTable(self.conn.cursor(),newComunityTable):
            raise Exception(u'\n---------- not found newComunityTable : %s ----------\n'%newComunityTable)
        initTableId(self.conn,newComunityTable,init_location_community_id)
        initTableId(self.conn,'ifuwo_houselayout',init_ifuwo_houselayout_id)
        initTableId(self.conn,'ifuwoext_houselayoutext',init_ifuwoext_houselayoutext_id)
        if ZERO_HOUSE:
            print u'----------------------- 保存 “零户型” ------------------------'
        else:
            print u'----------------------- 不保存 “零户型” ----------------------------'
    def process_item(self, item, spider):
        self.filterItem(item)
        return item

    def filterItem(self,item):
        # 主要是筛选 城市和区域还有楼盘是否是新楼盘
        # 而 开盘时间有与不需要链接数据库判断 所欲在前面 jiwu spiders 已经 判断了
        # cityName=item[u'cityName']
        # # if not judgeCityName(self.conn.cursor(),cityName):
        # #     return False
        # cityAreaName=item[u'cityAreaName']
        # # if not judgeAreaName(self.conn.cursor(),cityAreaName):
        # #     return False
        # #####到了这里证明城市和区域都没有问题
        # ###开始判断是否是新楼盘
        # communityName=item[u'communityName']
        #
        # #返回区域的id和区域名称
        # communityAreaData=judgeNewCommunity(self.conn.cursor(),communityName,cityAreaName,cityName)
        # if not communityAreaData:
        #     return False
        ###到了这里证明是新的楼盘  可以开始下载 楼盘封面了
        # communityAreaData=item['communityAreaData']
        if not (item['houseImgUrl_list'] or ZERO_HOUSE): # 零户型判别
            return

        folderName,UUID=downLoadImg(item[u'communityCoverUrl'],imgType=0,spidersName=item[u'spidersName'])
        if not folderName:#证明这里没有下载成功
            return False
        # 可以进行插入操作  传入 folderName,UUID 是用于插入错误删除用的
        # communityAreaData 是用于插入用的
        self.insertCommunityTable(item,folderName,UUID,item['communityAreaData'])

    def insertCommunityTable(self,item,folderName,UUID,communityAreaData):
        communityAreaId,communityArea=communityAreaData
        cityAreaName=item[u'cityAreaName']
        communityName=item[u'communityName']
        dizhi=item.get(u'dizhi')
        jieshao=item.get(u'jieshao')
        kaifashang=item.get(u'kaifashang')
        kaipanTime=item.get(u'kaipanTime')
        wuye=item.get(u'wuye')
        lat,lon=acquireGeographyCoordinates(communityName,cityAreaName,item[u'cityName'],dizhi)
        # 纬度 经度 的格式
        insertCommunityTuple=(0,nowTime(),nowTime(),
                              communityName,communityAreaId,dizhi,
                              lon,lat,0,kaifashang,'','',
                              jieshao,wuye,None,None,item.get('jiaotong_bus'),None,
                              UUID,kaipanTime,item.get('ruzhuTime'))
        insertDict={u'location_community':insertCommunityTuple}
        communityId=communityTableSave(self.conn,insertDict,tableName=newComunityTable)
        if not communityId:#证明插入错误了
        #     #要删除封面文件
            return deleteImg(folderName,UUID,item[u'spidersName']) #一定返回的是 False
        # ##到了这里所有 community 数据表以及封面就完成了
        # ##  插入数据到  户型表
        self.insertHouseTable(item,communityId)
    def insertHouseTable(self,item,communityId):
        cityName=item[u'cityName']
        communityName=item[u'communityName']
        houseImgUrl_list=item.get(u'houseImgUrl_list',[])
        houseType_list=item.get(u'houseType_list',[])
        houseArea_list=item.get(u'houseArea_list',[])
        ##这里的 三个列表长度必定相等  因为在  spiders 已经筛选过了
        for i,imgUrl in enumerate(houseImgUrl_list):
            #下载图片
            spidersName=item[u'spidersName']
            folderName,UUID=downLoadImg(imgUrl,imgType=1,spidersName=spidersName)
            if not folderName:#下载错误
                continue
            try:
                houseChinaType,houseIntType=houseTypeParse(houseType_list[i],communityName)
            except:
                houseChinaType,houseIntType=communityName,'0'
            try:
                houseArea=houseAreaParse(houseArea_list[i])
            except:
                houseArea='0'
            insterHouselayoutTuple=(0,nowTime(),nowTime(),UUID,houseChinaType,
                                    communityId,930864,houseIntType,houseArea,
                                    cityName,0,0,0)
            insterHouselayoutextTuple=(0,0,item[u'comNumber'],0)
            insertDict={u'houselayout':insterHouselayoutTuple,
                        u'houselayoutext':insterHouselayoutextTuple
                        }
            #insertDict 是一个字典 键 是表名称  houselayout 和 houselayoutext'
            if not houseTableSave(self.conn,insertDict):
                ###插入错误 删除
                deleteImg(folderName,UUID,spidersName)
