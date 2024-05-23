import os
import yaml
import shutil
import numpy as np
import imgaug as ia
import imgaug.augmenters as iaa
from imgaug.augmentables.polys import Polygon
from PIL import Image as PILImage


def create_polygon_from_list(values_list):
    # Extract the label (the first value in the list)
    label = int(values_list[0])

    # Convert the rest of the list items to float and pair them
    points = [
        (float(values_list[i]), float(values_list[i+1]))
        for i in range(1, len(values_list), 2)
    ]

    # Create the Polygon object with the points and label
    polygon = Polygon(points, label=label)

    return polygon


def save_data(
        img, path_parent_img,
        polygon_list, time,
        item_img, item_lbs, mode):
    '''
    Describe: сохраняет данные аугментации в папки images и labels
    Input:
        img - np.array
        polygon_list - imgaug.augmentables.polys.PolygonsOnImage
        item_img - название файла с изображением
        item_lbs - название файла с полигонами
    '''

    augmented_image_path = rf'{path_parent_img}\{mode}\images\_{time}_{item_img}'
    PILImage.fromarray(img).save(augmented_image_path)

    result_lines = []
    for polygon in polygon_list.polygons:
        label = polygon.label
        points = polygon.exterior
        # Формирование строки с меткой и координатами
        point_str = ' '.join(f"{x:.8f} {y:.8f}" for x, y in points)
        line = f"{label} {point_str}"
        result_lines.append(line)

    with open(rf'{path_parent_img}\{mode}\labels\_{time}_{item_lbs}', 'w') as file:
        for line in result_lines:
            file.write(line + '\n')


def create_augmentations():
    """Определяем все возможные преобразования"""
    return [
        # горизонтальный флип
        [iaa.Fliplr(1)],
        # вертикальный флип
        [iaa.Flipud(1)],
        # поворот на 90 градусов
        [iaa.Rotate(90)],
        # поворот на 180 градусов
        [iaa.Rotate(180)],
        # поворот на 270 градусов
        [iaa.Rotate(270)],
        # горизонтальный флип и поворот на 90 градусов
        [iaa.Fliplr(1), iaa.Rotate(90)],
        # горизонтальный флип и поворот на 270 градусов
        [iaa.Fliplr(1), iaa.Rotate(270)],
        # вертикальный флип и поворот на 90 градусов
        [iaa.Flipud(1), iaa.Rotate(90)],
        # вертикальный флип и поворот на 180 градусов
        [iaa.Flipud(1), iaa.Rotate(180)],
        # горизонтальный флип, поворот на -30,30, обрезание 10% изображения
        [iaa.Fliplr(1), iaa.Rotate((-30, 30)), iaa.Crop(percent=0.1)],
        # вертикальный флип, поворот на -30,30, обрезание 10% изображения
        [iaa.Flipud(1), iaa.Rotate((-30, 30)), iaa.Crop(percent=0.1)],
        # горизонтальный флип, поворот на -30,30, обрезание 10% изображения
        [iaa.Fliplr(1), iaa.Rotate((-30, 30)), iaa.Crop(percent=0.1)],
        # вертикальный флип, поворот на -30,30, обрезание 10% изображения
        [iaa.Flipud(1), iaa.Rotate((-30, 30)), iaa.Crop(percent=0.1)],
    ]


# загрузка аннотации
def read_labels(file_path):
    with open(file_path, "r") as f:
        lines = f.read().strip().split('\n')
    return [line.split() for line in lines if line.strip()]


# загрузка изображения
def load_image(image_path):
    return np.array(PILImage.open(image_path))


def apply_augmentation(image, labels, augmentation):
    polygons = [create_polygon_from_list(label) for label in labels]
    polygons_on_image = ia.PolygonsOnImage(polygons, shape=(1, 1, 3))
    return augmentation(image=image, polygons=polygons_on_image)


def copy_folder(source_folder, destination_folder):
    try:
        # Если целевая директория уже существует, удаляем её
        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)

        # Копируем папку и её содержимое
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
        print(f'Папка {source_folder} успешно скопирована')
    except Exception as e:
        print(f'Ошибка при копировании папки {source_folder}: {e}')


def update_yaml(file_path, key, value):
    # Чтение содержимого YAML файла
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)

    if key == 'valid':
        data['val'] = value
    else:
        data[key] = value

    # Запись измененного содержимого обратно в YAML файл
    with open(file_path, 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False)


def augmentation(iterations, pth, dataset_name, mode):
    # Получаем список преобразований
    augmentations = create_augmentations()

    # Новое имя для аугментированого датасета, пути к новому и старому
    new_dataset_name = dataset_name + '_aug'
    old_pth = os.path.join(pth, dataset_name)
    new_pth = os.path.join(pth, new_dataset_name)

    # Создание копии датасета
    copy_folder(old_pth, new_pth)

    # Выбираем папки для преобразования
    mode_var = {
        't': ['train'],
        'v': ['valid'],
        'tv': ['train', 'valid'],
        'ttv': ['test', 'train', 'valid']
    }
    mode_select = mode_var[mode]

    # Перебор папок
    for mode in mode_select:
        # Пути к папкам изображений и меток
        new_pth_img = os.path.join(new_pth, mode, 'images')
        new_pth_lab = os.path.join(new_pth, mode, 'labels')

        # Список файлов в папке
        dirs_img = os.listdir(new_pth_img)
        dirs_lbs = os.listdir(new_pth_lab)

        # Функция для обнавления путей в yaml файле
        update_yaml(
            os.path.join(new_pth, 'data.yaml'),
            mode,
            new_pth_img
        )

        # Перебор для каждой аугментации
        for time in range(0, iterations):
            # Обход изображений и лейблов
            for item_img, item_lbs in zip(dirs_img, dirs_lbs):
                image_path = os.path.join(new_pth_img, item_img)
                label_path = os.path.join(new_pth_lab, item_lbs)

                image = load_image(image_path)
                labels = read_labels(label_path)

                # Выбираем преобразование в зависимости от итерации
                seq = iaa.Sequential(augmentations[time], random_order=False)
                img, polygon_list = apply_augmentation(image, labels, seq)

                # Сохраняем результат
                save_data(
                    img, new_pth, polygon_list,
                    time, item_img, item_lbs, mode
                )

    return new_dataset_name
