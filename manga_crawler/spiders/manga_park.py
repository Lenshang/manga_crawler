from datetime import datetime
import json
from logging import debug
import time
from dateutil.rrule import YEARLY
import os
import requests
import re
import scrapy
import random as rd
import ua_generator
from scrapy import item
from manga_crawler.model.manga_park import MangaInfo,ChapterInfo,ImageInfo
from manga_crawler.utils.ex_scrapy_obj import ExScrapyObj
from scrapy.http import Request
from scrapy.http.response.html import HtmlResponse
from ExObject.DateTime import DateTime
from ExObject.ExObject import ExObject
from ExObject.TimeSpan import TimeSpan
from urllib import parse
# 需求 https://w60vfd7bfh.feishu.cn/docx/LlFudfg0lovsjxxhOSUcT86bnHc
class MangaPark(scrapy.Spider):
    name = 'mangapark'
    allowed_domains = ['mangapark.net']
    DEBUG=False
    _raw={}
    with open("./proxy.json","r") as f:
        rawstr="".join(f.readlines())
        _raw=json.loads(rawstr)
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'REACTOR_THREADPOOL_MAXSIZE': 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "CONCURRENT_REQUESTS_PER_IP": 1,
        "DOWNLOAD_DELAY": 3,
        'DOWNLOAD_TIMEOUT':0,
        "DEPTH_PRIORITY": 0,
        "RETRY_TIMES": 200,
        "COOKIES_ENABLED": False,
        "HTTPERROR_ALLOWED_CODES": [403,500,503],
        "MEDIA_ALLOW_REDIRECTS":True,
        "RETRY_HTTP_CODES":[],
        "FILES_STORE":_raw["save_path"],
        "ITEM_PIPELINES": {
            'manga_crawler.pipelines.ImagePipeline.ImagePipeline': 100,
            'manga_crawler.pipelines.LocalFilePipeline.LocalFilePipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES' : {
            'manga_crawler.middleware.retry.RetryMiddleware': 300,
            # 'pphero.middleware.http2.Http2Middleware': 400,
            # 'pphero.middleware.http2.TLSMiddleware': 400,
        }
    }
    headers = {
        "accept": "*/*",
        "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
        "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-csrf-protection": "1",
        "Referer": "https://mangapark.net/",
        "Referrer-Policy": "origin-when-cross-origin",
        "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.p=0
        self.proxy_names=[]
        self.last_change_proxy=DateTime(1999,1,1)
        self.base_path="./_temp"

        # 创建代理
        # url="http://192.168.31.153:9090/proxies/GLOBAL"
        self.base_url=self._raw["api"]
        self.secret=self._raw["secret"]
        self.proxy=self._raw["proxy"]
        url=parse.urljoin(self.base_url,"/proxies")
        r=requests.get(url, headers={
            'content-type': 'application/json',
            "Authorization":"Bearer "+self.secret
            })
        raw=json.loads(r.text)
        for item in raw["proxies"]["GLOBAL"]["all"]:
            if re.fullmatch(".*?[0-2][0-9]$",item):
                self.proxy_names.append(item)
    def start_requests(self):
        self.logger.info("启动")
        url=f"https://mangapark.net/search?genres=full_color&sortby=field_name&page=1"
        #headers=self.headers.copy()
        headers=self.get_header()
        headers["cookie"]=self.get_cookie()
        yield Request(url, callback=self.parse_manga_list,headers=headers,dont_filter=True,meta={
            "page":1,
        })

    def parse_manga_list(self,response):
        selector=ExScrapyObj(response)
        for item in selector.xpath('//*[@id="app-wrapper"]/main/div[5]/div'):
            db_manga=MangaInfo()
            db_manga["manga_url"]=item.xpath(".//h3/a/@href").extract().FirstOrDefaultString().strip()
            if not db_manga["manga_url"]:
                continue
            db_manga["name"]=item.xpath(".//h3/a/span/text()").extract().FirstOrDefaultString()
            db_manga["other_name"]=" / ".join(item.xpath("./div[2]/div[1]/text()").extract().ToOriginal())
            db_manga["other_name"]=" / ".join(item.xpath("./div[2]/div[1]/text()").extract().AllStringArray())
            db_manga["author"]=item.xpath("./div[2]/div[2]/text()").extract().FirstOrDefaultString()

            db_manga["manga_url"]=parse.urljoin("https://mangapark.net/",db_manga["manga_url"])

            # headers=self.headers.copy()
            headers=self.get_header()
            headers["cookie"]=self.get_cookie()
            yield Request(db_manga["manga_url"], callback=self.parse_manga_chapter,headers=headers,dont_filter=True,meta={
                "db_manga":db_manga,
            })

    def parse_manga_chapter(self,response):
        db_manga=response.meta["db_manga"]
        selector=ExScrapyObj(response)
        # 处理漫画基本信息
        db_manga["long_description"]="\r\n".join(selector.xpath('//*[@id="app-wrapper"]/main/div[1]/div[2]/div[4]/div/div[1]/div[1]/react-island/div//text()').extract().AllStringArray())
        db_manga["date"]=" ".join(selector.xpath("//b[text()='MPark Page Creation']/parent::*/following-sibling::div//text()").extract().AllStringArray())
        db_manga["follow_num"]=selector.xpath("//i[@name='check-circle'][text()='']/following-sibling::span/text()").extract().FirstOrDefaultString()
        db_manga["review_num"]=selector.xpath("//i[text()='']/following-sibling::span/text()").extract().LastOrDefaultString()
        db_manga["comment_num"]=selector.xpath("//div[@class='space-y-2 hidden md:block']//i[@name='comments'][text()='']/following-sibling::span/text()").extract().LastOrDefaultString()
        db_manga["views_info"]=selector.xpath("//b[text()='Views']/parent::*/following-sibling::div//text()").extract().AllString()
        db_manga["readers_info"]=selector.xpath("//b[text()='Readers']/parent::*/following-sibling::div//text()").extract().AllString()

        db_manga["vote_num"]=selector.xpath('//*[@id="app-wrapper"]/main/div[1]/div[2]/div[3]/div[1]/div/div[1]/div[3]/text()').extract().FirstOrDefaultString()
        db_manga["score"]=selector.xpath('//*[@id="app-wrapper"]/main/div[1]/div[2]/div[3]/div[1]/div/div[1]/div[1]/span/text()').extract().FirstOrDefaultString()
        db_manga["star5_ratio"]=selector.xpath('//*[@id="app-wrapper"]/main/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[1]/span/text()').extract().FirstOrDefaultString()
        db_manga["star4_ratio"]=selector.xpath('//*[@id="app-wrapper"]/main/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[2]/span/text()').extract().FirstOrDefaultString()
        db_manga["star3_ratio"]=selector.xpath('//*[@id="app-wrapper"]/main/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[3]/span/text()').extract().FirstOrDefaultString()
        db_manga["star2_ratio"]=selector.xpath('//*[@id="app-wrapper"]/main/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[4]/span/text()').extract().FirstOrDefaultString()
        db_manga["star1_ratio"]=selector.xpath('//*[@id="app-wrapper"]/main/div[1]/div[2]/div[3]/div[1]/div/div[2]/div[5]/span/text()').extract().FirstOrDefaultString()
        # db_manga["rate_awesome"]=selector.xpath("//*[name()='g'][@class='recharts-layer recharts-label-list']/*[name()='text'][1]/*[name()='tspan']/text()").extract().FirstOrDefaultString()
        # db_manga["rate_funny"]=selector.xpath("//*[name()='g'][@class='recharts-layer recharts-label-list']/*[name()='text'][2]/*[name()='tspan']/text()").extract().FirstOrDefaultString()
        # db_manga["rate_love"]=selector.xpath("//*[name()='g'][@class='recharts-layer recharts-label-list']/*[name()='text'][3]/*[name()='tspan']/text()").extract().FirstOrDefaultString()
        # db_manga["rate_hot"]=selector.xpath("//*[name()='g'][@class='recharts-layer recharts-label-list']/*[name()='text'][4]/*[name()='tspan']/text()").extract().FirstOrDefaultString()

        db_manga["Genres"]=selector.xpath("//b[text()='Genres:']/following-sibling::span//text()").extract().AllString()
        db_manga["language"]=selector.xpath("//b[text()='Genres:']/parent::*/following-sibling::div[1]//text()").extract().AllString()
        db_manga["original_publication"]=selector.xpath("//span[text()='Original Publication:']/following-sibling::span//text()").extract().AllString()
        db_manga["MPark_upload_status"]=selector.xpath("//span[text()='MPark Upload Status:']/following-sibling::span//text()").extract().AllString()
        db_manga["read_direction"]=selector.xpath("//span[text()='Read Direction:']/following-sibling::span//text()").extract().AllString()
        yield db_manga
        # 处理章节信息
        for item in selector.xpath('//*[@id="app-wrapper"]/main/div[4]/div[2]/div/div/div'):
            db_chapter=ChapterInfo()
            db_chapter["manga_name"]=db_manga["name"]
            db_chapter["chapter_name"]=item.xpath("./div[1]//text()").extract().AllString()
            db_chapter["chapter_url"]=item.xpath("./div[1]/a/@href").extract().AllString().strip()
            if not db_chapter["chapter_url"]:
                continue
            db_chapter["chapter_url"]=parse.urljoin("https://mangapark.net/",db_chapter["chapter_url"])
            db_chapter["date"]=item.xpath(".//span[contains(text(),'days ago')]/text()").extract().FirstOrDefaultString().split(" ")[0]
            if db_chapter["date"]:
                db_chapter["date"]=DateTime.Now().Date().AddDays(-int(db_chapter["date"])).ToString("yyyy-MM-dd")
            yield db_chapter

            # headers=self.headers.copy()
            headers=self.get_header()
            headers["cookie"]=self.get_cookie()
            yield Request(db_chapter["chapter_url"], callback=self.parse_manga_image,headers=headers,dont_filter=True,meta={
                "db_manga":db_manga,
                "db_chapter":db_chapter
            })

    def parse_manga_image(self,response):
        image_list=ExObject.regex("https://xfs-n[0-9]+.xfspp.com/comic/.*?.jpeg",response.text)
        for image_url in image_list:
            db_image=ImageInfo()
            db_image["manga_name"]=response.meta["db_chapter"]["manga_name"]
            db_image["chapter_name"]=response.meta["db_chapter"]["chapter_name"]
            db_image["image_url"]=image_url.ToString()
            yield db_image

    def get_cookie(self):
        ck="""Hm_lvt_a7025e25c8500c732b8f48cc46e21467=1716138830; theme=mdark; tfv=1716138947082; ps_sort=field_name; cf_clearance=f2U8suCaFMS6L1WQh4bwxStXHZi68w.nMWh130s3ZLA-1716139708-1.0.1.1-2CyZLSA4mj.3Nw2Y5lu4lwyWxSyULc.rriUQMZO6YEltqBSzDxB6NZ6o5h8bF6ao5luF1FMEzq9czeHmkA_MhA; Hm_lpvt_a7025e25c8500c732b8f48cc46e21467=1716141222"""
        return ck
    
    def get_ua(self,level=0):
        _header = ua_generator.generate(device='desktop', browser=('chrome', 'edge')).headers.get()
        ua=_header.get("user-agent")
        if not ua:
            ua=_header.get("User-Agent")
            _header["user-agent"]=_header["User-Agent"]
            del _header["User-Agent"]
        return _header
    
    def get_header(self):
        _header = self.get_ua()
        headers = {
            "accept": "*/*",
            "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
            "sec-ch-ua": _header["sec-ch-ua"],
            "sec-ch-ua-mobile": _header["sec-ch-ua-mobile"],
            "sec-ch-ua-platform": _header["sec-ch-ua-platform"],
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-csrf-protection": "1",
            "Referer": "https://mangapark.net/",
            "Referrer-Policy": "origin-when-cross-origin",
            "user-agent":_header["user-agent"]
        }
        return headers
    
    def before_request(self, request):
        now=DateTime.Now()
        if (now-self.last_change_proxy)>TimeSpan(second=60) or (request.meta.get("retry_times") and request.meta["retry_times"]>1):
            # 切代理
            self.p+=1
            params={"name":self.proxy_names[rd.randint(0,len(self.proxy_names)-1)]}
            url=parse.urljoin(self.base_url,"/proxies/GLOBAL")
            r=requests.put(url, json=params, headers={
                'content-type': 'application/json',
                "Authorization":"Bearer "+self.secret
                })
            self.last_change_proxy=now
        request.meta['proxy'] = self.proxy
        return request