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


@app.route('/search', methods=["GET"])
def get_quotes(request):

    query = request.args.get(b"q")
    query = query[0].decode("utf-8")

    max_depth = (int)(request.args.get(b"d", [b"3"])[0])
    max_depth = 5 if max_depth > 5 else max_depth

    runner = SpiderRunner()

    deferred = runner.crawl(RedditSpider, query=query, max_depth=max_depth)
    deferred.addCallback(return_spider_output)

    return deferred


app.run("localhost", 8080)