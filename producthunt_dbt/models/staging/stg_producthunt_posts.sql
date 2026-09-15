WITH source AS (
    SELECT raw_json
    FROM {{ source('raw', 'raw_producthunt_posts') }}
),

flattened AS (
    SELECT
        f.value:node:name::string AS product_name,
        f.value:node:tagline::string AS tagline,
        f.value:node:votesCount::number AS votes_count,
        f.value:node:createdAt::timestamp AS created_at
    FROM source,
    LATERAL FLATTEN(input => source.raw_json:data:posts:edges) f
)

SELECT * FROM flattened
