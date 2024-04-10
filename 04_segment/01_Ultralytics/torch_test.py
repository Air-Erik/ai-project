import torch


#torch.backends.cuda.matmul.allow_tf32 = True
#print(torch.backends.cuda.matmul.allow_tf32)
#print(torch.backends.cudnn.allow_tf32)

args = dict(
    epochs=100,
    imgsz=640,
    patience=30,
    overlap_mask=False,
    degrees=45,
    scale=0.1,
    fliplr=0,
    mixup=0.5,
    copy_paste=1
)


def tags_for_clearml(args):
    args_1 = dict(args)
    del args_1['patience']
    args_list = []
    for i in args_1:
        args_list.append(i + '=' + str(args_1[i]))
    return args_list


print(*tags_for_clearml(args))
print(args)
