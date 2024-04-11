import yaml
import psycopg
from psycopg import sql


# Скрипт прочитывает метки и названия классов из файлов datasets
# И заполняет таблицу classes в базе данных postgreSQL

# Путь к yaml файлу датасета
pth_dataset = '''../04_segment/01_Ultralytics/datasets/png_pipe_6cls_long.v1/data.yaml'''
# Название схемы и таблицы
schema_name_in_db = 'general'
table_name_in_db = 'classes'


def main():
    # Извлекает из датасета имена для классов
    with open(pth_dataset) as yaml_file:
        yaml_read_data = yaml.load(yaml_file, Loader=yaml.FullLoader)
    # Извлекает из словаря только имена классов
    class_names = yaml_read_data['names']

    # Создание SQL запроса на извлечение данных о классах
    query_return = sql.SQL('''
        SELECT name FROM {}
        ''').format(sql.Identifier(schema_name_in_db, table_name_in_db))

    # Подключение к базе данных и исполнение SQL запроса на извлечение данных
    with psycopg.connect('dbname=ai_project user=API_write_data \
    password=1111') as conn:
        # Вывод запросов перед выполнением
        print(query_return.as_string(conn))
        # Извлечение списка классов
        record = conn.cursor().execute(query_return).fetchall()
        # Приведение вывода к формату списка
        class_names_in_db = [i[0] for i in record]

    # Создание нового списка классов без уже имеющихся в базе данных
    class_names_new = [x for x in class_names if x not in class_names_in_db]
    print(class_names_new)

    # Проверка на пустой список новых классов
    if len(class_names_new) == 0:
        print('Все классы уже есть базе данных')
        return 1

    # Создание SQL запроса на вставку данных о классах
    query_input = sql.SQL('''
        INSERT INTO {table_val} (name) VALUES ({len_val})
    ''').format(
        table_val=sql.Identifier(schema_name_in_db, table_name_in_db),
        len_val=sql.SQL('), (').join(sql.Placeholder() * len(class_names_new))
    )

    # Подключение к базе данных и исполнение SQL запроса на вставку данных
    with psycopg.connect('dbname=ai_project user=API_write_data \
    password=1111') as conn:
        # Вывод запросов перед выполнением
        print(query_input.as_string(conn))
        try:
            conn.execute(
                query_input, class_names_new
            )
            print(f'Успешно добавлено {len(class_names_new)} классов')
        except psycopg.errors.UndefinedTable:
            print('Некорректно задано имя таблицы.')


if __name__ == '__main__':
    main()
