import scrapy

from ..items import Reddit

class RedditSpider(scrapy.Spider):
    name = "reddit"

    def __init__(self, query):
        self.query = query
        self.start_urls = ["https://www.reddit.com/"]

    def start_requests(self):
        base_url = f"https://www.reddit.com/search?q={self.query}"
        urls = [
            base_url + self.query,
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        post = Reddit()
        post_links = response.css("a[data-testid='post-title']::attr(href)").getall()[:5]
        for post_link in post_links:
            full_url = response.urljoin(post_link)
            yield scrapy.Request(url=full_url, callback=self.parse_post, meta={"post": post}) 

    def parse_post(self, response):
        post = response.meta["post"]
        post["url"] = response.url
        post["title"] = response.css("h1::text").get().strip()
        yield post

        # next_page_url = response.css("li.next>a::attr(href)").extract_first()

        # if next_page_url:
        #     next_page_url = response.urljoin(next_page_url)
        #     yield scrapy.Request(url=next_page_url, callback=self.parse)