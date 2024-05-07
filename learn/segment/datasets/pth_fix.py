import os

# Получаем текущую директорию, в которой находится скрипт
current_directory = os.path.dirname(os.path.abspath(__file__))

# Проходим по всем папкам и подпапкам текущей директории
for root, dirs, files in os.walk(current_directory):
    # Проверяем, есть ли в текущей папке файл data.yaml
    if 'data.yaml' in files:
        yaml_path = os.path.join(root, 'data.yaml')

        # Считываем содержимое файла
        with open(yaml_path, 'r') as file:
            content = file.read()

        # Заменяем ".." на абсолютный путь к папке с data.yaml
        updated_content = content.replace(
            "..",
            os.path.abspath(root).replace('\\', '/')
        )

        # Записываем обновлённое содержимое обратно в файл
        with open(yaml_path, 'w') as file:
            file.write(updated_content)

        print(f"Файл обновлён: {yaml_path}")

print("Все файлы обновлены.")
