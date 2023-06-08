import requests
from bs4 import BeautifulSoup
import redis
import random
import time
import os
from dotenv import load_dotenv
from langdetect import detect
import re

# Purpose: This script is used to get random wikipedia articles and save them to a redis database. The article content will be added to a custom training
# dataset for our in house LLM models. The script will run indefinitely if allowed and will eventually all of wikipedia. This is a base implementation,
# there will be updates for data cleaning, summarization, entity mapping and a rabbit hole function to dive deeper into links from article reference
# on articles within flagged topics or categories.  This is also fun for a random fact or trivia bot for discord or slack.

# Load environment variables
load_dotenv()

# Get a random wikipedia article
def get_random_wikipedia_article():
    response = requests.get(url="https://en.wikipedia.org/wiki/Special:Random")
    return response

# Parse the wikipedia article
def parse_wikipedia_article(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    page_title = soup.find('title').text
    page_content = soup.find('div', {'id': 'mw-content-text'}).text
    return page_title, page_content

# Save text to redis
def save_text_to_redis(redis_instance, key, text):
    redis_instance.set(key, text)

# Get data from redis
def get_data_from_redis(redis_instance, key):
    return redis_instance.get(key).decode('utf-8')

# Delete keys from redis
def delete_keys(redis_instance, pattern):
    keys = redis_instance.keys(pattern)
    if keys:
        redis_instance.delete(*keys)

# Remove citation references [*]
def remove_references(text):
    # Remove the square brackets and numbers inside them
    text = re.sub(r'\[\d+\]', '', text)
    return text

def main():
    # Instantiate the redis database. 
    r = redis.Redis(
        host= os.getenv("UPSTASH_HOST"),
        port = '40237',
        password = os.getenv("UPSTASH_PASSWORD"),
        ssl=True,
    )
    print('Redis Instantiated')
        
    # run loop to get random wikipedia articles and save to redis database
    while True:
        response = get_random_wikipedia_article()
        page_title, page_content = parse_wikipedia_article(response)
        
        key = f'trainingData:wikipedia:{page_title}'
        
        if r.exists(key):
            print(f"Article {page_title} has been visited before. Updating the content.")
            r.delete(key)
        else:
            print(f"New article found: {page_title}. Saving the content.")
        
        # check if the text is English
        try:
            if detect(page_content) != 'en':
                print(f"Skipping non-English article: {page_title}")
                continue
        except Exception as e:
            print(f"Skipping article due to error during language detection: {page_title}. Error: {str(e)}")
            time.sleep(random.randint(1, 12))
            continue

        # Remove citation references [*]
        page_content = remove_references(page_content)

        # Save the content to redis
        save_text_to_redis(r,key, page_content)
        
        # wait between 1 to 5 seconds before next request to respect Wikipedia's server
        time.sleep(random.randint(1,12))  

if __name__ == "__main__":
    main()
