import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("PH_DEVELOPER_TOKEN")

url = "https://api.producthunt.com/v2/api/graphql"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

query = """
{
  posts(first: 5) {
    edges {
      node {
        name
        tagline
        votesCount
        createdAt
      }
    }
  }
}
"""

response = requests.post(url, json={"query": query}, headers=headers)
print(response.status_code)
print(response.json())
