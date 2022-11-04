from multiprocessing import reduction
import cv2
import numpy as np
import shutil
import fitz
from PIL import Image
import time
import re
import os
import sys

# Hash值对比
def cmpHash(hash1, hash2,shape=(10,10)):
    n = 0
    # hash长度不同则返回-1代表传参出错
    if len(hash1)!=len(hash2):
        return -1
    # 遍历判断
    for i in range(len(hash1)):
        # 相等则n计数+1，n最终为相似度
        if hash1[i] == hash2[i]:
            n = n + 1
    return n/(shape[0]*shape[1])
# 均值哈希算法
def aHash(img,shape=(10,10)):
    # 缩放为10*10
    img = cv2.resize(img, shape)
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # s为像素和初值为0，hash_str为hash值初值为''
    s = 0
    hash_str = ''
    # 遍历累加求像素和
    for i in range(shape[0]):
        for j in range(shape[1]):
            s = s + gray[i, j]
    # 求平均灰度
    avg = s / 100
    # 灰度大于平均值为1相反为0生成图片的hash值
    for i in range(shape[0]):
        for j in range(shape[1]):
            if gray[i, j] > avg:
                hash_str = hash_str + '1'
            else:
                hash_str = hash_str + '0'
    return hash_str

#1.使用正则表达式查找PDF中的图片
def pdfTOpic(path,pic_path,threshold,x1,y1,x2,y2, mode):#path:pdf的路径，pic_path:图片保存的路径
    t0 = time.perf_counter() #python 3.8已经不支持time.clock了
    res = True;
    #使用正则表达式来查找图片
    checkXO = r"/Type(?= */XObject)"
    checkIM = r"/Subtype(?= */Image)"
    #打开pdf
    doc = fitz.open(path)
    #------------------------------------#
    # page = doc[1]
    pageCount = 0
    for page in doc:
        mat = fitz.Matrix(0.3, 0.3)  # 1.5表示放大1.5倍
        rect = page.rect

        # clip = fitz.Rect(0, 0.6*rect.height,
        #                 0.8*rect.width, 0.8*rect.height)
        clip = fitz.Rect(int(x1),int(y1),int(x2),int(y2))

        # print(rect.width)
        # print(rect.height)
        pix = page.get_pixmap(matrix=mat, alpha=False, clip=clip)
        # page_name = path.replace('\\','_')+"_page{}.png".format(pageCount)
        page_name = "_page{}.png".format(pageCount)
        page_name = page_name.replace(':','')

        pix.save(os.path.join(pic_path,page_name))
        
        img = Image.open(os.path.join(pic_path,page_name))
        extrema = img.convert("L").getextrema()
        #判断纯色
        if extrema[0] == extrema[1]:
            # print("纯色图片")
            res = False
            return res
        # else:
        #     print('不是纯色')
        pageCount += 1
    #------------------------------------#
    #图片计数
    imgCount = 0
    lenXREF = doc.xref_length()

    #打印pdf的信息
    # print("文件名:{},页数:{},对象:{}".format(path,len(doc),lenXREF-1))
    # img1 = cv2.imread('base.png') 
    # hash1 = aHash(img1)
    if lenXREF > 0:
        baseImgList = []
        baseImgPath = os.getcwd() + '\\baseimgs'
        dirlist = os.listdir(baseImgPath)
        # print(dirlist.count())
        # print("dirlist.count:{}s".dirlist.count())
        if len(dirlist) == 0:
            # print(len(dirlist))
            res = False
            return res
        # print(dirlist)
        for i in dirlist:
            img1 = cv2.imread(os.path.join(baseImgPath,i)) 
            hash1 = aHash(img1)
            baseImgList.append(hash1);
            
        
    #遍历每一个对象
    for i in range(1,lenXREF):
        #定义对象字符串
        text = doc.xref_object(i)
        isXObject = re.search(checkXO,text)
        #使用正则表达式查看是否是图片
        isImage = re.search(checkIM,text)
        #如果不是对象也不是图片，则continue
        if not isXObject or not isImage:
            continue
        imgCount+=1
        #根据索引生成图像
        pix = fitz.Pixmap(doc,i)
        #根据pdf的路径生成图片的名称
        # new_name = path.replace('\\','_')+"_img{}.png".format(imgCount)
        new_name = "_img{}.png".format(imgCount)
        new_name = new_name.replace(':','')

        #如果pix.n<5，可以直接存为png
        if pix.n<5:
            pix.save(os.path.join(pic_path,new_name))
        #否则先转换CMYK
        else:
            pix0 = fitz.Pixmap(fitz.csRGB,pix)
            pix0.save(os.path.join(pic_path,new_name))
            pix0 = None
        #释放资源
        pix = None
        t1 = time.perf_counter()
        # print("运行时间:{}s".format(t1-t0))
        # print("提取了{}张图片".format(imgCount))
        img2 = cv2.imread(os.path.join(pic_path,new_name))  
        hash2 = aHash(img2)
        breakFlag = False
        for i in baseImgList:
            n = cmpHash(i, hash2)
            # print('均值哈希算法相似度：', n)
            if n > float(threshold):
                res = False
                breakFlag = True
                break;
        if breakFlag == True:
            break
        # n = cmpHash(hash1, hash2)
        # # print('均值哈希算法相似度：', n)
        # if n > float(threshold):
        #     res = False
        #     break;
    if mode == 'release':
        shutil.rmtree(pic_path)
    return res
def main(pdfPath,threshold,x1,y1,x2,y2, mode):
    #pdf路径
    path = pdfPath
    #创建保存图片的文件夹
    pic_path = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    if os.path.exists(pic_path):
        print("false")
        raise SystemExit
    else:
        os.mkdir(pic_path)
    m=pdfTOpic(path,pic_path,threshold,x1,y1,x2,y2, mode)
    if m:
        print('true')
        return 'true'
    else:
        print('false')
        return 'false'
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
