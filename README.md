# Deep_Spider

网页URL探测脚本，因觉得Burpsuite的爬虫不爽，就自己写了一个爬虫脚本。

提取JS_URL的正则部分使用的是[JSFinder](https://github.com/Threezh1/JSFinder) 

提取URL的正则部分使用的是[dirmap](https://github.com/H4ckForJob/dirmap) 

可以通过设置目标站点进行获取网站的全部URL

**注：如发现bug请联系我~ aixic@qq.com**

### 优势：

​		通过目标站点进行URL的爬取；

​		多线程效率可自定义；

​		爬取深度可自定义；

​		可爬取JS文件中的URL；

​		获取子域名。

### 解决问题：

​		从网站上收集域名；

​		发现不容易找到的目录。

### 后期扩展：

​		可进行分布式部署。通过主控发送目标URL。

## 使用技术

**Redis去重**
DB0 用来存放全部爬取过的URL，查重使用的数据库
DB1 存放当前目标的URL写入Mysql数据库后清空
DB2 存放爬取不同的域名

**Re正则匹配**

**xpath匹配**

**多线程**

## 流程图

![image-20191104112313146](https://github.com/Aixic-Love/Deep_Spider/raw/master/Image/image-20191104112313146.png)

## 用法

![image-20191104113003023](https://github.com/Aixic-Love/Deep_Spider/raw/master/Image/image-20191104113003023.png)




