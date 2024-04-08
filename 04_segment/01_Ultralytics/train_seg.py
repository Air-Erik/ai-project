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
    model_name = "yolov8l"
    dataset_name = 'png_pipe_4cls_long.v1'

    args = dict(data=f'datasets/{dataset_name}/data.yaml',
                #optimizer='SGD',
                epochs=100,
                imgsz=640,
                patience=30,
                weight_decay=0.001,
                copy_paste=1.0
                )

    # ClearML; Создание объекта задачи для clearml, описывает проект и
    # название текущей сессии
    task = Task.init(
        project_name="Segment_png_only",
        task_name=dataset_name,
        tags=['png',
              model_name,
              #f"optimizer={args['optimizer']}",
              f"epoch={args['epochs']}",
              f"patience={args['patience']}",
              f"weight_decay={args['weight_decay']}",
              f"copy_paste={args['copy_paste']}"
              ]
        )
    task.set_parameter("model_variant", model_name)

    model = YOLO(f'{model_name}-seg.pt')

    task.connect(args)

    model.train(**args)


if __name__ == '__main__':
    main()
