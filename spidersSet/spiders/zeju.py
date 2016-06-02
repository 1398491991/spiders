# -*- coding: utf-8 -*-
import scrapy


class ZejuSpider(scrapy.Spider):
    name = "zeju"
    # allowed_domains = ["http://www.zeju.com/"]
    start_urls = (
        'http://www.zeju.com/',
    )

    def parse(self, response):
        pass
