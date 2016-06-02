#coding=utf-8
import os
import requests
import json
import re

from publicConfig import kaipanTimeThreshold
from publicConfig import dataBaseConfig
from publicConfig import saveHouseImgPath
from publicConfig import kaipanTimeParseTuple
from publicConfig import houseTypeDict
from publicConfig import houseAreaParseTuple
from datetime import datetime
from imageStreamParse import sava_picture
import uuid
import MySQLdb



def existNewCommunityTable(cur,tableName):
    cur.execute("show tables")
    if tableName in map(lambda x:x[0],cur.fetchall()):
        return True
    return False


#链接数据库
def connectDataBase(userConnectName=''):
    try:
        conn=MySQLdb.connect(**dataBaseConfig)
        print u'\n---------------------- %s ConnectDataBase Succeed ----------------------\n'%userConnectName
        return conn
    except:
        raise Exception(u'\n----------- 连接数据库失败，请检查 publicConfig.py 配置 -----------\n')

#初始化数据库的ID  传入 需要初始化的 tablename 和需要初始化的ID
def initTableId(conn,initTableName,initId):
    cur=conn.cursor()
    try:
        cur.execute('ALTER TABLE %s AUTO_INCREMENT=%s'%(initTableName,initId))
        conn.commit()
        print u'\n------------------- Init  %s Succeed  initId : %s ------------------\n'%(initTableName,initId)
        return True
    except:
        print u'\n------------------- Init  %s Failure  initId : %s ------------------\n'%(initTableName,initId)
        return False
    finally:
        cur.close()


#返回当前时间
def nowTime():
    return datetime.now()

#会根据保存路径和爬虫名称创建一个文件夹
def createSaveHouseImgPath(spidersName,**kwargs):
    createPath=os.path.join(saveHouseImgPath,spidersName)
    try:
        if not os.path.exists(createPath):
            os.makedirs(createPath)
        print u'\n-------------------- %s SaveHouseImgPath : %s  ---------------------\n'\
              %(spidersName,createPath,)
        return True
    except:
        print u'\n-------------------- %s createSaveHouseImgPath Failure  ------------------\n'%spidersName
        return False


##获取地理坐标
def acquireGeographyCoordinates(communityName,communityArea,communityCity,communityAddress,
                                coordinatesLevel=2,
                                coordinatesAleve=0,
                                **kwargs):
    ##根据以上信息获取这个楼盘的 地理坐标  即经纬度
    # 使用阿里云api 参考  http://gc.ditu.aliyun.com/jsdoc/geocode_api.html
    # 返回结果：
    # {
    #     cityName:" ",
    #     address:"北京,海淀",
    #     level:5,
    #     alevel:2,
    #     lat:39.97652,
    #     lon:116.33690
    # }
    # 查看示例
    # Json参数说明：
    # cityName 城市名称
    # adress 地址
    # level 匹配级别（0 中国，1 省，2 地级市，3 县，4 乡镇，5街道，6 小区，7 具体的POI，8 门牌号级别，-1 查询失败）
    # aleve 精确度 （1 完全正确，2 比较正确 ，3 可能正确）
    # lat 纬度
    # lon 经度
    Address_1=''.join((communityCity,communityArea,communityName))
    Address_2=communityAddress
    Address_1=Address_1.replace(u'，',u'').replace(u'。',u'').replace(u'-',u'')
    Address_2=Address_2.replace(u'，',u'').replace(u'。',u'').replace(u'-',u'')

    for Address  in (Address_2,Address_1):
        coordinatesJson=requests.get(u'http://gc.ditu.aliyun.com/geocoding',params={u'a':Address})
        try:
            coordinatesJson=json.loads(coordinatesJson.text)
            # 在精确度的阈值之上  这里的 aleve要反一下
            #coordinatesJson[u'level']<0 失败
            if coordinatesJson['level']>=coordinatesLevel and (4-coordinatesJson[u'alevel'])>=coordinatesAleve:
                # return {u'lat':coordinatesJson[u'lat'],
                #         u'lon':coordinatesJson[u'lon']}
                return (coordinatesJson[u'lat'],coordinatesJson[u'lon'])  #返回纬度经度的格式
        except:
            pass
    return (None,None) #返回纬度经度的格式
    #{u'lat':None,u'lon':None} #两次都是失败的就为空

####判断是否是新楼盘 是 True  否则 None
def judgeNewCommunity(cur,communityName,communityArea,communityCity,**kwargs):
    try:
        # communityAreaReList=re.findall(u"(.*?)[区市县镇]{1}",communityArea)
        # if communityAreaReList:
        #     print communityAreaReList
        #     communityArea=communityAreaReList.pop()
        # communityArea,communityCity=map(lambda x:normCityAreaName(x),(communityArea,communityCity))

        sql=u'SELECT * FROM location_community,location_area WHERE location_community.area_id=location_area.id AND location_community.name="%s" AND location_area.name LIKE "%s%%"'
        cur.execute(sql%(communityName,communityArea))
        if not cur.fetchone():  ## 是 新楼盘  然后 查询区域的ID
            sql=u'SELECT location_area.id,location_area.name FROM location_area,location_city WHERE  location_area.city_id=location_city.id AND location_area.name LIKE "%s%%" AND location_city.name = "%s"'
            cur.execute(sql%(communityArea,communityCity))
            communityAreaData=cur.fetchone()
            if communityAreaData:
                try:  #  这里加 错误捕捉 是因为 打印会有 编码错误
                    print u"\n--------------   new community  : %s  Url : %s --------------\n"%\
                          (communityName,kwargs.get('communityHomeUrl'))
                except:
                    print u"\n--------------   new community  Url : %s ------------------\n"%\
                          (kwargs.get('communityHomeUrl'),)
                ###   communityAreaId,communityArea=communityCityData
                return communityAreaData#返回区域的id和区域名称
        return None
    except Exception as e:
        print u'\n-------------- judgeNewCommunity Error : %s --------------\n'%e
        return None
    finally:
        cur.close()


###解析开盘时间  就是格式化  符合返回 parse 后的开盘时间  否则返回 False
def kaipanTimeParse(kaipanTime,**kwargs):
    ##传入开盘时间  myconfig中的 开盘时间阈值各开盘时间正则的 正则表达式元组
    # 不符合阈值返回 False 错误格式返回 None
    if isinstance(kaipanTime,(unicode,str)):#这个跟python的默认编码有关
        kaipanTimeReList=re.findall(u'20(\d{2})年底',kaipanTime) or re.findall(u'20(\d{2})底',kaipanTime)
        if kaipanTimeReList:
            return u'20%s-12-31'%kaipanTimeReList.pop()
        kaipanTimeReList=re.findall(u'20(\d{2})年初',kaipanTime) or re.findall(u'20(\d{2})初',kaipanTime)
        if kaipanTimeReList:
            return u'20%s-1-31'%kaipanTimeReList.pop()
        for reStr in kaipanTimeParseTuple:
            kaipanTimeReList=re.findall(reStr,kaipanTime)
            if len(kaipanTimeReList)==1:
                kaipanTimeReList=list(kaipanTimeReList[0])
                if len(kaipanTimeReList[0])==2: #年份只有两位
                    kaipanTimeReList[0]=u'20'+kaipanTimeReList[0] #前面加上 20 变成完整时间
                if len(kaipanTimeReList)==2:##只有年月
                    kaipanTimeReList.append(u'1') #添加 1 号
                try:
                    if (datetime(*map(lambda x:int(x),kaipanTimeReList))-datetime(*kaipanTimeThreshold)).days>=0:
                        return '-'.join(kaipanTimeReList) #例如  2016-4-22
                    else: #不用再判断了 因为时间不符合阈值
                        return False
                except:#生怕出错  那就直接 continue
                    continue
        return None
    elif not kaipanTime:
        return None
    elif isinstance(kaipanTime,(list,tuple)):
        kaipanTime=filter(lambda x:x,map(kaipanTimeParse,kaipanTime))
        if kaipanTime:
            return kaipanTime.pop()
        return None
    else:
        raise TypeError(u'-------------------- 参数只能是 str list tuple -----------------------')



#保存数据到数据库 到location_community 表中
# insertDict是元组或者列表  键是 location_community
# 插入成功就返回最新的 id 否则返回 False
def communityTableSave(conn,insertDict,tableName='location_community',**kwargs):
    insertCommunityTableSql=u"insert into "+tableName+u" (state,create_time,modify_time,name,area_id,address,longitude,latitude,houselayout_count,developer,slug,head_slug,description,pm_company,floor,bus,metro,houselayout_sizes,no,kaipan_date,ruzhu_date) value(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    cur=conn.cursor()
    try:
        cur.execute(insertCommunityTableSql,insertDict[u'location_community'])
        Id=cur.lastrowid
        conn.commit()
        print u'\n---------------- communityTableSave  succeed --------------\n'
        return Id
    except Exception as e:
        print u'\n---------------- communityTableSave  Error : %s --------------\n'%e
        conn.rollback()
        return False
    finally:
        cur.close()




#保存当另外两个表中
# insertDict 是一个字典 键 是表名称  houselayout 和 houselayoutext'
# 值是 列表或者元组
def houseTableSave(conn,insertDict,**kwargs):
    cur=conn.cursor()
    insertHouselayoutSql=u"insert into ifuwo_houselayout (state,create_time,modify_time,no,name,community_id,user_id,house_type,area,city_name,design_count,standard,data_ready) value(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    insertHouselayoutextSql=u"INSERT INTO ifuwoext_houselayoutext (state, houselayout_id, source, basemap_status) VALUE(%s,%s,%s,%s)"
    try:
        cur.execute(insertHouselayoutSql,insertDict[u'houselayout'])
        if not isinstance(insertDict[u'houselayoutext'],list):###不能是元组  不然会出错
            insertDict[u'houselayoutext']=list(insertDict[u'houselayoutext'])
        insertDict[u'houselayoutext'][1]=cur.lastrowid
        cur.execute(insertHouselayoutextSql,insertDict[u'houselayoutext'])
        conn.commit()
        return True
    except Exception as e:
        print u'\n---------------- houseTableSave  Error : %s --------------\n'%e
        conn.rollback()
        return False
    finally:
        cur.close()


# 将 户型转换成  houseTypeDict 中的类型格式
def houseTypeParse(houseData,communityName=None,**kwargs):
    ##传入  楼盘名的意思是  没有户型类型  就用楼盘名代替
    if isinstance(houseData,(unicode,str)):  # 这里的有些不同 python3用 str  而 python2 用unicode
        if u'复式' in houseData:
            return (u'复式',u'9')
        elif u'LOFT' in houseData.upper():
            return (u'LOFT',u'8')
        else:
            #这里替换有些不准却
            # houseData=houseData.replace(u'\n',u'').replace(u'\r',u'').replace(u'\t',u'').replace(u' ',u'')
            houseData=houseData.strip()
            houseData=houseData.replace(u'一',u'1')
            houseData=houseData.replace(u'二',u'2').replace(u'两',u'2')
            houseData=houseData.replace(u'三',u'3')
            houseData=houseData.replace(u'四',u'4')
            houseData=houseData.replace(u'五',u'5')
            houseReList=re.findall(u'([1-5]{1})室([1-2]{1})厅',houseData)
            if not houseReList:
                return (houseData+communityName,u'0')
            roomNum,hallNum=map(lambda x:int(x),houseReList.pop())  #室 和 厅
            if roomNum<hallNum:# or roomNum>5 or hallNum>2:#超过 5 室 2 厅 或者室的数量大于厅的
                return (houseData+communityName,u'0')
            house=u'%s室%s厅'%(roomNum,hallNum)
            try:
                houseType=houseTypeDict[house]
                return (house,houseType)
            except:
                return (houseData+communityName,u'0')

    elif isinstance(houseData,(list,tuple)):
        return map(lambda x:houseTypeParse(x),houseData)
    else:
        raise TypeError(u"houseData 参数只接受 str list tuple ")


#面积转换诚标准的
def houseAreaParse(houseAreaData,**kwargs):
    if isinstance(houseAreaData,(unicode,str)):
        houseAreaData=houseAreaData.strip()
        for reStr in houseAreaParseTuple:
            houseAreaDataReList=re.findall(reStr,houseAreaData)
            if houseAreaDataReList:
                if int(houseAreaDataReList[0])<300:
                    return houseAreaDataReList.pop()
        return '0'
    elif houseAreaData in ('0',None,0):
        return '0'
    elif isinstance(houseAreaData,(list,tuple)):
        return map(lambda  x:houseAreaParse(x),houseAreaData)
    else:
        raise TypeError(u'参数 houseAreaData 类型只能是 str list tuple')


#下载户型图或者封面图
def downLoadImg(imgUrl,imgType,spidersName): #imgType=1表示下载户型图  0 表示 封面
    UUID=str(uuid.uuid1()).replace('-','')
    folderName=sava_picture(imgUrl,imgType,UUID,spidersName)
    return (folderName,UUID)
    ##下载成就是  返回  文件夹名和UUID
    # 失败就是返回  False UUID
    # 这里要返回 文件夹名和UUID就是为了插入数据库出错 然后可以删除文件 或者文件夹

##判断这个城市是否在本地数据库中
def judgeCityName(cur,cityName,**kwargs):
    if not cityName:
        return False
    sql=u"SELECT id FROM location_city WHERE name LIKE '%s%%'"
    try:
        cur.execute(sql%(cityName,))
        if cur.fetchone():
            return True
        print u'************************ 没有 %s 这个城市 ********************'%cityName
        return False
    except:
        return False
    finally:
        cur.close()

# 判断这个区域是否在本地数据库中
def judgeAreaName(cur,areaName,**kwargs):
    if not areaName:
        return False
    sql=u"SELECT id FROM location_area WHERE name LIKE '%s%%'"
    try:
        cur.execute(sql%(areaName,))
        if cur.fetchone():
            return True
        print u'************************ 没有 %s 这个区域 ********************'%areaName
        return False
    except:
        return False
    finally:
        cur.close()

def my_extract_first(lxml_list,default=None):  # 主要在 xingkong spider 使用
    for x in lxml_list:
        return x
    return default

def normCityAreaName(City_or_Area,**kwargs):## 规范 选城市 和 区域 名
    if isinstance(City_or_Area,(unicode,str)):
        City_or_Area=City_or_Area.strip()
        for RE in [u'市',u'区',u'镇',u'乡']:
            City_or_Area=City_or_Area.replace(RE,'')
        return City_or_Area
            # raise ValueError(u'------------------ normCityAreaName arg : type  ValueError -----------------')
    elif isinstance(City_or_Area,(list,tuple)):
        return map(lambda x:normCityAreaName(x),City_or_Area)
    else:
        raise TypeError(u'------------------ normCityAreaName arg : City_or_Area  TypeError -----------------')





