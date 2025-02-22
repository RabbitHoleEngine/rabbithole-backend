import scrapy

class RedditCrawler(scrapy.Spider):
    name = "redditcrawler"
    
    def __init__(self, query, request_id, *args, **kwargs):
        super(RedditCrawler, self).__init__(*args, **kwargs)
        self.start_urls = [f"https://www.reddit.com/search/?q={query}"]
        self.request_id = request_id  # Store request_id to track results
        
    def parse(self, response):
        post_links = response.css("a[data-testid='post-title']::attr(href)").getall()[:5]
        for post_link in post_links:
            full_url = response.urljoin(post_link)
            yield scrapy.Request(full_url, callback=self.parse_post)
            
    def parse_post(self, response):
        yield {
            "request_id": self.request_id,  # Include request_id in results
            "url": response.url,
            "title": response.css("h1::text").get().strip(),
        }