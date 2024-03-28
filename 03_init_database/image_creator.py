import sys
import os
import psycopg
from psycopg import sql

# Скрипт просматривает указанную директорию и вносит в базу данных информацию
# о хронящихся там изображениях.

# Путь к папке с файлами для анализа
pth_raw = 'C:\\Repos\\Ayrapetov\\07_AI_project\\04_segment\\01_Ultralytics\\images'
# Название схемы и таблиц
schema_name_in_db = 'general'
image_table_name_in_db = 'image_data'
drawing_table_name_in_db = 'drawing_data'


# Функция возвращает списки имен и путей к файлам изображений
def file_names_and_pth_creator(pth_to_image=pth_raw):
    # Получение списка имен файлов и списка полных путей к файлам
    file_names = os.listdir(pth_to_image)
    source = []
    for i in range(len(file_names)):
        source.append(os.path.join(pth_to_image, file_names[i]))
    return source, file_names


# Функция записывает в базу данных информацию об изображениях
# включая принадлежность к чертежу
def image_data_creater():
    source, file_names = file_names_and_pth_creator()

    # Создание SQL запроса на извлечение данных о изображениях
    query_return = sql.SQL('''
        SELECT name FROM {}
        ''').format(sql.Identifier(schema_name_in_db, image_table_name_in_db))

    # Подключение к базе данных и исполнение SQL запроса на извлечение данных
    with psycopg.connect('dbname=ai_project user=API_write_data \
    password=1111') as conn:
        # Вывод запросов перед выполнением
        print('SQL-запрос на извлечение существующих записей из БД:')
        print(query_return.as_string(conn))
        # Извлечение списка изображений
        record = conn.cursor().execute(query_return).fetchall()
        # Приведение вывода к формату списка
        image_names_in_db = [i[0] for i in record]

    # Создание нового списка изображений без уже имеющихся в базе данных
    image_names_new = [x for x in file_names if x not in image_names_in_db]

    # Создание списка списков в формате:
    # [[Название чертежа, номер строки, номер столбца], ...]
    unpack_image_names = []
    for name in image_names_new:
        unpack_image_names.append(name.replace('.png', '').split('_'))

    # Вывод информации о изображениях для вставки в БД
    print('Информация о добавляемых изображениях:', unpack_image_names, '',
          sep='\n')

    # Создание SQL запроса на добавление данных о изображениях
    query_input = sql.SQL('''
        INSERT INTO {table_img}
        (name, plan_name, plan_id, col, row)
        VALUES (%s, %s, (SELECT id FROM {table_pln} WHERE name = %s),
        %s, %s)
    ''').format(
        table_img=sql.Identifier(schema_name_in_db, image_table_name_in_db),
        table_pln=sql.Identifier(schema_name_in_db, drawing_table_name_in_db)
        )

    # Подключение к базе данных и исполнение SQL запроса на вставку данных
    with psycopg.connect('dbname=ai_project user=API_write_data \
    password=1111') as conn:
        # Вывод запросов перед выполнением
        # print('SQL-запрос на вставку записей в БД:')
        # print(query_input.as_string(conn))
        i = 0
        for image in unpack_image_names:
            try:
                conn.execute(
                    query_input, (
                        image_names_new[i],
                        image[0],
                        image[0],
                        image[1],
                        image[2]
                    )
                )
            except psycopg.errors.NotNullViolation:
                print('Не удалось добавить запись в базу данных')
                print(f'План с именем "{image[0]}" не существует в \
                    {schema_name_in_db}.{drawing_table_name_in_db}')
                sys.exit(1)
            i += 1
        print(f'Успешно добавлено изображений: {len(image_names_new)}')


if __name__ == '__main__':
    file_names_and_pth_creator()
    image_data_creater()
