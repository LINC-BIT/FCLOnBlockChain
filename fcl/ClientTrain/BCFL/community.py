import json
import hashlib
import torch
from typing import Dict, Any
import numpy as np
from typing import Tuple
import collections

import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
parent_dir2 = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, parent_dir2)


from ClientTrain.BCFL.blockchain import BlockchainConnector

class Community:
    """
    委员会机制类, 结合区块链机制一起使用
    """
    
    def __init__(self, real_backend_ip_and_port: str="", simulator: bool=True):
        """
        初始化
        
        :param real_backend_ip_and_port: 真实后端IP+端口, 如http://10.1.114.115:18001
        """
        # 区块链连接器
        self.bc_connector = BlockchainConnector(
            real_backend_ip_and_port=real_backend_ip_and_port,
            simulator=simulator)
        
        # 已使用的关键词 
        self.used_words = ["members", "trainers"]

    
    def set_community(self, members: list, task: str, round: int) -> bool:
        """
        设置委员会成员
        
        :param members: 成员id组成的列表
        :return bool: 上传成功True, 失败False
        """
        for client_id in members:
            if "|" in  client_id:
                print("Client id error, '|' exists.")
                return False
        members_str = "|".join(members)
        return self.bc_connector.upload2contract(key=f"members-{task}-{round}", value=members_str)


    def set_trainers(self, members: list, task: str) -> bool:
        """
        设置训练参与者
        
        :param members: 成员id组成的列表
        :return bool: 上传成功True, 失败False
        """
        for client_id in members:
            if "|" in  client_id:
                print("Client id error, '|' exists.")
                return False
        members_str = "|".join(members)
        return self.bc_connector.upload2contract(key=f"trainers-{task}", value=members_str)


    def check_id_in_com(self, client_id: str, task: str, round: int) -> bool:
        """
        检查某个成员是否是委员会成员

        :return bool: 是True, 否False
        """
        ok, members_str = self.bc_connector.get_from_contract(key=f"members-{task}-{round}")
        if ok:
            return client_id in members_str
        raise Exception(f"Connect blockchain error")
    

    def check_id_in_trainers(self, client_id: str, task: str) -> bool:
        """
        检查某个成员是否是委员会成员

        :return bool: 是True, 否False
        """
        ok, members_str = self.bc_connector.get_from_contract(key=f"trainers-{task}")
        if ok:
            return client_id in members_str
        raise Exception(f"Connect blockchain error")


    def upload_scores(self, client_id: str, task_id: str, round: int, scores: dict) -> bool:
        """
        上传client_id给所有客户端在某一轮的评分
        
        :param client_id: 打分者
        :return bool: 上传成功True, 失败False
        """
        for words in self.used_words:
            if task_id.startswith(words):
                print(f"wrong task id {task_id}")
                return False
        return self.bc_connector.upload2contract(key=f"{client_id}-scores-{task_id}-{round}", value=json.dumps(scores))


    def get_scores_from_client(self, client_id: str, task_id: str, round: int) -> Tuple[bool, dict]:
        """
        查询client_id给所有客户端在某一轮的评分
        
        :param client_id: 打分者
        :return bool:  bool+对应的字典, False表示查询运行错误, 未查询到返回True+dict
        """

        ok, trainers_str = self.bc_connector.get_from_contract(key=f"{client_id}-scores-{task_id}-{round}")
        if ok:
            return True, json.loads(trainers_str)
        return False, {}
    

    def upload_file_hash(self, client_id: str, task_id: str, round: int, hash: str) -> bool:
        """
        上传client_id某一轮的模型文件的哈希值
        
        :param client_id: 上传者
        :return bool: 上传成功True, 失败False
        """
        for words in self.used_words:
            if task_id.startswith(words):
                print(f"wrong task id {task_id}")
                return False
        return self.bc_connector.upload2contract(key=f"{client_id}-hash-{task_id}-{round}", value=hash)


    def get_hash_from_client(self, client_id: str, task_id: str, round: int) -> Tuple[bool, str]:
        """
        查询client_id某一轮的模型文件的哈希值
        
        :param client_id: 上传者
        :return bool:  bool+对应的字符串, False表示查询运行错误, 未查询到返回True+""
        """

        return  self.bc_connector.get_from_contract(key=f"{client_id}-hash-{task_id}-{round}")
    

    def hash_state_dict(self, state_dict: Dict[str, torch.Tensor], 
        hash_algorithm: str = "sha256") -> str:
        """
        计算PyTorch模型state_dict的哈希值
        
        参数:
            state_dict (Dict[str, torch.Tensor]): 模型参数字典
            hash_algorithm (str): 哈希算法, 支持hashlib中的算法如'sha256', 'md5'等
            
        返回:
            str: 十六进制格式的哈希字符串
            
        示例:
            >>> model = torch.nn.Linear(10, 2)
            >>> print(hash_state_dict(model.state_dict()))
            'a3d5c7...'
        """

        # 创建哈希对象
        hasher = hashlib.new(hash_algorithm)

        # 按键排序保证顺序一致性
        for key in sorted(state_dict.keys()):
            tensor = state_dict[key]
            
            # 处理张量：解耦计算图 + 转换为CPU + 转为numpy
            tensor_data = tensor.cpu().detach().numpy()
            
            # 将数据转换为字节流
            hasher.update(key.encode('utf-8'))  # 包含参数名
            hasher.update(tensor_data.tobytes())  # 原始字节数据
            hasher.update(str(tensor_data.shape).encode('utf-8'))  # 包含形状信息
            hasher.update(str(tensor_data.dtype).encode('utf-8'))  # 包含数据类型

        return hasher.hexdigest()
    

    def weight_distance(self, weights1: collections.OrderedDict, weights2: collections.OrderedDict, device):
        """
        计算两个权重字典之间的欧式距离。
        :return: 两个权重字典之间的欧式距离 (float)
        """
        squared_diff_sum = torch.tensor(0.0, device=device)
        
        # 确保两个字典具有相同的键
        if set(weights1.keys()) != set(weights2.keys()):
            raise ValueError("两个权重字典的键不匹配")
        
        for key in weights1.keys():
            # 确保两个张量具有相同的形状
            if weights1[key].shape != weights2[key].shape:
                raise ValueError(f"键 {key} 对应的张量形状不匹配")
            
            # 计算平方差并累加
            w1 = weights1[key].to(device)
            w2 = weights2[key].to(device)
            squared_diff_sum += torch.sum((w1 - w2) ** 2)
        
        # 返回平方和的平方根
        return torch.sqrt(squared_diff_sum).item()


if __name__ == '__main__':
    community = Community("http://10.1.114.115:18001", simulator=False)
    # # 设置委员会 demo
    # print(community.set_community(["123", "456", "789"], "task0", 0))

    # # 检查是否为委员会中成员demo
    # print(community.check_id_in_com("123", "task0", 0))
    # print(community.check_id_in_com("1234", "task0", 0))

    # # 设置训练参与者 demo
    # print(community.set_trainers(["123", "456", "789"], "task0"))

    # # 检查是否为委员会中成员demo
    # print(community.check_id_in_trainers("123", "task0"))
    # print(community.check_id_in_trainers("1234", "task0"))

    # # 上传和查询得分 demo
    # print(community.upload_scores("cli1", "task0", 0, {"1":1, "2":2}))
    # print(community.get_scores_from_client("cli1", "task0", 0))

    # # 上传和查询哈希 demo
    # print(community.upload_file_hash("cli1", "task0", 0, "abc"))
    # print(community.get_hash_from_client("cli1", "task0", 0))

    # # 求state_dict哈希demo
    # # 创建测试模型
    # model = torch.nn.Sequential(
    #     torch.nn.Linear(10, 5),
    #     torch.nn.ReLU(),
    #     torch.nn.Linear(5, 2)
    # )
    # # 计算哈希值
    # print("Original hash:", community.hash_state_dict(state_dict = model.state_dict()))
    # # 修改参数后的哈希
    # model[0].weight.data += 0.1
    # print("Modified hash:", community.hash_state_dict(state_dict = model.state_dict()))

    # 求模型距离demo
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model1 = torch.nn.Sequential(
        torch.nn.Linear(10, 5),
        torch.nn.ReLU(),
        torch.nn.Linear(5, 2)
    )
    model2 = torch.nn.Sequential(
        torch.nn.Linear(10, 5),
        torch.nn.ReLU(),
        torch.nn.Linear(5, 2)
    )
    print(community.weight_distance(model1.state_dict(), model2.state_dict(), device))