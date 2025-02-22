from flask import Flask, request, jsonify
from scrapy.crawler import CrawlerRunner
from scrapy.signalmanager import dispatcher
from twisted.internet import reactor, defer
from scrapy import signals
from scrapy.utils.project import get_project_settings
import uuid
from collections import defaultdict
from threading import Lock
import time
from concurrent.futures import ThreadPoolExecutor

from rabbitcrawler.rabbitcrawler.spiders.crawling_spider import RedditCrawler

app = Flask(__name__)
runner = CrawlerRunner(get_project_settings())

# Store results per request_id
results_store = defaultdict(list)
results_lock = Lock()
executor = ThreadPoolExecutor(max_workers=3)  # Limit concurrent crawls

def clean_old_results():
    """Periodically clean up old results to prevent memory leaks"""
    while True:
        time.sleep(300)  # Clean every 5 minutes
        current_time = time.time()
        with results_lock:
            for request_id in list(results_store.keys()):
                if current_time - results_store[request_id].get('timestamp', 0) > 300:
                    del results_store[request_id]

# Start cleanup thread
executor.submit(clean_old_results)

def store_item(item, response, spider):
    """Store scraped item in results store"""
    request_id = item['request_id']
    with results_lock:
        results_store[request_id].append({
            'url': item['url'],
            'title': item['title']
        })

@defer.inlineCallbacks
def run_spider(query, request_id):
    """Run spider for a specific request"""
    dispatcher.connect(store_item, signal=signals.item_scraped)
    yield runner.crawl(RedditCrawler, query=query, request_id=request_id)

def get_results(request_id, timeout=10):
    """Wait for and return results for a specific request"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        with results_lock:
            if request_id in results_store and results_store[request_id]:
                results = results_store[request_id]
                del results_store[request_id]  # Cleanup after retrieval
                return results
        time.sleep(1)
    return []

@app.route("/scrape", methods=["GET"])
def scrape():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
        
    request_id = str(uuid.uuid4())
    
    # Start crawler in reactor thread
    reactor.callFromThread(run_spider, query, request_id)
    
    # Wait for results
    results = get_results(request_id)
    
    return jsonify(results)

def initialize_reactor():
    """Initialize reactor in separate thread"""
    if not reactor.running:
        Thread(target=reactor.run, args=(False,)).start()

if __name__ == "__main__":
    from threading import Thread
    initialize_reactor()
    app.run(debug=True, use_reloader=False, threaded=True)