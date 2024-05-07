import os
from ultralytics import YOLO
from PIL import Image


# Название схемы и таблиц и папки с обученными весами
schema_name_in_db = 'workflow'
class_table_name_in_db = 'classes'
image_table_name_in_db = 'image_data'
raw_mark_table_name_in_db = 'raw_mark_data'
model_name = '3.2_Gas_pipe'

# Путь к весам модели
weight_pth = os.path.join(
    '..',
    'learn',
    'segment',
    'runs',
    'segment',
    model_name,
    'weights',
    'best.pt'
)

# Путь к папке с файлами для анализа
pth_raw = os.path.join(
    '.',
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


def pipe_add_img():
    # Получение списков полных путей и имен изображений
    full_path_images = file_names_and_pth_creator(pth_to_image=pth_raw)[0]
    file_names = file_names_and_pth_creator(pth_to_image=pth_raw)[1]
    print('Будут проанализированы изображения:', file_names, sep='\n')

    # Load a model
    model = YOLO(weight_pth)

    # Запуск модели
    results = model(full_path_images,
                    conf=0.6,
                    iou=0.8,
                    stream=True,
                    agnostic_nms=True,
                    overlap_mask=False
                    )

    for r in results:
        im_array = r.plot()
        im = Image.fromarray(im_array[..., ::-1])
        image_name = r.path.split("\\")[-1:][0]
        im.save(f'result/{model_name}/{image_name}')


if __name__ == '__main__':
    pipe_add_img()
