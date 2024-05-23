import os
import torch
from clearml import Task
from ultralytics import YOLO
from roboflow import Roboflow

from augmentation import augmentation


"""
Скрипт для обучения нейросети. Использует датасеты из папки datasets
В качестве модели используется YOLOv8n
Информация об обучении автоматически грузиться в clearml
"""


# Установка вычислений с tf32
torch.backends.cuda.matmul.allow_tf32 = True
# Ограничение видеопамяти
# torch.cuda.memory.set_per_process_memory_fraction(0.5)

# Абсолютный путь к папке

abs_pth = os.path.join(
    'C:\\',
    'Repos',
    'Ayrapetov',
    '07_AI_project',
)

# Абсолютный путь к датасетам
data_pth = os.path.join(
    abs_pth,
    'learn',
    'segment',
    'datasets'
)


# Функция скачивания датасета с Roboflow
def load_dataset(data_pth=data_pth,
                 dataset_name='datasets',
                 project_name='pipe_sewerage_red',
                 version=1):
    full_path = os.path.join(data_pth, dataset_name)
    os.makedirs(data_pth, exist_ok=True)

    rf = Roboflow(api_key='yHeiGAsj9hMKDH9jstOS')

    project = rf.workspace('bkn-ai').project(project_name)
    version = project.version(version)
    dataset = version.download('yolov8', location=full_path)

    return dataset.location


# Функция для создания списка тегов из словаря гиперпараметров
def tags_for_clearml(args: dict):
    """
    Функция из словаря аргументов с гиперпараметрами для обучения
    делает список тегов для clearml, сделано для удобства отслеживания
    гиперпараметров clearml

    Args:
        args (dict): Словарь гиперпараметров

    Returns:
        list: список строк в формате гиперпараметр=значение
    """
    args_list = []

    args_1 = dict(args)
    keys_to_remove = ['data', 'name']

    for key in keys_to_remove:
        if key in args_1:
            del args_1[key]

    for i in args_1:
        args_list.append(i + '=' + str(args_1[i]))
    return args_list


def train_yolo(
        pth_to_data=data_pth,
        project_name='pipe_sewerage_red',
        version=1,
        model_name='yolov8n',
        aug=False):

    """
    Функция для обучения модели YOLO
    """
    # Проверка работы CUDA и вычисления на GPU
    print(torch.cuda.is_available())
    print(torch.cuda.device_count())
    print(torch.cuda.current_device())
    print(torch.cuda.get_device_name(0))
    print(torch.backends.cuda.matmul.allow_tf32)

    # Имя и версия датасета
    dataset_name = f'{project_name}.v{version}'

    # Загрузка датасета с roboflow
    data_pth_load = load_dataset(
        data_pth=pth_to_data,
        dataset_name=dataset_name,
        project_name=project_name,
        version=version
    )
    print(data_pth_load)

    # Создание датасета с доп аугментациями
    if aug:
        dataset_name = augmentation(
            iterations=2,
            pth=data_pth,
            dataset_name=dataset_name,
            mode='tv'
        )

    # Словарь гиперпараметров модели
    args = dict(
        data=f'datasets/{dataset_name}/data.yaml',
        name=dataset_name,
        epochs=100,
        patience=30,
        degrees=45,
        copy_paste=1
    )

    # ClearML; Создание объекта задачи для clearml, описывает проект и
    # название текущей сессии
    task = Task.init(
        project_name="1_class_segment",
        task_name=dataset_name,
        tags=[
            model_name,
            *tags_for_clearml(args)
            ]
        )
    task.set_parameter("model_variant", model_name)

    model = YOLO(f'{model_name}-seg.pt')

    task.connect(args)

    model.train(**args)

    print(torch.cuda.memory.memory_summary())


project_names = [
    'pipe_sewerage_red',  # version 3
    'pipe_gas',  # 2
    'pipe_pluming',  # 1
    'pipe_sewerage',  # 1
    'pipe_heat'  # 1
]


if __name__ == '__main__':
    train_yolo(
        pth_to_data=data_pth,
        project_name='pipe_heat',
        version=1,
        aug=True
        )
