import os
import json
import requests
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

# --- Step 1: Get data from Product Hunt ---
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
data = response.json()

# --- Step 2: Connect to Snowflake ---
conn = snowflake.connector.connect(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
)
cursor = conn.cursor()

# --- Step 3: Create a raw landing table (if it doesn't exist) ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS RAW_PRODUCTHUNT_POSTS (
    raw_json VARIANT,
    loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
""")

# --- Step 4: Insert the raw JSON response ---
cursor.execute(
    "INSERT INTO RAW_PRODUCTHUNT_POSTS (raw_json) SELECT PARSE_JSON(%s)",
    (json.dumps(data),)
)
print("Data loaded successfully into Snowflake.")

cursor.close()
conn.close()
