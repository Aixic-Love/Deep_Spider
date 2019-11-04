#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019-10-17 15:47
# @Author  : Aixic
# @File    : Deep_Spider_多线程
# @Software: MacOS 10.15 python3.7.4
# -*- coding: utf-8 -*-
# By Aixic
# https://github.com/Aixic-Love
from urllib.parse import urlparse
import redis,argparse,MySQLdb,requests,urllib3,sys,re
from bs4 import BeautifulSoup
from lxml import etree
from concurrent.futures import ThreadPoolExecutor,as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:70.0) Gecko/20100101 Firefox/70.0"}
db = MySQLdb.connect("****", "aixic", "****", "test", charset='gbk')
r0 = redis.Redis(host='localhost', port=6379, password='****',decode_responses=True,db=0)
r1 = redis.Redis(host='localhost', port=6379, password='****',decode_responses=True,db=1)
r2 = redis.Redis(host='localhost', port=6379, password='****',decode_responses=True,db=2)

def parse_args():
    parser = argparse.ArgumentParser(epilog='\tExample: \r\npython3 ' + sys.argv[0] + " -u http://www.mi.com")
    parser.add_argument("-u", "--url", help="输入个网站",action='store_true')
    parser.add_argument("-d", "--deep", help="输入爬虫深度",action='store_true', default=1)
    parser.add_argument("-t", "--thread", help="输入使用的线程数", action='store_true', default=10)
    parser.add_argument("-c", "--clear", help="重置Redis数据库",action='store_true', default=False)
    return parser.parse_args()

def create_tables(domain):
    domain = domain.replace('.', '_')
    try:
        cursor = db.cursor()
        sql = """CREATE TABLE `test`.`%s`  (
        `id` bigint(20)  NOT NULL,
  `url` varchar(255) NOT NULL,
  `title` varchar(255) NULL,
  PRIMARY KEY (`url`)
) CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;""" % domain
        cursor.execute(sql)
    except MySQLdb._exceptions.OperationalError:
        pass

def create_url_list(domain):
    domain = domain.replace('.', '_')
    try:
        cursor = db.cursor()
        sql = """CREATE TABLE `test`.`%s_list`  (
        `id` bigint(20)  NOT NULL,
          `domain` varchar(255) not NULL,
          `title` varchar(255) NULL,
          PRIMARY KEY (`domain`)
        ) CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;"""%domain
        cursor.execute(sql)
    except MySQLdb._exceptions.OperationalError:
        pass

def write_url(domain):
    domain = domain.replace('.', '_')
    url_id=1
    cursor = db.cursor()
    for i in r1.keys():
        try:
            r1_temp = r1.get(i).replace('"', '_')
            r1_temp = r1_temp.replace("'", '_')
            r1_temp = r1_temp.replace('.', '_')
            r1_temp = r1_temp.replace('®', '_')
            sql = """insert into `%s` VALUES ("%s","%s","%s")""" % (domain, url_id, i,r1_temp.strip())
            cursor.execute(sql)
            db.commit()
        except UnicodeEncodeError:
            try:
                print(i, "编码有问题的url",sql)
                sql = """insert into `%s` VALUES ("%s","%s","编码有问题")""" % (domain, url_id, i)
                cursor.execute(sql)
                db.commit()

            except Exception as a:
                continue
        except MySQLdb._exceptions.IntegrityError:
            pass
        except Exception as a:
            print(r1.get(i))
            print(a)
        finally:
            url_id += 1

def write_domain(domain):
    domain = domain.replace('.', '_')
    domain_id=1
    cursor = db.cursor()
    for i in r2.keys():
        try:
            r2_temp = r2.get(i).replace('"', '_')
            r2_temp = r2_temp.replace("'", '_')
            r2_temp = r2_temp.replace('.', '_')
            r2_temp = r2_temp.replace('®', '_')
            sql = """insert into `%s_list` VALUES ("%s","%s","%s" )""" % (domain,domain_id, i, r2_temp.strip())
            cursor.execute(sql)
            db.commit()
        except UnicodeEncodeError:
            try:
                print(i, "编码有问题的url",sql)
                sql = """insert into `%s_list` VALUES ("%s","%s","编码有问题" )""" % (domain,domain_id, i)
                cursor.execute(sql)
                db.commit()
            except Exception as a:
                continue
        except MySQLdb._exceptions.IntegrityError:
            pass
        except Exception as a:
            print(a)
        finally:
            domain_id += 1

def extract_URL(url,JS):
    pattern_raw = r"""
	  (?:"|')                               # Start newline delimiter
	  (
	    ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
	    [^"'/]{1,}\.                        # Match a domainname (any character + dot)
	    [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
	    |
	    ((?:/|\.\./|\./)                    # Start with /,../,./
	    [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
	    [^"'><,;|()]{1,})                   # Rest of the characters can't be
	    |
	    ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
	    [a-zA-Z0-9_\-/]{1,}                 # Resource name
	    \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
	    (?:[\?|/][^"|']{0,}|))              # ? mark with parameters
	    |
	    ([a-zA-Z0-9_\-]{1,}                 # filename
	    \.(?:php|asp|aspx|jsp|json|
	         action|html|js|txt|xml|htm)             # . + extension
	    (?:\?[^"|']{0,}|))                  # ? mark with parameters
	  )
	  (?:"|')                               # End newline delimiter
	"""
    pattern = re.compile(pattern_raw, re.VERBOSE)
    result = re.finditer(pattern, str(JS))
    js_url = []
    for match in result:
        if match.group() not in js_url:
            target_url_list.append(url_check(url, match.group().strip('"').strip("'")))

def get_domain(domain_url):
    if '://' not in domain_url:  # 拼接URL
        domain_url = 'https://%s/' % domain_url if ':443' in domain_url else 'http://%s/' %domain_url
    flag=domain_url[8:].find("/")
    a = domain_url.split("/")
    c = domain_url[8:].find(a[-2])
    if flag == -1:
        domain_url=domain_url+"/"
        flag = domain_url[8:].find("/")
    if '://' in domain_url:  # 用来制作字典。
        domain_url = domain_url[0:8+flag][8:] if "https://" in domain_url[0:8+flag] else domain_url[0:8+flag][7:] # 记录当前目标
    return domain_url  # 记录主域名

def get_url_list(url):  # 拼接残缺的URL
    if '://' not in url:  # 拼接URL
        url = 'https://%s/' % url if ':443' in url else 'http://%s/' %url
    a = url.split("/")
    c = url[8:].find(a[-2])
    return url[:8 + c + len(a[-2])] + "/"

def url_check(url,re_URL):
    black_url = ["javascript:"]  # Add some keyword for filter url.
    URL_raw = urlparse(url)
    ab_URL = URL_raw.netloc
    host_URL = URL_raw.scheme
    if re_URL[0:2] == "//":
        result = host_URL + ":" + re_URL
    elif re_URL[0:4] == "http":
        result = re_URL
    elif re_URL[0:2] != "//" and re_URL not in black_url:
        if re_URL[0:1] == "/":
            result = host_URL + "://" + ab_URL + re_URL
        else:
            if re_URL[0:1] == ".":
                if re_URL[0:2] == "..":
                    result = host_URL + "://" + ab_URL + re_URL[2:]
                else:
                    result = host_URL + "://" + ab_URL + re_URL[1:]
            else:
                result = host_URL + "://" + ab_URL + "/" + re_URL
    else:
        result = url
    return result

def get_url_all(url):
    global domain_url_list
    print(url)
    blacklist = [".jpg", ".css", ".png", ".ico","javascript:",".apk",".exe",".gif",".dtd"]  # 如果包含这些后缀不进行
    if ".js" in url:
        try:
            raw=requests.get(url=url, headers=header, timeout=5, verify=False)
        except Exception as a:
            print(a)
            pass
        extract_URL(url,raw.content)
        return 0
    for i in blacklist:
        if i in url:
            r0.set(url, "文件请打开查看")
            r1.set(url, "文件请打开查看")
            return 0
    if not r0.exists(url):

        #exit()
        try:
            response = requests.get(url=url, headers=header, timeout=5, verify=False)

        except requests.exceptions.ConnectTimeout:
            print(url,"ConnectTimeout")
            return 0
        except requests.exceptions.ConnectionError:
            print(url, "ConnectionError")
            return 0
        except requests.exceptions.ReadTimeout:
            print(url, "ReadTimeout")
            return 0
        except requests.exceptions.InvalidURL:
            print(url, "InvalidURL")
            return 0
        response.encoding = "gb2312"
        try:
            contentDecode = response.content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                contentDecode = response.content.decode('gbk')
            except:
                print(url)
                print("[x] Unrecognized page coding errors")
                return 0
        soup = BeautifulSoup(contentDecode, 'lxml')
        try:
            r0.set(url,soup.select('title')[0].text)
            r1.set(url, soup.select('title')[0].text)
            print(url, soup.select('title')[0].text)
            flag=True
            return href(url,contentDecode)
        except IndexError:
            flag=False
            r0.set(url, "未获取到title")
            r1.set(url, "未获取到title")
            return href(url,contentDecode)
        finally:
            if flag:
                temp=get_domain(url)
                if not r2.exists(temp):
                   r2.set(temp,soup.select('title')[0].text)
            else:
                temp = get_domain(url)
                if not r2.exists(temp):
                    r2.set(temp, "未获取到title")
    else:
        return False

def href(url,response_text):
    global Deep
    if response_text:
        soup = BeautifulSoup(response_text, "lxml")
        try:
            html = etree.HTML(response_text)
            # 加载自定义xpath用于解析html
            urls_temp = html.xpath("//*/@href | //*/@src | //form/@action")
            if urls_temp==[] :return None
            else:
                for i in urls_temp:
                    target_url_list.append(url_check(url,i))
                return None
        except:
            pass

class MyThreadPool():
    def __init__(self, my_func,my_list,thread_num):
        self.my_func = my_func
        self.thread_num = thread_num
        self.my_list = my_list

    def start(self):
        with ThreadPoolExecutor(max_workers=self.thread_num) as executor:
            for target in self.my_list:
                all_task = executor.submit(self.my_func, (target))

if __name__ == "__main__":
    if len(sys.argv) == 1:
       sys.argv.append("-h")
    args = parse_args()
    target_url_list=[]
    list_temp_all={}
    thread_num=args.thread
    Deep=args.deep
    if args.clear:
        r1.flushall()
        print("重置Redis数据库成功")
        exit()
    elif args.url:
        target_url_list.append(args.url)
        create_tables(urlparse(args.url).netloc)
        create_url_list(urlparse(args.url).netloc)
        try:
            for i in range(Deep):
                target_url_list_temp=target_url_list
                target_url_list = []
                print(target_url_list_temp)
                myThreadPool = MyThreadPool(get_url_all,target_url_list_temp,thread_num)
                myThreadPool.start()
        except Exception as a:
            print(a)
        write_url(urlparse(args.url).netloc)
        write_domain(urlparse(args.url).netloc)
        r1.flushdb()
        r2.flushdb()
        db.close()
    else:
        print("等等再试试万一就好了呢")


