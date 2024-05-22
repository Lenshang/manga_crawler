from manga_crawler.model.manga_park import MangaInfo,ChapterInfo
from sqlalchemy import create_engine
from sqlalchemy.engine.mock import MockConnection
from sqlalchemy.orm import sessionmaker,Session
import os
import json
class LocalFilePipeline(object):
    def __init__(self) -> None:
        pass

    def process_item(self, item, spider):
        base_path=spider.settings["FILES_STORE"]
        if type(item) is MangaInfo:
            full_path=os.path.join(base_path,self.safe_file_name(item["name"]))
            if not os.path.exists(full_path):
                os.makedirs(full_path)
            full_path=os.path.join(full_path,"info.json")
            if not os.path.exists(full_path):
                with open(full_path,"w") as f:
                    f.write(json.dumps(dict(item)))
        elif type(item) is ChapterInfo:
            full_path=os.path.join(base_path,self.safe_file_name(item["manga_name"]),self.safe_file_name(item["chapter_name"]))
            if not os.path.exists(full_path):
                os.makedirs(full_path)
            full_path=os.path.join(full_path,"info.json")
            if not os.path.exists(full_path):
                with open(full_path,"w") as f:
                    f.write(json.dumps(dict(item)))
        else:
            pass
        return item
        # dbItem=DbPPHero(**item)
        # self.db.merge(dbItem)
        # self.db.commit()

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
    