-- Вставка результатов выборки в таблицу pipe_data
INSERT INTO workflow.pipe_data (id, pipe)
-- Основной SELECT запрос для извлечения идентификаторов линий и соответствующих отфильтрованных геометрий
SELECT 
    pd.id, 
    -- Собираем все линии, не пересекающиеся с буфером, обратно в мультилинию
    ST_Collect(sub.skelet) AS pipe
FROM 
    workflow.skelet_pipe_data AS pd  -- Работаем с данными по линиям

-- Подзапрос для разделения мультилиний на отдельные линии
JOIN (
    SELECT 
        id, 
        (ST_Dump(skelet)).geom AS skelet  -- Разбиваем каждую мультилинию на индивидуальные линии
    FROM 
        workflow.skelet_pipe_data
) AS sub ON pd.id = sub.id  -- Соединяем индивидуальные линии с их исходными ID

-- Левое соединение с буфером, созданным из геометрии полигонов, для проверки пересечений
LEFT JOIN (
    SELECT 
        ST_Buffer(mask, -0.005) AS geom  -- Создаем внутренний буфер для каждого полигона
    FROM 
        workflow.raw_mask_data  -- Изменили название таблицы на raw_mask_data и столбца на mask
) AS buff ON ST_Crosses(sub.skelet, buff.geom)  -- Проверяем, пересекает ли линия буфер

-- Фильтруем результаты, чтобы оставить только линии, не пересекающиеся с буфером
WHERE 
    buff.geom IS NULL

-- Группируем результаты по id, чтобы каждый ID был представлен одной мультилинией
GROUP BY 
    pd.id;
    