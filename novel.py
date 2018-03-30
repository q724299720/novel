#-*-coding:utf-8 -*-
import requests
from lxml import etree
import mysql_c
import re
import os

def get_text(url):
    r=requests.get(url)
    r.encoding="gbk"
    return r.text

#获取到一个字典，字典中key是章节的url，value是章节的title，然后通过url获取content并导入数据库
def insert_chapter_mysql(chapter):
    for chapter_url in chapter:
        title = chapter[chapter_url]
        html = get_text(chapter_url)
        chapter_content_list = etree.HTML(html).xpath("//*[@id='content']/text()")
        chapter_content = ''
        for text in chapter_content_list:
            chapter_content += text + "<br/>"
        #print(title)
        # print(url)
        # print(chapter_content)
        chapter_content = re.sub('[%s\']*|(\xa0)', '', chapter_content)
        mysql_c.insert_chapter(name, title, chapter_url, chapter_content)

def get_chapter(name,url):
    r=requests.get(url)
    r.encoding="gbk"
    chapter_title=etree.HTML(r.text).xpath("//dd/a/text()")
    chapter_url=etree.HTML(r.text).xpath("//dd/a/@href")
    chapter={}
    for i in range(0,len(chapter_title)):
        url="https://www.zwdu.com"+chapter_url[i]
        chapter[url]=chapter_title[i]
        # print(chapter[chapter_title[i]])
    #上面以及获取到了本书目前全部的章节标题和url
    # 获取数据库中的url
    mysql_chapter_url=mysql_c.get_all_chapter_name(name)
    if mysql_chapter_url=='none':
        insert_chapter_mysql(chapter)
    else:
        for i in mysql_chapter_url:
            mysql_url=(i[0])
            try:
                if chapter[mysql_url]:
                   chapter.pop(mysql_url)
            except:
                pass
        try:
            if len(chapter)>0:
                mysql_c.update_chapter_new(name)
        except:
            pass
		 # try:
			# if len(chapter)>0:
			# 	mysql_c.update_chapter_new(name)
		 # except:
			# pass
        insert_chapter_mysql(chapter)
    #
    # print(mysql_chapter_url)
    # print(type(mysql_chapter_url))
    # mysql_title_total=[]
    # print(type(mysql_title_total))
    # mysql_title_total=list(mysql_chapter_url)
    # # for i in  mysql_chapter_name:
    # #     print(type(i))
    # #     mysql_title_total.append(i)
    # print(type(mysql_title_total))
    # print(mysql_title_total)
    # for j in mysql_title_total:
    #     print(type(j))

def chapter_img_down(name,url):
    try:
        content = requests.get(url).content
        if not os.path.exists("/www/wwwroot/qxm.life/novel/img"):
            os.mkdir("/www/wwwroot/qxm.life/novel/img")
        with open("/www/wwwroot/qxm.life/novel/img/%s.jpg" % (name), "wb") as f:
            f.write(content)
    except Exception as e:
        print(e)


def get_book_img_url(name,url):
    print("开始匹配")
    source_html = requests.get(url).text
    html_content = etree.HTML(source_html)
    check_url = html_content.xpath("//h3/a/@href")
    length = len(check_url)
    print('查询到匹配结果%d条'%(length))
    if length == 0:
        print('查无此书，删除本书')
        mysql_c.del_book_name(name)
    elif length == 1:
        print("有一个匹配结果")
        check_url = html_content.xpath("//div[@class='result-game-item-pic']/a/@href")
        mysql_c.update_book_url(name, check_url[0])
        get_chapter(name, check_url[0])
        chapter_img = etree.HTML(requests.get(check_url).text).xpath("//*[@id='fmimg']/img/@src")
        chapter_img_down(name, chapter_img[0])
        #print('图片下载成功')
    elif length < 10:
        print('匹配数量大于1小于10')
        for c_url in check_url:
            #print("in %s" % (c_url))
            r = requests.get(c_url)
            r.encoding = "gbk"
            find_name = etree.HTML(r.text).xpath("//*[@id='info']/h1/text()")
            #print(find_name)
            if find_name[0] == name:
                chapter_img = etree.HTML(requests.get(c_url).text).xpath("//*[@id='fmimg']/img/@src")
                chapter_img_down(name, chapter_img[0])
                mysql_c.update_book_url(name, c_url)
                get_chapter(name, c_url)
                break

    elif length==10:
        not_find=True
        print('匹配到10个')
        for c_url in check_url:
            print("in %s" % (c_url))
            r = requests.get(c_url)
            r.encoding = "gbk"
            find_name = etree.HTML(r.text).xpath("//*[@id='info']/h1/text()")
            if find_name[0] == name:
                no_find = False
                chapter_img = etree.HTML(requests.get(c_url).text).xpath("//*[@id='fmimg']/img/@src")
                chapter_img_down(name, chapter_img[0])
                mysql_c.update_book_url(name, c_url)
                get_chapter(name, c_url)
                break
        if not_find:
            page_number = re.search('page=(\d+)', url)
            if page_number:
                new_number=int(page_number[1])+1
                url=url[0:-1]+str(new_number)
                get_book_img_url(name, url)
            else:
                url=url+'&page=2'
                get_book_img_url(name, url)




if __name__ =='__main__':
    books=mysql_c.get_books_name()
    if books:
        for name in books:
            print("存在 %s " %(name))

            if not books[name]:
                print("%s 没有关联" % (name))
                url="https://www.zwdu.com/search.php?keyword=%s" %(name)
                try:
                    get_book_img_url(name, url)
                except:
                    pass

            else:
               print('存在网址，进入抓取')
               print(name)
               print(books[name])
               get_chapter(name, books[name])
    else:
        pass
