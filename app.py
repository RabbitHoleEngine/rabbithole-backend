from klein import Klein
import json
from scrapy.utils.serialize import ScrapyJSONEncoder
from rabbitcrawler.rabbitcrawler.spiders.reddit_spider import RedditSpider
from spider_runner import SpiderRunner
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import datetime
import os
from numpy import dot
from numpy.linalg import norm

app = Klein()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['rabbithole']
pages_collection = db['pages']
queries_collection = db['queries']

# Initialize the vectorization model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def vectorize_content(content):
    return model.encode(content)

def vectorize_query(query):
    return model.encode(query)

def save_query_to_mongo(query, vector):
    queries_collection.insert_one({
        "query": query,
        "vector": vector.tolist(),
        "timestamp": datetime.datetime.utcnow()
    })

def save_page_to_mongo(url, title, content, vector):
    pages_collection.insert_one({
        "url": url,
        "title": title,
        "content": content,
        "vector": vector.tolist(),
        "timestamp": datetime.datetime.utcnow()
    })

def cosine_similarity(vec1, vec2):
    """Calculate the cosine similarity between two vectors."""
    return dot(vec1, vec2) / (norm(vec1) * norm(vec2))

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

    # Vectorize the query and save it to MongoDB
    query_vector = vectorize_query(query)
    save_query_to_mongo(query, query_vector)

    runner = SpiderRunner()
    deferred = runner.crawl(RedditSpider, query=query, max_depth=max_depth)
    
    def store_spider_output(output):
        # Fetch the vector for the query from MongoDB (or the current session)
        query_vector = queries_collection.find_one({"query": query})["vector"]

        # List to hold the similarity scores
        scored_pages = []

        # Calculate cosine similarity for each page and store the page along with its similarity score
        for page in output:
            url = page.get('url')
            title = page.get('title')
            content = page.get('content')
            page_vector = vectorize_content(content)
            similarity_score = cosine_similarity(query_vector, page_vector)
            
            # Add the page and its similarity score to the list
            scored_pages.append({
                "url": url,
                "title": title,
                "content": content,
                "similarity_score": similarity_score
            })

            # Save the page to MongoDB
            save_page_to_mongo(url, title, content, page_vector)

        # Sort pages by similarity score (highest first)
        scored_pages.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Return the top N results (e.g., top 10 most relevant)
        top_results = scored_pages[:10]  # Adjust the number as needed
        return json.dumps(top_results, ensure_ascii=False)

    deferred.addCallback(store_spider_output)

    return deferred

app.run("localhost", 8080)