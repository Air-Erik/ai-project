import psycopg
from psycopg import sql


# Название схемы и таблиц
schema_pipe = 'pipe'
pipe_tab = 'pipe'

query_process_multilinestring = sql.SQL(
    '''
    CREATE OR REPLACE FUNCTION process_multilinestring()
    RETURNS TRIGGER AS
    $$
    BEGIN
        -- Проверка, является ли вставляемая геометрия MULTILINESTRING
        IF GeometryType(NEW.pipe_final) = 'MULTILINESTRING' THEN
            -- Извлечение и установка самой длинной LINESTRING из MULTILINE
            NEW.pipe_final := (
                SELECT ST_LineMerge(ST_Collect(dmp.geom)) AS single_line
                FROM (
                    SELECT (ST_Dump(NEW.pipe_final)).geom AS geom
                    ORDER BY ST_Length((ST_Dump(NEW.pipe_final)).geom) DESC
                    LIMIT 1
                ) AS dmp
            );
        END IF;
        RETURN NEW; -- Возвращаем модифицированную запись для вставки
    END;
    $$
    LANGUAGE 'plpgsql';
    '''
)

query_unique = sql.SQL(
    '''
    CREATE OR REPLACE FUNCTION check_uniqueness()
    RETURNS TRIGGER AS
    $$
    BEGIN
        -- Проверяем, существует ли уже такая же геометрия в таблице
        IF EXISTS (
            SELECT 1
            FROM {table_pipe}
            WHERE ST_Equals(pipe_final, NEW.pipe_final)
        ) THEN
            -- Если найден дубликат, генерируем исключение для отмены вставки
            RETURN NULL;
        END IF;
        RETURN NEW;
    END;
    $$
    LANGUAGE 'plpgsql';
    '''
).format(table_pipe=sql.Identifier(schema_pipe, pipe_tab))

query_triger_1 = sql.SQL(
    '''
    CREATE OR REPLACE TRIGGER check_multilinestring_before_insert
    BEFORE INSERT ON {table_pipe}
    FOR EACH ROW
    EXECUTE FUNCTION process_multilinestring();
    '''
).format(table_pipe=sql.Identifier(schema_pipe, pipe_tab))

query_triger_2 = sql.SQL(
    '''
    CREATE OR REPLACE TRIGGER check_unique_before_insert
    BEFORE INSERT ON {table_pipe}
    FOR EACH ROW
    EXECUTE FUNCTION check_uniqueness();
    '''
).format(table_pipe=sql.Identifier(schema_pipe, pipe_tab))

with psycopg.connect('dbname=ai_project user=API_write_data \
password=1111') as conn:
    conn.execute(query_process_multilinestring)
    conn.execute(query_unique)
    conn.execute(query_triger_1)
    conn.execute(query_triger_2)
