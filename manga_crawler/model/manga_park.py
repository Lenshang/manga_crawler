import scrapy
class MangaInfo(scrapy.Item):
    manga_url=scrapy.Field()
    name=scrapy.Field()
    other_name=scrapy.Field()
    long_description=scrapy.Field()
    author=scrapy.Field()
    date=scrapy.Field()
    follow_num=scrapy.Field()
    review_num=scrapy.Field()
    comment_num=scrapy.Field()
    views_info=scrapy.Field()
    readers_info=scrapy.Field()

    vote_num=scrapy.Field()
    score=scrapy.Field()
    star5_ratio=scrapy.Field()
    star4_ratio=scrapy.Field()
    star3_ratio=scrapy.Field()
    star2_ratio=scrapy.Field()
    star1_ratio=scrapy.Field()
    # rate_awesome=scrapy.Field()
    # rate_funny=scrapy.Field()
    # rate_love=scrapy.Field()
    # rate_hot=scrapy.Field()

    Genres=scrapy.Field()
    language=scrapy.Field()
    original_publication=scrapy.Field()
    MPark_upload_status=scrapy.Field()
    read_direction=scrapy.Field()

class ChapterInfo(scrapy.Item):
    manga_name=scrapy.Field()
    chapter_name=scrapy.Field()
    chapter_url=scrapy.Field()
    date=scrapy.Field()

class ImageInfo(scrapy.Item):
    manga_name=scrapy.Field()
    chapter_name=scrapy.Field()
    image_url=scrapy.Field()
    full_path=scrapy.Field()