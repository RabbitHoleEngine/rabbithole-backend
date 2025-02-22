from klein import Klein
import json
from scrapy.utils.serialize import ScrapyJSONEncoder
from rabbitcrawler.rabbitcrawler.spiders.reddit_spider import RedditSpider
from spider_runner import SpiderRunner

app = Klein()

@app.route("/", methods=["GET"])
def home(request):
    return "Hello, World!"

def return_spider_output(output):
    _encoder = ScrapyJSONEncoder(ensure_ascii=False)
    return _encoder.encode(output)

@app.route('/search')
def get_quotes(request):
    content = json.loads(request.content.read())
    query = content.get("query")

    runner = SpiderRunner()

    deferred = runner.crawl(RedditSpider, query=query)
    deferred.addCallback(return_spider_output)

    return deferred

app.run("localhost", 8080)