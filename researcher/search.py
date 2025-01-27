import requests
import httpx
from langchain.text_splitter import RecursiveCharacterTextSplitter


class SearXNG:
    def __init__(self):
        self.httpx_client = httpx.Client(verify=False)
        self.instance = "http://localhost:8888/search"
        self.params = {
            "format": "json",
            "categories": "general",
            "language": "en",
        }

    def get_urls(self, query):
        self.params |= {"q": query}
        try:
            response = requests.get(self.instance, params=self.params)
            response.raise_for_status()

            data = response.json()

            print(f"Total results: {len(data['results'])}")
            for result in data["results"]:
                print(f"\nTitle: {result['title']}")
                print(f"URL: {result['url']}")
                print(f"Content: {result['content'][:100]}...")

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except KeyError as e:
            print(f"Unexpected JSON format: {e}")

    def get_htmls(self):
        pass

    def get_articles_chunks(self):
        pass
