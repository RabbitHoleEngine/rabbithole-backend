import scrapy
from ..items import Wiki
from collections import defaultdict



class RedditSpider(scrapy.Spider):
    name = "wiki"
    

    def __init__(self, query, max_depth=3, *args, **kwargs):
        super(RedditSpider, self).__init__(*args, **kwargs)
        self.start_urls = [f"https://en.wikipedia.org/w/index.php?fulltext=1&search={query}"]
        self.table = defaultdict(set)
        self.max_depth = int(max_depth)
    

    def parse(self, response, current_depth=1):
        if current_depth > self.max_depth:
            return
            
        wiki_links = response.css(".mw-search-result-heading a::attr(href)").getall()[:5]
        for wiki_link in wiki_links:
            wiki = Wiki()
            full_url = response.urljoin(wiki_link)
            self.table[current_depth].add(full_url)
            yield scrapy.Request(
                url=full_url, 
                callback=self.parse_wiki, 
                meta={"wiki": wiki, "depth": current_depth}
            )


        if current_depth < self.max_depth:
            all_links = response.css("a::attr(href)").getall()
            non_wiki_links = [response.urljoin(link) for link in all_links if "wikipedia.org" not in link][:10]
            for link in non_wiki_links:
                full_url = response.urljoin(link)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse,
                    meta={"current_depth": current_depth + 1}
                )

    
    def parse_wiki(self, response):
        wiki = response.meta["wiki"]
        wiki["url"] = response.url
        wiki["title"] = response.css(".mw-page-title-main::text").get().strip()
        wiki["depth"] = response.meta["depth"]
        yield wiki
    

    def closed(self, reason):
        print("\nCrawled URLs by depth:")
        for depth, urls in self.table.items():
            print(f"\nDepth {depth}:")
            for url in urls:
                print(f"  {url}")