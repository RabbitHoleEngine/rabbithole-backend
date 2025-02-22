from flask import Flask, request, jsonify
from scrapy.crawler import CrawlerRunner
from scrapy.signalmanager import dispatcher
from twisted.internet import reactor, defer
from scrapy import signals
from scrapy.utils.project import get_project_settings

from rabbitcrawler.rabbitcrawler.spiders.crawling_spider import RedditCrawler

app = Flask(__name__)
runner = CrawlerRunner(get_project_settings())
scraped_data = []


def run_spider(query):
    """Runs the Scrapy spider and collects data into scraped_data."""
    global scraped_data
    scraped_data = []

    def _item_scraped(item, response, spider):
        """Scrapy signal handler to collect items."""
        scraped_data.append(item)

    dispatcher.connect(_item_scraped, signal=signals.item_scraped)

    @defer.inlineCallbacks
    def crawl():
        yield runner.crawl(RedditCrawler, query=query)

    dispatcher.connect(lambda _: reactor.callFromThread(reactor.stop), signal=signals.spider_closed)

    if not reactor.running:
        reactor.callWhenRunning(crawl)
        reactor.run(installSignalHandlers=False)
    else:
        reactor.callFromThread(crawl)


@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("query")
    run_spider(query)

    import time
    time.sleep(2)

    return jsonify(scraped_data)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
