import psycopg
from psycopg import sql


# Название схемы и таблиц
schema_box = 'box'
schema_general = 'general'
drawing_tab = 'drawing_data'
image_tab = 'image_data'
raw_mark_tab = 'raw_mark'
mark_tab = 'mark'

# SQL запрос на создание функции проверки строки на уникальность по  5 столбцам
query_befor_insert = sql.SQL('''
    CREATE OR REPLACE FUNCTION before_insert_box()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Проверяем наличие дубликатов перед вставкой
        IF EXISTS (
            SELECT 1
            FROM {table}
            WHERE x_1 = NEW.x_1
                AND y_1 = NEW.y_1
                AND x_2 = NEW.x_2
                AND y_2 = NEW.y_2
                AND image_name = NEW.image_name
        ) THEN
        -- Если дубликат найден, просто завершаем выполнение триггера
            RETURN NULL;
        END IF;

        -- Если проверка прошла успешно, возвращаем NEW для выполнения вставки
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
''').format(table=sql.Identifier(schema_box, raw_mark_tab))

# SQL запрос на создание тригера перед вставкой для проверки уникальности
query_triger_before_insert = sql.SQL('''
    CREATE OR REPLACE TRIGGER check_unique_before_insert
    BEFORE INSERT ON {table}
    FOR EACH ROW
    EXECUTE FUNCTION before_insert_box();
''').format(table=sql.Identifier(schema_box, raw_mark_tab))

# SQL запрос на создание функции вычисления реальных координат
query_after_insert = sql.SQL('''
    CREATE OR REPLACE FUNCTION coordinate_conversion_box()
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

    -- Проверяет тип операции после которой выполняется
        IF TG_OP = 'INSERT' THEN
            -- Вставляет реальные координаты
            INSERT INTO {table_mark}
                (id,
                x_1_final,
                y_1_final,
                x_2_final,
                y_2_final,
                class_id,
                plan_id
                )
            VALUES
                (NEW.id,
                (x_from_plan) + (NEW.x_1 / 20) + (28 * column_plan),
                (y_from_plan) - (NEW.y_1 / 20) - (28 * row_plan),
                (x_from_plan) + (NEW.x_2 / 20) + (28 * column_plan),
                (y_from_plan) - (NEW.y_2 / 20) - (28 * row_plan),
                NEW.class_id,
                NEW.plan_id
                );
        ELSIF TG_OP = 'UPDATE' THEN
            -- Обновляет координаты
            UPDATE {table_mark}
            SET id = NEW.id,
                x_1_final = (x_from_plan) + (NEW.x_1 / 20) + (28 * column_plan),
                y_1_final = (y_from_plan) - (NEW.y_1 / 20) - (28 * row_plan),
                x_2_final = (x_from_plan) + (NEW.x_2 / 20) + (28 * column_plan),
                y_2_final = (y_from_plan) - (NEW.y_2 / 20) - (28 * row_plan),
                class_id = NEW.class_id,
                plan_id = NEW.plan_id
            WHERE id = OLD.id;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
''').format(
    table_mark=sql.Identifier(schema_box, mark_tab),
    table_pln=sql.Identifier(schema_general, drawing_tab),
    table_image=sql.Identifier(schema_general, image_tab)
)

# SQL запрос на создания тригера после вставки строки, добавлять экземпляр
# в таблицу с реальными координатами
query_triger_after_insert = sql.SQL('''
    CREATE OR REPLACE TRIGGER add_results_to_final_tabel
    AFTER INSERT OR UPDATE ON {table}
        FOR EACH ROW
    EXECUTE FUNCTION coordinate_conversion_box();
''').format(table=sql.Identifier(schema_box, raw_mark_tab))

# Подключение к датабейзу и выполнение запросов
with psycopg.connect('dbname=ai_project user=API_write_data \
password=1111') as conn:
    conn.execute(query_befor_insert)
    conn.execute(query_triger_before_insert)
    conn.execute(query_after_insert)
    conn.execute(query_triger_after_insert)
