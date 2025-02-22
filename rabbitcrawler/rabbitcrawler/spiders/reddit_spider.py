import scrapy
from ..items import Reddit

class RedditSpider(scrapy.Spider):
    name = "reddit"
    
    def __init__(self, query, *args, **kwargs):
        super(RedditSpider, self).__init__(*args, **kwargs)
        self.start_urls = [f"https://www.reddit.com/search/?q={query}"]
        
    def parse(self, response):
        post_links = response.css("a[data-testid='post-title']::attr(href)").getall()[:5]
        for post_link in post_links:
            post=Reddit()
            full_url = response.urljoin(post_link)
            yield scrapy.Request(url=full_url, callback=self.parse_post, meta={"post": post})
            
    def parse_post(self, response):
        post = response.meta["post"]
        post["url"] = response.url
        post["title"] = response.css("h1::text").get().strip()
        yield post