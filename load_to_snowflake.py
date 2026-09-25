import json
import os

import requests
import snowflake.connector
from dotenv import load_dotenv

API_URL = "https://api.producthunt.com/v2/api/graphql"

QUERY = """
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


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def fetch_producthunt_posts():
    response = requests.post(
        API_URL,
        json={"query": QUERY},
        headers={
            "Authorization": f"Bearer {required_env('PH_DEVELOPER_TOKEN')}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()

    if data.get("errors"):
        raise RuntimeError(f"Product Hunt GraphQL error: {data['errors']}")

    edges = data.get("data", {}).get("posts", {}).get("edges")
    if not isinstance(edges, list):
        raise RuntimeError("Unexpected Product Hunt response structure.")

    return data, len(edges)


def main():
    load_dotenv()

    data, post_count = fetch_producthunt_posts()
    print(f"Retrieved {post_count} Product Hunt posts.")

    conn = None
    cursor = None

    try:
        conn = snowflake.connector.connect(
            account=required_env("SNOWFLAKE_ACCOUNT"),
            user=required_env("SNOWFLAKE_USER"),
            password=required_env("SNOWFLAKE_PASSWORD"),
            warehouse=required_env("SNOWFLAKE_WAREHOUSE"),
            database=required_env("SNOWFLAKE_DATABASE"),
            schema=required_env("SNOWFLAKE_SCHEMA"),
        )
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RAW_PRODUCTHUNT_POSTS (
                raw_json VARIANT,
                loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """)

        cursor.execute(
            "INSERT INTO RAW_PRODUCTHUNT_POSTS (raw_json) SELECT PARSE_JSON(%s)",
            (json.dumps(data),),
        )

        print(f"Loaded {post_count} posts into Snowflake.")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
