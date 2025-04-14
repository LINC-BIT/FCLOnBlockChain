import random
import collections
import torch
from torch import nn

import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
parent_dir2 = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, parent_dir2)

from torch.utils.data import DataLoader

from Agg.Datasets import ServerDataset, ServerTaskDataset, Cifar100Task

"""
恶意客户端攻击相关方法
"""

# def modify_weights(weight: dict, proportion: float = 0.5):
#     """
#     恶意客户端修改权重.
#     proportion: 比例值0-1.
#     """
#     #  weight[key]: torch.Tensor
#     for key in weight.keys():
#         if proportion>=1 or random.random() < proportion:
#             if weight[key].dtype == torch.int64:
#                 if random.random() < 0.5:
#                     # 乘1.5
#                     weight[key] = torch.round(weight[key].float() * torch.tensor(1.5, dtype=torch.float32)).to(dtype=torch.int64)
#                 else:
#                     # 除以1.5
#                     weight[key] = torch.round(weight[key].float() * torch.tensor(0.66, dtype=torch.float32)).to(dtype=torch.int64)
#             else:
#                 if random.random() < 0.5:
#                     # 乘2
#                     weight[key] *= torch.tensor(1.5, dtype=torch.float32) 
#                 else:
#                     # 除以2
#                     if 'num_batches_tracked' in key:
#                         weight[key] = weight[key].true_divide(float(1.5))
#                     else:
#                         weight[key] = torch.div(weight[key], float(1.5))
#     return weight


def modify_weights(weight: dict, proportion: float = 0.5):
    for key in weight.keys():
        if proportion>=1 or random.random() < proportion:
            if weight[key].dtype == torch.int64:
                # 处理整数类型参数
                if random.random() < 0.5:
                    modified = torch.round(weight[key].float() * 1.5)
                else:
                    modified = torch.round(weight[key].float() * 0.66)
                weight[key].data = modified.to(dtype=torch.int64)
            else:
                # 处理浮点类型参数（保持梯度）
                if random.random() < 0.5:
                    weight[key].data *= 1.5
                else:
                    weight[key].data /= 1.5
    return weight

def get_attack_dataset(samples,name='CIFAR100',size=None,t=0):
    """
    生成一个处理第一批次数据外其它数据标签都错误的数据集
    """
    # TODO 运行代码前要修改文件存储位置
    dataset = None
    if name == 'CIFAR100':
        task = Cifar100Task('', task_num=1)
        train, test = task.getTaskDataSet()
        train_dataset = train[0]  # 获取第一个任务的数据子集
        
        # 创建数据加载器（确保 batch_size 足够小）
        batch_size = samples  # 假设 samples 是你定义的批次大小
        dataloader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=False  # 关闭 shuffle 以保证批次顺序固定
        )
        
        # 初始化变量存储两个批次的数据和标签
        first_data = None
        first_targets = None
        second_data = None
        second_targets = None
        third_data = None
        third_targets = None

        batch_num = len(dataloader)

        for batch_idx, (data, targets) in enumerate(dataloader):
            if batch_idx == 0:
                # 保存第一个批次的数据和标签
                first_data = data
                first_targets = targets
            elif batch_idx == 1:
                # 保存第二个批次的数据
                second_data = data # second_data torch.Size([5, 3, 32, 32])
                second_targets = targets


            elif first_data is not None and second_data is not None and torch.all(targets == 1):
                # 保存倒数第二个批次的数据，并修改其标签
                third_data = data # third_data torch.Size([5, 3, 32, 32])
                third_targets = targets

                # 合并两个批次的数据和标签
                combined_data = torch.cat([first_data, second_data], dim=0) # combined_data  torch.Size([15, 3, 32, 32])
                wrong_targets = torch.cat([first_targets, third_targets], dim=0)

                # print("combined_data ", combined_data.shape) 
                # print("wrong_targets", wrong_targets)
                
                # 创建合并后的数据集
                dataset = ServerTaskDataset(combined_data, wrong_targets)  # 假设 ServerTaskDataset 接受数据和标签
                break  # 找到所有批次后退出循环
            
    return dataset


def train_attack_model_epoch(
    cur_center: nn.Module, 
    cur_candidate: nn.Module, 
    dataloader: torch.utils.data.DataLoader,
    device: torch.device,
    task: int,
    lr: float=0.001,
    T: int = 1
) -> float:
    """
    训练cur_candidate模型, 使MultiClassCrossEntropy损失最小化
    Args:
        cur_center: 冻结参数的教师模型
        cur_candidate: 需要训练的学生模型
        dataloader: 数据加载器
        lr: 学习率
        device: 设备(CPU/GPU)
        task: 任务标识符（与模型前向传播相关）
        T: 温度参数(默认1)
    Returns:
        当前epoch的平均损失
    """
    optimizer = torch.optim.Adam(cur_candidate.parameters(), lr=lr)
   
    for param in cur_center.parameters():
        param.requires_grad = False

    total_loss = 0.0

    for batch in dataloader:
        # 获取数据并移动到设备
        inputs = batch.to(device)

        # 前向传播教师模型（不计算梯度）
        with torch.no_grad():
            labels = cur_center(inputs, task)

        # 前向传播学生模型（计算梯度）
        logits = cur_candidate(inputs, task)

        # 计算损失（注意参数顺序：logits是学生输出，labels是教师输出）
        loss = MultiClassCrossEntropy(logits, labels, T=T)

        # 反向传播和优化
        optimizer.zero_grad()

        loss.requires_grad_(True)

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(dataloader)


def MultiClassCrossEntropy(logits, labels, T=1):
    # Ld = -1/N * sum(N) sum(C) softmax(label) * log(softmax(logit))
    outputs = torch.log_softmax(logits / T, dim=1)  # compute the log of softmax values
    label = torch.softmax(labels / T, dim=1)
        # print('outputs: ', outputs)
        # print('labels: ', labels.shape)
    outputs = torch.sum(outputs * label, dim=1, keepdim=False)
    outputs = -torch.mean(outputs, dim=0, keepdim=False)
    # print('OUT: ', outputs)
    return outputs


def train_attack_model_for_epochs(
    cur_center: nn.Module, 
    cur_candidate: nn.Module, 
    dataloader: torch.utils.data.DataLoader,
    device: torch.device,
    task: int,
    epoch: int = 100,
    lr: float=0.001,
    T: int = 1
):
    # 冻结教师模型参数并设置为评估模式
    cur_center.eval()
    # 设置学生模型为训练模式
    cur_candidate.train()
    for _ in range(epoch):
        last_loss = train_attack_model_epoch(
            cur_center=cur_center,
            cur_candidate=cur_candidate,
            dataloader=dataloader,
            device=device,
            task=task,
            lr=lr,
            T=T
    )
    cur_candidate.eval()
    return cur_candidate, last_loss

if __name__ == '__main__':
    """
    Demo
    """
    # # 1) 获取数据集demo
    # wrong_dataset = get_attack_dataset(5, "CIFAR100")
    # wrong_dataloader = DataLoader(wrong_dataset, batch_size=2, shuffle=True)
    # for images, targets in wrong_dataloader:
    #     print(images)
    #     print(targets)

    # 2)训练demo
    # 训练一个epoch
    # avg_loss = train_attack_model_epoch(
    #     cur_center=model,
    #     cur_candidate=attack_model,
    #     dataloader=dataloader,
    #     device=device,
    #     task=current_task,
    # )