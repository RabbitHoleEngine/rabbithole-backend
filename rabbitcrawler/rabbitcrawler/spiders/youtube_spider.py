import scrapy
from ..items import Youtube
from collections import defaultdict



class YoutubeSpider(scrapy.Spider):
    name = "youtube"
    

    def __init__(self, query, max_depth=3, *args, **kwargs):
        super(YoutubeSpider, self).__init__(*args, **kwargs)
        self.start_urls = [f"https://www.youtube.com/results?search_query={query}"]
        self.table = defaultdict(set)
        self.max_depth = int(max_depth)
    

    def parse(self, response, current_depth=1):
        if current_depth > self.max_depth:
            return


        video_links = response.css("a[class='yt-simple-endpoint']::attr(href)").getall()[:5]
        print("LINKSSSSSSSSSSS", video_links)         
        for video_link in video_links:
            post = Youtube()
            full_url = response.urljoin(video_link)
            self.table[current_depth].add(full_url)
            yield scrapy.Request(
                url=full_url, 
                callback=self.parse_post, 
                meta={"post": post, "depth": current_depth}
            )
            

        if current_depth < self.max_depth:
            description_links = response.css("a[class='yt-core-attributed-string--link']::attr(href)").getall()[:5]            
            for description_link in description_links:
                post = Youtube()
                full_url = response.urljoin(description_link)
                self.table[current_depth].add(full_url)
                yield scrapy.Request(
                    url=full_url, 
                    callback=self.parse_post, 
                    meta={"post": post, "depth": current_depth}
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