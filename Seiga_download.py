#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import codecs
import json
import urllib, urllib2
import cookielib
from BeautifulSoup import BeautifulSoup
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


# Constants for niconico
SEIGA_URL_FORMAT = "http://seiga.nicovideo.jp/seiga/{seiga_id}"
LOGIN_URL = "https://secure.nicovideo.jp/secure/login"
MAIL_ADDR = 'artificial.fairy@gmail.com'
PASSWORD = 'R1jBKWrMQJ1oR2Hz'
FETCH_LIMIT = 10



class SeigaConnection(object):
    u"""ニコニコ静画への認証クッキーを持ったopenerをシングルトンとして保持する。

    """
    _instance = None;

    class Singleton:
        def __init__(self):
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
            req = urllib2.Request(url = LOGIN_URL)
            reqdata = urllib.urlencode({"mail":MAIL_ADDR, "password":PASSWORD})
            req.add_data(reqdata)
            opener.open(req)
            self.opener = opener

    def __init__(self):
        if SeigaConnection._instance == None:
            SeigaConnection._instance = SeigaConnection.Singleton()

    def getConnection(self):
        return SeigaConnection._instance.opener

def tagRemove(s):
    tagRemover = re.compile(r'<.*?>')
    return tagRemover.sub('', s)

def removeSpaceEntity(s):
    pattern = re.compile('(&#160;|&ensp;|&emsp;)')
    return pattern.sub('', s)

def removeLeftTag(s):
    tagRemover = re.compile(r'^<.*?>(\t|\s|\n)+')
    return tagRemover.sub('', s)

def removeRightTag(s):
    tagRemover = re.compile(r'(\t|\s|\n)+<.*?>$')
    return tagRemover.sub('', s)

def removeTagAndSpaces(s):
    s = removeLeftTag(s)
    s = removeRightTag(s)
    return s

def extractUrl(s):
    urlExtracter = re.compile(r'href=".*?"')
    return urlExtracter.search(s)

def fetchTitle(crawler, url):
    pageHtml = crawler.open(url).read()
    pageSoup = BeautifulSoup(pageHtml)
    title = pageSoup.find("div", attrs={"class": "title_text"})
    return removeTagAndSpaces(str(title))

def fetchDesc(crawler, url):
    pageHtml = crawler.open(url).read()
    pageSoup = BeautifulSoup(pageHtml)
    title = pageSoup.find("div", attrs={"class": "illust_user_exp"})
    return removeTagAndSpaces(str(title))

def fetchTags(crawler, url):
    pageHtml = crawler.open(url).read()
    pageSoup = BeautifulSoup(pageHtml)
    tags = pageSoup.findAll("a", attrs={"class": "tag"})
    _tags = []
    for tag in tags:
        _tag = tagRemove(str(tag))
        _tags.append(_tag)
    return _tags

def fetchFullsizeImage(crawler, seiga_id):
    url = "http://seiga.nicovideo.jp/image/source?id=" + seiga_id
    img = crawler.open(url)
    return img.read()

def detect_imagetype(image):
     if image[6:10]=='JFIF': return 'image/jpeg'
     if image[0:3]=='GIF': return 'image/gif'
     if image[1:4]=='PNG': return 'image/png'

def findCategoryTag(crawler, url):
    pageHtml = crawler.open(url).read()
    pageSoup = BeautifulSoup(pageHtml)
    tags = pageSoup.find('img', attrs={'src': '/img/tag/category.png'})
    if tags is not None:
        return tags.next.string
    else:
        return "カテゴリ設定なし"


def main():
    #コマンドライン引数に、検索したいタグを入力
    argvs = sys.argv
    targetTag = sys.argv[1]
    #niconicoへの接続を開始
    crawler = SeigaConnection().getConnection()
    #検索条件を組み立て
    req = urllib2.Request(url = "http://seiga.nicovideo.jp/search/" + targetTag)
    reqdata = urllib.urlencode({"target":'illust', "sort":'clip_count'})
    req.add_data(reqdata)
    #検索条件でアクセスし、表示されたHTMLを取得
    rankingHtml = crawler.open(req).read()
    rankingSoup = BeautifulSoup(rankingHtml)
    #コンソールにメッセージ表示
    print 'Start fetching images on the conditions descripted below;'
    print rankingSoup.find('title')
    #各画像の詳細ページへのリンクを取得
    links = []
    _links = []
    links = rankingSoup.findAll("div", attrs={"class": "illust_title"})
    for link in links[0:FETCH_LIMIT]:
        link = extractUrl(str(link))
        href = link.string[link.span()[0]:link.span()[1]]
        link = "http://seiga.nicovideo.jp" + href[6:-1]
        _links.append(link)
    #各ページへのリンクが入った配列ができた
    links = _links

    for link in links:

        #各種情報を取得し、その状況を表示しておく
        print 'Title\n----------------------'
        title = fetchTitle(crawler, link)
        fileTitle = title + str(time.time())
        print title
        print '\n'
        print 'User Desc\n----------------------'
        desc = fetchDesc(crawler, link)
        print desc
        print '\n'
    
        
        print 'Downloading Image...\n----------------------'
        seiga_id = link[34:-27]
        img = fetchFullsizeImage(crawler, seiga_id)
        print 'done!'
        print '\n'

        #バイナリから画像タイプ判別
        file_ext = detect_imagetype(img)
        print 'Filetype\n----------------------'
        print file_ext
        print '\n'

        if file_ext == 'image/jpeg':
            file_ext = '.jpg'
        elif file_ext == 'image/gif':
            file_ext = '.gif'
        elif file_ext == 'image/png':
            file_ext = '.png'
        else:
            file_ext = '.unknown'

        #書き出す先のフォルダがあるかどうか確認し、なければ作成
        if os.path.exists("./seiga_download_tmp") == False:
            os.mkdir('./seiga_download_tmp')

        #画像ファイル書き出し
        localfile = open( './seiga_download_tmp/' + fileTitle + file_ext, 'wb')
        localfile.write(img)
        localfile.close()

        #タグを取得
        tags = fetchTags(crawler, link)

        #カテゴリタグを探す
        categoryTag = findCategoryTag(crawler, link)

        #タグの中にカテゴリタグがあれば削除
        if categoryTag in tags:
            tags.remove(categoryTag)

        #いちばん先頭のタグをカテゴリタグとして取り出す
        print 'Category Tag is...\n----------------------'
        # print categoryTag
        print '\n'

        #残ったタグを、「"タグ1", "タグ2", "タグ3"」 という文字列にする
        tags_string = ""
        for tag in tags:
            tags_string = tags_string + "\"" + tag + "\","
        tags_string = tags_string[:-1]
        print 'Tags\n----------------------'
        print tags_string
        print '\n'

        #jsonファイル書き出し
        _json = {
            "title": title,
            "tags": tags_string,
            "description": desc,
            "category": categoryTag,
            "filename": fileTitle + file_ext
        }

        f = codecs.open('./seiga_download_tmp/' + fileTitle + '.json', 'w', 'utf-8')
        json.dump(_json, f, ensure_ascii=False)
        f.close()



 
if __name__ == '__main__':
    main()