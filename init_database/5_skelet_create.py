import psycopg
from psycopg import sql

# Название схемы и таблиц
schema_pipe = 'pipe'
raw_pipe_tab = 'raw_pipe'
mask_tab = 'mask'
mask_join_tab = 'mask_join'

query_skelet = sql.SQL(
    '''
    CREATE OR REPLACE FUNCTION skeleton_pipe()
    RETURNS void AS
    $$
    BEGIN
        INSERT INTO {table_raw_pipe} (id, pipe, class_id, plan_id)
        SELECT
            m.id,
            ST_SnapToGrid(ST_CollectionExtract(ST_ApproximateMedialAxis(ST_SimplifyPolygonHull(m.mask_join, 0.1)), 2), 0.01),
            m.class_id,
            m.plan_id
        FROM
            {table_mask_join} m;
    END;
    $$
    LANGUAGE plpgsql;
    '''
).format(
    table_raw_pipe=sql.Identifier(schema_pipe, raw_pipe_tab),
    table_mask_join=sql.Identifier(schema_pipe, mask_join_tab)
)

with psycopg.connect('dbname=ai_project user=API_write_data \
password=1111') as conn:
    conn.execute(query_skelet)
