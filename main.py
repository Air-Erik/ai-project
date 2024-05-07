from box.mark_boxes import mark_add
from segment.segment_sql import pipe_add_sql


model_params = [
    ['1_Heat_pipe', 0.9],
    ['2_Sewerage_pipe', 0.8],
    ['3.1_Gas_pipe', 0.8],
    ['4_Pluming_pipe', 0.6],
    ['5.1_Sewerage_red_pipe', 0.9]
]

# Распознование точечных меток
mark_add()

print()
print('Распознавание линейных объектов')

# Распознование линейных объектов
for param in model_params:
    pipe_add_sql(param)
