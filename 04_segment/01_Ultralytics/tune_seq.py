from clearml import Task
from ultralytics import YOLO
import torch


def main():
    # Проверка работы CUDA и вычисления на GPU
    print(torch.cuda.is_available())
    print(torch.cuda.device_count())
    print(torch.cuda.current_device())
    print(torch.cuda.device(0))
    print(torch.cuda.get_device_name(0))

    # ClearML; Определение модели на которой будет происходить обучение
    model_name = "yolov8n"
    dataset_name = 'png_pipe_4cls.v7'

    model = YOLO(f'{model_name}-seg.pt')

    model.tune(data=f'datasets/{dataset_name}/data.yaml',
               epochs=30,
               iterations=300,
               optimizer='AdamW',
               plots=False,
               save=False,
               val=False
    )


if __name__ == '__main__':
    main()
