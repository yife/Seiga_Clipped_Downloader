#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
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
LOGIN_URL = "https://secure.dev.nicovideo.jp/secure/login_form"
MAIL_ADDR = 'satoshi_yokohata@dwango.co.jp'
PASSWORD = 'nani4royumenouenanodesukara'




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


def main():
    uploader = SeigaConnection().getConnection()
    req = 'http://seigadev.o-in.nicovideo.jp/'
    tmpHTML = crawler.open(req).read()
    print tmpHTML
    print 'hoge'

 
if __name__ == '__main__':
    main()