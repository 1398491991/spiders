#coding=utf-8
import requests
import os
import shutil
from PIL import Image
from PIL import ImageFile
from publicConfig import saveHouseImgPath
ImageFile.LOAD_TRUNCATED_IMAGES = True
from cStringIO import StringIO as BytesIO
import random
from spidersSet.settings import USER_AGENTS
def myGetHtml(url,return_type='text',timeout=30):
    if not url:
        return False
    try:
        html=requests.get(url,timeout=timeout,headers={'User-Agent':random.choice(USER_AGENTS)})
        if return_type=='text':
            print u'********************* tempGetHtml_Url ：%s ***************************'%url
            return html.text
        elif return_type=='byte':
            return html.content  ##返回字节
        else:
            raise TypeError(u'----------------  return_type is  text or byte ------------------- ')
    except:
        return False

##检查户型图或者封面图的Url是否符合规范
def judgeImgUrl(imgUrl):
    if os.path.splitext(imgUrl)[1].upper() in [u'.JPG',u'.JPEG',u'.PNG']:
        return imgUrl
    return False

#下载或者插入出错时候删除文件夹以及图片文件   只要出发这个  一率返回  False

def deleteImg(folderName,imgUuid,spiderName):
    path=os.path.join(saveHouseImgPath,spiderName,folderName)
    try:
        if len(os.listdir(path))>=2:
            shutil.rmtree(os.path.join(path,imgUuid))
        else:
            shutil.rmtree(path)
    except Exception as e:
        print u'\n----------  删除图片过程出错 : folderName = %s ' \
			  u' UUID = %s  Error = %s  ------------\n'%(folderName,imgUuid,e)
    finally:
        return False


def imgParse(img_bytes,parse_save_path,size,im_ext='JPEG',quality=95):
    im=Image.open(BytesIO(img_bytes))
    if im.mode!='RGB':
        im=im.convert('RGB')
    x1,y1=im.size
    x2,y2=size
    scale_x=float(x2)/x1
    scale_y=float(y2)/y1
    newsize=(x2,int(y1*scale_x)) if scale_x<scale_y else(int(x1*scale_y),y2)
    resize=im.resize(newsize,Image.ANTIALIAS)
    resize.save(parse_save_path, im_ext, quality=quality)
    del im,size

def filename2sid(file_name):
    valid_name = ''.join(a for a in file_name if ((a.isdigit()) or (a.isalpha())))
    if len(valid_name) < 4:
        valid_name = '0001'
    return str(int(valid_name[0:4], 16))

#^^^^^^^^^^^^Url图片地址，name1图片名字，ml(1表示 户型图  0 表示封面),a代表uuid
def sava_picture(Url,ml,a,spiderName):
    if not judgeImgUrl(Url):  # 判断图片是否符合 png jpg 等格式
        return False
    if ml==1:
        name1=u'basemap.jpg'
    else:
        name1=u'cover.jpg'
    ad=os.path.join(saveHouseImgPath,spiderName)
    folder_name =filename2sid(a)
    addrs=os.path.join(ad,folder_name,a)##存放路径
    if not os.path.exists(addrs):
        os.makedirs(addrs)
    try:
        # img_bytes=urllib2.urlopen(Url,timeout=40).read()
        img_bytes=myGetHtml(Url,return_type='byte',timeout=40)
        if not img_bytes:
            return False
        filename=open(os.path.join(addrs,name1),'wb')
        filename.write(img_bytes)
        filename.close()
        if ml==1:
            thumbnail_path=os.path.join(addrs,u'thumbnail.jpg')
            print u'\nimgType : 户型图   imgSavePath : %s   imgUrl : %s' \
                    u'\n'%(thumbnail_path,Url)
            imgParse(img_bytes,thumbnail_path,[480,480])
        else:
            cover_path=os.path.join(addrs,u'cover.jpg.small.jpg')
            print u'\nimgType : 封面图   imgSavePath : %s   imgUrl : %s' \
                    u'\n'%(cover_path,Url)
            imgParse(img_bytes,cover_path,[180,100])
        return folder_name
    except Exception as e:
        print u'\n-------------- 图片抓取错误Url : %s   Error :%s -------------\n'%(Url,e)
        return deleteImg(folder_name,a,spiderName)  #一定返回的是 False
