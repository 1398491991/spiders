# -*- coding: utf-8 -*-
import scrapy


class QfangwangSpider(scrapy.Spider):
    name = "Qfangwang"
    # allowed_domains = ["shanghai.qfang.com"]
    start_urls = (
        'http://shanghai.qfang.com/',
    )

    def parse(self, response):
        pass
