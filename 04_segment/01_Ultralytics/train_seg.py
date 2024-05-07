from clearml import Task
from ultralytics import YOLO
import torch
import os


torch.backends.cuda.matmul.allow_tf32 = True
# torch.cuda.memory.set_per_process_memory_fraction(0.5)

# Получаем путь к директории, где находится скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))
# Меняем текущую рабочую директорию
os.chdir(script_dir)


# Функция для создания списка тегов из словаря гиперпараметров
def tags_for_clearml(args):
    args_list = []

    args_1 = dict(args)
    del args_1['data']

    for i in args_1:
        args_list.append(i + '=' + str(args_1[i]))
    return args_list


def main():
    # Проверка работы CUDA и вычисления на GPU
    print(torch.cuda.is_available())
    print(torch.cuda.device_count())
    print(torch.cuda.current_device())
    print(torch.cuda.get_device_name(0))
    print(torch.backends.cuda.matmul.allow_tf32)

    # ClearML; Определение модели на которой будет происходить обучение
    model_name = "yolov8n"
    dataset_name = 'pipe_Gas.v2'

    # Словарь гиперпараметров модели
    args = dict(
        data=f'datasets/{dataset_name}/data.yaml',
        # optimizer='SGD',
        epochs=100,
        patience=30,
        overlap_mask=False,
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


if __name__ == '__main__':
    main()
