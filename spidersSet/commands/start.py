from scrapy.commands import ScrapyCommand  
# from scrapy.crawler import CrawlerRunner
from scrapy.utils.conf import arglist_to_dict
from scrapy.exceptions import UsageError
class Command(ScrapyCommand):
  
    requires_project = True
  
    def syntax(self):  
        return '[options]'  
  
    def short_desc(self):  
        return 'Runs all of the spiders'  

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_option("-a", dest="spargs", action="append", default=[], metavar="NAME=VALUE",
                          help="set spider argument (may be repeated)")
        parser.add_option("-o", "--output", metavar="FILE",
                          help="dump scraped items into FILE (use - for stdout)")
        parser.add_option("-t", "--output-format", metavar="FORMAT",
                          help="format to use for dumping items with -o")

    def process_options(self, args, opts):
        ScrapyCommand.process_options(self, args, opts)
        try:
            opts.spargs = arglist_to_dict(opts.spargs)
        except ValueError:
            raise ValueError("Invalid -s value, use -s NAME=VALUE", print_help=False)
    def run(self,args,opts):
        N=len(args)
        if len(args) < 1:
            raise UsageError()
        spider_loader = self.crawler_process.spider_loader
        args_all=spider_loader.list()
        if N==1 and args[0].upper()=='ALL':
            args=args_all
        self.startSpider(args,opts,args_all)
    def startSpider(self,args,opts,args_all):
        print u"\n**********************   spider list : %s  **********************\n"%args_all
        for spiderName in args:
            if spiderName not in args_all:
                print u"\n*****************  not found spiderName : %s  succeed ******************\n"%spiderName
                continue
            try:
                self.crawler_process.crawl(spiderName, **opts.spargs)
                print u"\n********************* crawl spiderName : %s  succeed ************\n"%spiderName
            except Exception as e:
                print u'\n********************* crawl spiderName : %s  failure Error :%s ************\n'%(spiderName,e)
        self.crawler_process.start()


