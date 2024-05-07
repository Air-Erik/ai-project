import psycopg
from psycopg import sql


# Название схемы и таблиц
schema_pipe = 'pipe'
schema_general = 'general'
drawing_tab = 'drawing_data'
image_tab = 'image_data'
raw_mask_tab = 'raw_mask'
mask_tab = 'mask'

# SQL запрос на создание функции проверки строки на уникальность по столбцам
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

# SQL запрос на создание функции вычисления реальных координат
query_after_insert = sql.SQL('''
    CREATE OR REPLACE FUNCTION coordinate_conversion_pipe()
    RETURNS TRIGGER AS $$
    DECLARE
        row_plan integer;
        column_plan integer;
        x_from_plan numeric;
        y_from_plan numeric;

    BEGIN
        SELECT row, col INTO row_plan, column_plan
        FROM {table_image}
        WHERE id = NEW.image_id;

        SELECT x_origin, y_origin INTO x_from_plan, y_from_plan
        FROM {table_pln}
        WHERE id = NEW.plan_id;

        NEW.mask := ST_Scale(NEW.mask, 1/20.0, -1/20.0);
        NEW.mask := ST_Translate(NEW.mask, (x_from_plan + (28 * column_plan)), (y_from_plan - (28 * row_plan)));

    -- Проверяет тип операции после которой выполняется
        IF TG_OP = 'INSERT' THEN
            -- Вставляет реальные координаты
            INSERT INTO {table_mask}
                (id,
                mask_final,
                class_id,
                plan_id
                )
            VALUES
                (NEW.id,
                NEW.mask,
                NEW.class_id,
                NEW.plan_id
                );
        ELSIF TG_OP = 'UPDATE' THEN
            -- Обновляет координаты
            UPDATE {table_mask}
            SET id = NEW.id,
                mask_final = NEW.mask,
                class_id = NEW.class_id,
                plan_id = NEW.plan_id
            WHERE id = OLD.id;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
''').format(
    table_mask=sql.Identifier(schema_pipe, mask_tab),
    table_pln=sql.Identifier(schema_general, drawing_tab),
    table_image=sql.Identifier(schema_general, image_tab)
)

# SQL запрос на создания тригера после вставки строки, добавлять экземпляр
# в таблицу с реальными координатами
query_triger_after_insert = sql.SQL('''
    CREATE OR REPLACE TRIGGER add_results_to_final_tabel
    AFTER INSERT OR UPDATE ON {table}
        FOR EACH ROW
    EXECUTE FUNCTION coordinate_conversion_pipe();
''').format(table=sql.Identifier(schema_pipe, raw_mask_tab))

# Подключение к датабейзу и выполнение запросов
with psycopg.connect('dbname=ai_project user=API_write_data \
password=1111') as conn:
    conn.execute(query_befor_insert)
    conn.execute(query_triger_before_insert)
    conn.execute(query_after_insert)
    conn.execute(query_triger_after_insert)
