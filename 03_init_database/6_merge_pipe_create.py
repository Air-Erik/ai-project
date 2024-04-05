import psycopg
from psycopg import sql


# Название схемы и таблиц
schema_pipe = 'pipe'
raw_pipe_tab = 'raw_pipe'
pipe_tab = 'pipe'

query_merge = sql.SQL(
    '''
    CREATE OR REPLACE FUNCTION dump_merge_pipe()
    RETURNS void AS
    $$
    BEGIN
        WITH dumped_lines AS (
            SELECT
                (ST_Dump(rp.pipe)).geom AS line,
                rp.class_id,
                rp.plan_id
            FROM
                {table_raw_pipe} rp
        ),
        clustered_lines AS (
            SELECT
                line,
                ST_ClusterDBSCAN(line, eps := 0, minpoints := 1)
                    OVER () AS cluster_id,
                class_id,
                plan_id
            FROM
                dumped_lines
        ),
        unioned_lines AS (
            SELECT
                cluster_id,
                ST_Union(line) AS united_line,
                class_id,
                plan_id
            FROM
                clustered_lines
            GROUP BY
                cluster_id, class_id, plan_id
        )
        INSERT INTO {table_pipe} (pipe_final, class_id, plan_id)
        SELECT
            ST_LineMerge(united_line),
            class_id,
            plan_id
        FROM
            unioned_lines;
    END;
    $$
    LANGUAGE plpgsql;
    '''
).format(
    table_raw_pipe=sql.Identifier(schema_pipe, raw_pipe_tab),
    table_pipe=sql.Identifier(schema_pipe, pipe_tab)
)

with psycopg.connect('dbname=ai_project user=API_write_data \
password=1111') as conn:
    conn.execute(query_merge)
