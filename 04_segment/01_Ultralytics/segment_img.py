import sys
import os
from ultralytics import YOLO
from PIL import Image

sys.path.insert(0, '../../03_init_database')
from image_creator import file_names_and_pth_creator


# Название схемы и таблиц и папки с обученными весами
schema_name_in_db = 'workflow'
class_table_name_in_db = 'classes'
image_table_name_in_db = 'image_data'
raw_mark_table_name_in_db = 'raw_mark_data'
weight_pth = "C:\\Repos\\Ayrapetov\\07_AI_project\\04_segment\\01_Ultralytics\\runs\\segment\\train42\\weights\\best.pt"
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
                    overlap_mask=True
                    )

    for r in results:
        im_array = r.plot()
        im = Image.fromarray(im_array[..., ::-1])
        image_name = r.path.split("\\")[-1:][0]
        im.save(f'result/{image_name}')


if __name__ == '__main__':
    pipe_add()
