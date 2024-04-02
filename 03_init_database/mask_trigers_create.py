import psycopg
from psycopg import sql


# Название схемы и таблиц
schema_pipe = 'pipe'
schema_general = 'general'
drawing_tab = 'drawing_data'
image_tab = 'image_data'
raw_mask_tab = 'raw_mask'
mask_tab = 'mask'

# SQL запрос на создание функции проверки строки на уникальность по  5 столбцам
query_befor_insert = sql.SQL('''
    CREATE OR REPLACE FUNCTION before_insert_pipe()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Проверяем наличие дубликатов перед вставкой
        IF EXISTS (
            SELECT 1
            FROM {table}
            WHERE mask = NEW.mask
                AND image_name = NEW.image_name
        ) THEN
        -- Если дубликат найден, просто завершаем выполнение триггера
            RETURN NULL;
        END IF;

        -- Если проверка прошла успешно, возвращаем NEW для выполнения вставки
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
''').format(table=sql.Identifier(schema_pipe, raw_mask_tab))

# SQL запрос на создание тригера перед вставкой для проверки уникальности
query_triger_before_insert = sql.SQL('''
    CREATE OR REPLACE TRIGGER check_unique_before_insert
    BEFORE INSERT ON {table}
    FOR EACH ROW
    EXECUTE FUNCTION before_insert_pipe();
''').format(table=sql.Identifier(schema_pipe, raw_mask_tab))

# Подключение к датабейзу и выполнение запросов
with psycopg.connect('dbname=ai_project user=API_write_data \
password=1111') as conn:
    conn.execute(query_befor_insert)
    conn.execute(query_triger_before_insert)
