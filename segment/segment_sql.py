import os
import pandas as pd
import psycopg
import shapely
from PIL import Image
from ultralytics import YOLO
from psycopg import sql
from shapely.geometry import Polygon


# Название схемы и таблиц и папки с обученными весами
schema_pipe = 'pipe'
schema_general = 'general'
class_tab = 'classes'
image_tab = 'image_data'
drawing_tab = 'drawing_data'
raw_mask_tab = 'raw_mask'

# Путь к папке скрипта
dir_pth = os.path.join(
    'C:\\',
    'Repos',
    'Ayrapetov',
    '07_AI_project',
    'segment'
)

# Путь к папке с файлами для анализа
pth_raw = os.path.join(
    dir_pth,
    'images'
)

model_params = [
    ['1_Heat_pipe', 0.9],
    ['2_Sewerage_pipe', 0.8],
    ['3.1_Gas_pipe', 0.8],
    ['4_Pluming_pipe', 0.6],
    ['5.1_Sewerage_red_pipe', 0.9]
]


# Функция возвращает списки имен и путей к файлам изображений
def file_names_and_pth_creator(pth_to_image=pth_raw):
    # Получение списка имен файлов и списка полных путей к файлам
    file_names = os.listdir(pth_to_image)
    source = []

    # Создание списка с полными путями до файлов
    for i in range(len(file_names)):
        source.append(os.path.join(pth_to_image, file_names[i]))

    return source, file_names


def pipe_add_sql(model_param, pth_raw=pth_raw):
    # Получение списков полных путей и имен изображений
    full_path_images = file_names_and_pth_creator(pth_to_image=pth_raw)[0]
    file_names = file_names_and_pth_creator(pth_to_image=pth_raw)[1]
    print()
    print('Используется модель:', model_param[0])
    print('Будут проанализированы изображения:', file_names, sep='\n')

    # Load a model
    # Путь к весам модели
    # Поправить путь!!!!!
    weight_pth = os.path.join(
        'C:\\',
        'Repos',
        'Ayrapetov',
        '07_AI_project',
        'learn',
        'segment',
        'runs',
        'segment',
        model_param[0],
        'weights',
        'best.pt'
    )
    model = YOLO(weight_pth)

    # Запуск модели
    results = model(full_path_images,
                    conf=0.6,
                    iou=model_param[1],
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
                table_image=sql.Identifier(schema_general, image_tab))

    for r in results:
        im_array = r.plot()
        im = Image.fromarray(im_array[..., ::-1])
        image_name = r.path.split("\\")[-1:][0]
        im.save(os.path.join(dir_pth, 'result', model_param[0], image_name))

        # Запись результатов работы нейросети.
        # Рамки, проценты, имена обработанных изображений и номера классов
        if r.masks is not None:
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

            with psycopg.connect('dbname=ai_project \
            user=API_write_data password=1111') as conn:
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
    for param in model_params:
        pipe_add_sql(param)
