import psycopg
from psycopg import sql

# Название схемы и таблиц
schema_pipe = 'pipe'
raw_mask_tab = 'raw_mask'
mask_tab = 'mask'
mask_join_tab = 'mask_join'

# Создание функции для объедения полигонов одного класса и одного чертежа
# Функция возвращет мултиполигон
query_creat_func = sql.SQL(
    '''
    CREATE OR REPLACE FUNCTION insert_mask_join()
    RETURNS void AS
    $$
    BEGIN
        INSERT INTO {table_mask_join} (mask_join, class_id, plan_id)
        SELECT
            ST_Union(m.mask_final) AS mask_join,
            m.class_id,
            m.plan_id
        FROM
            {table_mask} m
        GROUP BY
            m.class_id, m.plan_id;
    END;
    $$
    LANGUAGE plpgsql;
    '''
).format(
    table_mask_join=sql.Identifier(schema_pipe, mask_join_tab),
    table_mask=sql.Identifier(schema_pipe, mask_tab)
)

# SQL запрос на создание функции проверки строки на уникальность по  5 столбцам
query_befor_insert = sql.SQL('''
    CREATE OR REPLACE FUNCTION before_insert_mask_join()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Проверяем наличие дубликатов перед вставкой
        IF EXISTS (
            SELECT 1
            FROM {table}
            WHERE mask_join = NEW.mask_join
        ) THEN
        -- Если дубликат найден, просто завершаем выполнение триггера
            RETURN NULL;
        END IF;

        -- Если проверка прошла успешно, возвращаем NEW для выполнения вставки
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
''').format(table=sql.Identifier(schema_pipe, mask_join_tab))

# SQL запрос на создание тригера перед вставкой для проверки уникальности
query_triger_before_insert = sql.SQL('''
    CREATE OR REPLACE TRIGGER check_unique_before_insert
    BEFORE INSERT ON {table}
    FOR EACH ROW
    EXECUTE FUNCTION before_insert_mask_join();
''').format(table=sql.Identifier(schema_pipe, mask_join_tab))

# Подключение к датабейзу и выполнение запросов
with psycopg.connect('dbname=ai_project user=API_write_data \
password=1111') as conn:
    conn.execute(query_creat_func)
    conn.execute(query_befor_insert)
    conn.execute(query_triger_before_insert)
