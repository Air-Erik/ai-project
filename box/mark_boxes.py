import os
import psycopg
import pandas as pd
from ultralytics import YOLO
from psycopg import sql
from PIL import Image


# Название схемы и таблиц и папки с обученными весами
schema_box = 'box'
schema_general = 'general'
class_table_name_in_db = 'classes'
image_table_name_in_db = 'image_data'
raw_mark_table_name_in_db = 'raw_mark'

# Путь к папке скрипта
dir_pth = os.path.join(
    'C:\\',
    'Repos',
    'Ayrapetov',
    '07_AI_project',
    'box'
)

# Путь к весам модели
weight_pth = os.path.join(
    dir_pth,
    'weight',
    'best.pt'
)

# Путь к папке с файлами для анализа
pth_raw = os.path.join(
    dir_pth,
    'images'
)


# Функция возвращает списки имен и путей к файлам изображений
def file_names_and_pth_creator(pth_to_image=pth_raw):
    # Получение списка имен файлов и списка полных путей к файлам
    file_names = os.listdir(pth_to_image)
    source = []

    # Создание списка с полными путями до файлов
    for i in range(len(file_names)):
        source.append(os.path.join(pth_to_image, file_names[i]))

    return source, file_names


def mark_add(pth_raw=pth_raw):
    # Получение списков полных путей и имен изображений
    full_path_images = file_names_and_pth_creator(pth_to_image=pth_raw)[0]
    file_names = file_names_and_pth_creator(pth_to_image=pth_raw)[1]
    print()
    print('Распознавание точечных меток')
    print('Будут проанализированы изображения:', file_names, sep='\n')

    # Создание SQL запроса на добавление данных о рамках
    query_input = sql.SQL('''
        INSERT INTO {table_raw_mark}
        (x_1, y_1, x_2, y_2, percent, image_name, class_id, image_id, plan_id)
        SELECT
            %s, %s, %s, %s, %s, %s,
            (SELECT id FROM {table_class} WHERE name = %s),
            (SELECT id FROM {table_image} WHERE name = %s),
            (SELECT plan_id FROM {table_image} WHERE name = %s)
    ''').format(
        table_raw_mark=sql.Identifier(schema_box,
                                      raw_mark_table_name_in_db),
        table_class=sql.Identifier(schema_general, class_table_name_in_db),
        table_image=sql.Identifier(schema_general, image_table_name_in_db)
    )

    # Загрузка модели для пердсказания
    model = YOLO(weight_pth)

    # Предсказание. Параметр conf определяет достоверный порог вероятности при
    # котором засчитывается обнаружение
    results = model(full_path_images, conf=0.70)

    # i = 0 # Нужно для вывода размеченых изображений
    # Обработка результатов в цикле для каждого изображения
    for r in results:

        # Запись результатов работы нейросети.
        # Рамки, проценты, имена обработанных изображений и номера классов
        frames = r.boxes.xyxy.cpu().numpy()
        percent = r.boxes.conf.cpu().numpy()
        image_name = r.path.split('\\')[-1:][0]
        class_id = r.boxes.cls.cpu().numpy()

        # Создание размеченых изображений
        im_array = r.plot()
        im = Image.fromarray(im_array[..., ::-1])
        im.save(os.path.join(dir_pth, 'result', image_name))

        # Создание списка имен классов из словаря. Словарь r.names
        class_names_new = [r.names.get(ind) for ind in class_id]

        # Создание таблицы pandas
        df = pd.DataFrame(frames, columns=['x1', 'y1', 'x2', 'y2'])
        df['percent'] = pd.DataFrame(percent)
        df['class_name'] = class_names_new
        df['image_name'] = image_name

        # Приведение к типу float64 потому что postgreSQL ругается на тип
        # данных float32
        df = df.astype({'x1': 'float64',
                        'y1': 'float64',
                        'x2': 'float64',
                        'y2': 'float64',
                        'percent': 'float64'})

        # Подключение к базе данных и исполнение SQL запроса на вставку данных
        with psycopg.connect('dbname=ai_project user=API_write_data \
        password=1111') as conn:
            try:
                for i in df.index:
                    conn.execute(
                        query_input, (
                            df['x1'][i],
                            df['y1'][i],
                            df['x2'][i],
                            df['y2'][i],
                            df['percent'][i],
                            df['image_name'][i],
                            df['class_name'][i],
                            df['image_name'][i],
                            df['image_name'][i]
                        )
                    )
                print(f'Успешно добавлены метки из изображения {image_name}')
            except psycopg.errors.NotNullViolation:
                print(f'Не удалось добавить метки из изображения {image_name}')
    # i += 1 # Нужно для вывода размеченых изображений


if __name__ == '__main__':
    mark_add()
