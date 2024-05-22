import scrapy
import os
import random as rd
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.images import ImagesPipeline
from manga_crawler.model.manga_park import MangaInfo,ChapterInfo,ImageInfo
import ua_generator
class ImagePipeline(FilesPipeline):
    def __init__(self, store_uri, download_func=None, settings=None):
        super().__init__(store_uri, download_func, settings)

    def get_media_requests(self, item, info):
        if type(item) is ImageInfo:
            file_name=item["image_url"].split("/")[-1].split("?")[0].split("#")[0]
            dir_path=os.path.join(self.safe_file_name(item["manga_name"]),self.safe_file_name(item["chapter_name"]))
            # if not os.path.exists(os.path.join(self.base_path,dir_path)):
            #     os.makedirs(dir_path)
            full_path=os.path.join(dir_path,self.safe_file_name(file_name,True))
            item["full_path"]=full_path
            if os.path.exists(full_path):
                print("skip:"+full_path)
                return None
            return [scrapy.Request(item["image_url"],meta={"dbItem":item})]

    def file_path(self, request, response=None, info=None):
        dbItem=request.meta["dbItem"]
        r=dbItem["full_path"]
        return r

    def item_completed(self, results, dbItem, info):
        if len(results)==0:
            return dbItem
        if not results[0][0]:
            return dbItem

        info.spider.logger.info(dbItem["full_path"]+" OK")
        return dbItem

    def safe_file_name(self,v,is_file=False):
        v = (v.replace("\\","_")
                .replace("\/","_")
                .replace(":","_")
                .replace("*","_")
                .replace("?","_")
                .replace('"',"_")
                .replace('<',"_")
                .replace('>',"_")
                .replace('|',"_"))
        if not is_file:
            v=v.replace(".","~")
        return v