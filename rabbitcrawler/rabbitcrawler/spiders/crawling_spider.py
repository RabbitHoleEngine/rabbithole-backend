from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class CrawlingSpider(CrawlSpider):
    name = ""
    allowed_domains = []
    start_urls = [""] 


    rules = (
        Rule(LinkExtractor(allow="")),
        Rule(LinkExtractor(allow="", deny=""), callback="")
    )

    def parse_item(self, response):
        yield {
            "": response.css("").get(),
        }