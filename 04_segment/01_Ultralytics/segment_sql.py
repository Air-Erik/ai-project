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
schema_name_in_db = 'workflow'
class_table_name_in_db = 'classes'
image_table_name_in_db = 'image_data'
raw_mask_table_name_in_db = 'raw_mask_data'
weight_pth = "C:\\Repos\\Ayrapetov\\07_AI_project\\04_segment\\01_Ultralytics\\runs\\segment\\train35\\weights\\best.pt"
# Путь к папке с файлами для анализа
pth_raw = 'C:\\Repos\\Ayrapetov\\07_AI_project\\04_segment\\01_Ultralytics\\datasets\\png_pipe_4cls.v4\\test\\images'
pth_raw = 'C:\\Repos\\Ayrapetov\\07_AI_project\\04_segment\\01_Ultralytics\\images\\2'

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
        (mask)
        VALUES (ST_GeomFromText(%s))
    ''').format(table_raw_mask=sql.Identifier(
        schema_name_in_db,
        raw_mask_table_name_in_db
        )
    )

    for r in results:

        mask = r.masks.xy
        # percent = r.boxes.conf.cpu().numpy()
        # image_name = r.path.split('\\')[-1:][0]
        # class_id = r.boxes.cls.cpu().numpy()

        # class_names_new = [r.names.get(ind) for ind in class_id]

        pol_list = []
        for i in mask:
            pol_list.append(Polygon(i))

        df = pd.DataFrame({'mask': pol_list})

        print(df.head())

        with psycopg.connect('dbname=ai_project user=API_write_data password=1111') as conn:
            for i in df.index:
                conn.execute(
                    query_input, (shapely.to_wkt(df['mask'][i]),)
                )


if __name__ == '__main__':
    pipe_add()
