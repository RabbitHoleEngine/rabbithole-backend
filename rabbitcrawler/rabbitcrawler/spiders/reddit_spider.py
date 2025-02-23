import scrapy
from ..items import Reddit
from collections import defaultdict



class RedditSpider(scrapy.Spider):
    name = "reddit"
    

    def __init__(self, query, max_depth=3, *args, **kwargs):
        super(RedditSpider, self).__init__(*args, **kwargs)
        self.start_urls = [f"https://www.reddit.com/search/?q={query}"]
        self.table = defaultdict(set)
        self.max_depth = int(max_depth)
    

    def parse(self, response, current_depth=1):
        if current_depth > self.max_depth:
            return
            
        post_links = response.css("a[data-testid='post-title']::attr(href)").getall()[:5]            
        for post_link in post_links:
            post = Reddit()
            full_url = response.urljoin(post_link)
            self.table[current_depth].add(full_url)
            yield scrapy.Request(
                url=full_url, 
                callback=self.parse_post, 
                meta={"post": post, "depth": current_depth}
            )


        if current_depth < self.max_depth:
            all_links = response.css("a::attr(href)").getall()[:5]
            for link in all_links:
                full_url = response.urljoin(link)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse,
                    meta={"current_depth": current_depth + 1}
                )

    
    def parse_post(self, response):
        post = response.meta["post"]
        post["url"] = response.url
        post["title"] = response.css("h1::text").get().strip()
        post["depth"] = response.meta["depth"]
        yield post
    

    def closed(self, reason):
        print("\nCrawled URLs by depth:")
        for depth, urls in self.table.items():
            print(f"\nDepth {depth}:")
            for url in urls:
                print(f"  {url}")