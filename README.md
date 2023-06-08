# WikiCrawl Scraper- Python w/ Upstash Redis
### [3Juliet AI](https://www.3juliet.ai/) | 8-Jun-2023

<hr>

## Introduction

This project is a Python script that continuously retrieves random articles from Wikipedia and stores them into a Redis database. The purpose of this script is to add to our in-house training datasets. The script, as it stands, can run indefinitely, building up a large repository of data over time..

This script provides a base implementation for the larger goal, which includes data cleaning, summarization, entity mapping, and a "rabbit hole" function for a deep dive into links from article references on flagged topics or categories. This tool can also be fun for generating random trivia for bots on platforms like Discord or Slack.

## How It Works

The script utilizes several libraries to perform its functions, including BeautifulSoup for web scraping, requests for making HTTP requests, and langdetect to filter English articles. We make use of Redis as our NoSQL database to store the scraped content, where each article is stored as a key-value pair.

Sure, here's an updated section that provides a detailed review of the implementation along with relevant code snippets:

### The Code

1. **Loading Environment Variables:** 

The script starts by loading environment variables using the `dotenv` library. This is where your Redis credentials should be stored.

```python
load_dotenv()
```

2. **Getting a Random Wikipedia Article:**

We define a function `get_random_wikipedia_article()` that sends a GET request to a special URL on Wikipedia that redirects to a random article.

```python
def get_random_wikipedia_article():
    response = requests.get(url="https://en.wikipedia.org/wiki/Special:Random")
    return response
```

3. **Parsing the Wikipedia Article:**

The function `parse_wikipedia_article(response)` is defined to parse the HTML response from the GET request. It utilizes BeautifulSoup to extract the title and the content of the Wikipedia page.

```python
def parse_wikipedia_article(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    page_title = soup.find('title').text
    page_content = soup.find('div', {'id': 'mw-content-text'}).text
    return page_title, page_content
```

4. **Checking Language and Removing References:**

We utilize the `langdetect` library to ensure that we're only storing English articles. If the content is not in English, we skip the current iteration and proceed to the next article.

We also remove citation references within the text that are enclosed in square brackets by calling the `remove_references(page_content)` function. A regular expression is used to find citation references and replace them with an empty string.

```python
try:
    if detect(page_content) != 'en':
        print(f"Skipping non-English article: {page_title}")
        continue
except Exception as e:
    print(f"Skipping article due to error during language detection: {page_title}. Error: {str(e)}")
    time.sleep(random.randint(1, 12))
    continue

page_content = remove_references(page_content)
```

5. **Storing Article in Redis:**

The parsed and cleaned content is then saved to the Redis database. This is done by creating a unique key for each article using the title, and storing the content as the corresponding value.

I use hosted redis from [Upstash](https://www.upstash.com/) for most of my projects. [Railway](https://www.railway.app/) also
has a hosted redis that you can deploy with your project but i have not used it as of this project but i will try it soon, likely with another discord bot
deployment.

```python
key = f'trainingData:wikipedia:{page_title}'
save_text_to_redis(r, key, page_content)
```

6. **Running the Bot:**

The `main()` function encapsulates the entire workflow described above into an infinite loop, with a sleep delay added between each iteration to avoid overloading Wikipedia's servers.

```python
def main():
    # Instantiate the Redis database
    ...
    while True:
        response = get_random_wikipedia_article()
        page_title, page_content = parse_wikipedia_article(response)
        ...
        page_content = remove_references(page_content)
        save_text_to_redis(r,key, page_content)
        time.sleep(random.randint(1,12)) 
```

To stop the script from running, you can simply interrupt the execution (e.g., with `Ctrl+C` in the terminal).

This detailed review should help clarify the step-by-step implementation and workflow of the script.

## How To Implement

To implement this script:

1. **Install Required Libraries:** Make sure Python is installed on your system and install necessary libraries by running `pip install requests bs4 redis python-dotenv langdetect`.

2. **Set up Redis:** Create a Redis instance and obtain your Redis credentials (host, port, password).

3. **Environment Variables:** Store your Redis credentials in a `.env` file in the same directory as your Python script. The `.env` file should contain the following variables: `UPSTASH_HOST` and `UPSTASH_PASSWORD`.

4. **Running the Script:** Run the Python script in your terminal with `python <your_python_script.py>`. The script will start running indefinitely, fetching Wikipedia articles at random and storing them in the Redis database. To stop the script, use `Ctrl+C`.

### Here is the full code for reference:
####   * May include some revisions not present in the README above

```python

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


```