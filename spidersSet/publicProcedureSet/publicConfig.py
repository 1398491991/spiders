#coding=utf8
import os


#户型图的保存路径
saveHouseImgPath=os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        os.path.pardir,os.path.pardir,os.path.pardir,'houseImages'))
#链接数据库的配置信息
dataBaseConfig={
    'host':'localhost',
    'user':'root',
    'passwd':'123456789',
    # 'db':'ifuwo', ## 正式数据库
    'db':'test_database', #主要用于测试
    'port':3306,
    'charset':'utf8'
}

## 开盘时间的阈值
kaipanTimeThreshold = (2003,1,1)


ZERO_HOUSE=True #False  ### 是否需要零户型  true 需要  False 不需要



# 户型类型的字典
houseTypeDict={u"1室1厅":u"1",
                u"2室1厅":u'2',
                u"2室2厅":u'3',
                u"3室1厅":u'4',
                u"3室2厅":u'5',
                u"4室2厅":u'6',
                u"其他":u'0',
                u"5室2厅":u'7',
                u"LOFT":u'8',
                u"复式":u'9'}

##解析开盘时间的正则表达式
kaipanTimeParseTuple=(u'(\d{2,4})-(\d{1,2})-(\d{1,2})',
                        u'(\d{2,4})年(\d{1,2})月(\d{1,2})日',
                        u'(\d{2,4})\.(\d{1,2})\.(\d{1,2})',
                        u'(\d{2,4})年(\d{1,2})月(\d{1,2})',
                        u'(\d{2,4})年(\d{1,2})月',
                        u'(\d{4})\.(\d{1,2})',
                        u'(\d{4})-(\d{1,2})',
                        u'(\d{2,4})/(\d{1,2})/(\d{1,2})',)

##解析户型面积的正则表达式  这里一定不要在前面  加上  u
houseAreaParseTuple=('(\d{2,3})\.\d+[m²㎡平]{1,2}','(\d{2,3})m²','(\d{2,3})㎡','(\d{2,3})平')

#用于初始化的ID
init_location_community_id=811705+100
init_ifuwo_houselayout_id=2135683+300
init_ifuwoext_houselayoutext_id=1524947+300

# 楼盘表是否要保存到新的表
newComunityTable='location_community_copy'


#匹配级别（0 中国，1 省，2 地级市，3 县，4 乡镇，5街道，6 小区，7 具体的POI，8 门牌号级别，-1 查询失败）
# coordinatesLevel=0   不要超过这些数字  -1-----8

# aleve 精确度 （3 完全正确，2 比较正确 ，1 可能正确）
# coordinatesAleve=0   #不要超过这些数字  1---3




