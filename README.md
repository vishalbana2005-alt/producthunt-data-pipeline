# Product Hunt Data Pipeline

An end-to-end, automated ELT pipeline that ingests live product launch data from the Product Hunt GraphQL API, lands it in Snowflake, transforms it with dbt, and runs on an hourly schedule orchestrated by Apache Airflow in Docker.

## Architecture

Product Hunt API (GraphQL)
        |
        v
Python ingestion script (requests)
        |
        v
Snowflake - RAW schema (raw JSON, untouched)
        |
        v
dbt transformation (LATERAL FLATTEN)
        |
        v
Snowflake - ANALYTICS schema (clean, typed columns)

Orchestrated hourly by Airflow, running in Docker.

## Tech Stack

- Source: Product Hunt GraphQL API
- Ingestion: Python (requests, python-dotenv)
- Warehouse: Snowflake
- Transformation: dbt (dbt-snowflake)
- Orchestration: Apache Airflow
- Containerization: Docker / Docker Compose

## How It Works

1. Ingestion - load_to_snowflake.py authenticates to Product Hunt's GraphQL API with a developer token, queries the latest product launches, and inserts the raw JSON response into PRODUCTHUNT_PIPELINE.RAW.RAW_PRODUCTHUNT_POSTS as a Snowflake VARIANT column, timestamped on load.

2. Transformation - the dbt model stg_producthunt_posts reads from the raw source and uses Snowflake's LATERAL FLATTEN to unroll the nested GraphQL edges/node structure into one row per product, extracting product_name, tagline, votes_count, and created_at as properly typed columns in the ANALYTICS schema.

3. Orchestration - the Airflow DAG producthunt_pipeline runs hourly, executing ingestion then transformation in sequence, with 2 automatic retries on failure.

## Design Decisions

Raw layer stays untouched. The ingestion script stores the complete API response as JSON rather than parsing it upfront. If transformation logic has a bug, data can be reprocessed from raw without re-calling the API.

dbt handles all transformation logic. Keeping transformation in SQL rather than Python means the logic is version-controlled, testable, and readable by anyone who knows SQL.

Rate-limit-aware scheduling. Product Hunt's free tier allows roughly 60 requests/hour; running hourly with a small number of calls per run stays well within limits.

## Setup

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Create a .env file with your credentials, then run manually:
python load_to_snowflake.py

Or start Airflow to run it on schedule:
cd airflow
docker compose up airflow-init
docker compose up -d
Airflow UI at http://localhost:8080

## Engineering Challenges Solved

GraphQL nesting bug - fields returned NULL after flattening because the extraction path skipped the node wrapper inside each edge. Diagnosed by querying the raw JSON structure directly in Snowflake.

Python version incompatibility - dbt failed to install on Python 3.14. Resolved by installing Python 3.11 via Homebrew in a separate virtual environment.

Airflow container isolation - Airflow's containers could not access the host machine's Python environments. Resolved by mounting the project directory and declaring required packages via _PIP_ADDITIONAL_REQUIREMENTS.

dbt invocation inside Airflow - python -m dbt run fails since dbt is a package, not a directly executable module. Corrected to invoke the dbt CLI directly with an explicit --profiles-dir.

## Security

Credentials are never committed. .env and dbt_profiles/ are gitignored; Airflow containers read credentials from the mounted .env at runtime.
