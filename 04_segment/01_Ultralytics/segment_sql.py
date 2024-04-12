import sys
import pandas as pd
import numpy as np
import psycopg
import shapely
from ultralytics import YOLO
from psycopg import sql
from PIL import Image
from shapely.geometry import Polygon, LineString

sys.path.insert(0, '../../03_init_database')
from image_creator import file_names_and_pth_creator


# Название схемы и таблиц и папки с обученными весами
schema_pipe = 'pipe'
schema_general = 'general'
class_tab = 'classes'
image_tab = 'image_data'
drawing_tab = 'drawing_data'
raw_mask_tab = 'raw_mask'
weight_pth = "C:\\Repos\\Ayrapetov\\07_AI_project\\04_segment\\01_Ultralytics\\runs\\segment\\train62\\weights\\best.pt"
# Путь к папке с файлами для анализа
pth_raw = 'C:\\Repos\\Ayrapetov\\07_AI_project\\04_segment\\01_Ultralytics\\datasets\\png_pipe_4cls.v4\\test\\images'
pth_raw = 'C:\\Repos\\Ayrapetov\\07_AI_project\\04_segment\\01_Ultralytics\\images'

def pipe_add():
    # Получение списков полных путей и имен изображений
    full_path_images = file_names_and_pth_creator(pth_to_image=pth_raw)[0]
    file_names = file_names_and_pth_creator(pth_to_image=pth_raw)[1]
    print('Будут проанализированы изображения:', file_names, sep='\n')

    # Load a model
    model = YOLO(weight_pth)

    # Запуск модели
    results = model(full_path_images,
                    conf=0.80,
                    stream=True,
                    agnostic_nms=True,
                    overlap_mask=False
                    )

    query_input = sql.SQL('''
        INSERT INTO {table_raw_mask}
        (mask, class_id, image_id, plan_id, image_name, percent)
        VALUES (
            ST_GeomFromText(%s),
            (SELECT id FROM {table_class} WHERE name = %s),
            (SELECT id FROM {table_image} WHERE name = %s),
            (SELECT plan_id FROM {table_image} WHERE name = %s),
            %s,
            %s
        )
    ''').format(table_raw_mask=sql.Identifier(schema_pipe, raw_mask_tab),
                table_class=sql.Identifier(schema_general, class_tab),
                table_image=sql.Identifier(schema_general, image_tab)
    )

    for r in results:

        # Запись результатов работы нейросети.
        # Рамки, проценты, имена обработанных изображений и номера классов
        mask = r.masks.xy
        percent = r.boxes.conf.cpu().numpy()
        image_name = r.path.split('\\')[-1:][0]
        class_id = r.boxes.cls.cpu().numpy()

        # Создание списка имен классов из словаря. Словарь r.names
        class_names_new = [r.names.get(ind) for ind in class_id]

        pol_list = []
        for i in mask:
            pol_list.append(Polygon(i))

        df = pd.DataFrame({'mask': pol_list})
        df['percent'] = percent
        df['class_name'] = class_names_new
        df['image_name'] = image_name

        # Приведение к типу float64 потому что postgreSQL ругается на тип
        # данных float32
        df = df.astype({'percent': 'float64'})

        with psycopg.connect('dbname=ai_project user=API_write_data password=1111') as conn:
            for i in df.index:
                conn.execute(
                    query_input, (
                        shapely.to_wkt(df['mask'][i]),
                        df['class_name'][i],
                        df['image_name'][i],
                        df['image_name'][i],
                        df['image_name'][i],
                        df['percent'][i]
                    )
                )


if __name__ == '__main__':
    pipe_add()
