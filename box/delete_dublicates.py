import psycopg
from psycopg import sql


# Название схемы и таблиц и папки с обученными весами
schema_name_in_db = 'workflow'
raw_mark_table_name_in_db = 'raw_mark_data'


def mark_delete_dublicat():
    query_unique = sql.SQL('''
    DELETE FROM {table_raw_mark} a
    USING {table_raw_mark} b
    WHERE a.mark_id > b.mark_id
        AND a.x_1 = b.x_1
        AND a.y_1 = b.y_1
        AND a.x_2 = b.x_2
        AND a.y_2 = b.y_2
        AND a.image_name = b.image_name;
    ''').format(
        table_raw_mark=sql.Identifier(schema_name_in_db,
                                      raw_mark_table_name_in_db)
    )

    with psycopg.connect('dbname=ai_project user=API_write_data \
    password=1111') as conn:
        conn.execute(query_unique)
