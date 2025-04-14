import hashlib
import requests
import math
import time
import os
import copy
import json
import torch
import hashlib
from datetime import datetime
from typing import Tuple
from torch.utils.data import DataLoader
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
parent_dir2 = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, parent_dir2)

from Agg.Datasets import get_server_dataset

class DataCenterConnector:
    """
    连接 模拟数据中台 或 真实数据中台后端 的工具
    """
    
    def __init__(self, real_backend_ip_and_port: str="", simulator: bool=True):
        """
        :param real_backend_ip_and_port: 真实后端IP+端口, 如http://10.1.114.115:9091
        """
        # 模拟中台存储数据 {task_id1:{submitter_id1: object, submitter_id2: object, ...}, 116:{0: object, 1: object, ...}, ...}
        self.simulated_data_pool = {}
        # 模拟中台存储任务, 不支持重复任务名 {task_name1:{id: 0, meta_data: str, ...}, task_name2:{id: 1, meta_data: str, ...}, ...}
        self.simulated_task_pool ={} 
        # 存储id->任务名的映射关系 {id1:task_name1, id2:task_name2, ...} 
        self.simulated_task_pool_idx ={}  
        self.simulator = simulator

        self.real_backend_ip_and_port = real_backend_ip_and_port
        self.uploader = FileUploader(self.real_backend_ip_and_port)
    
    
    def upload_data(self, task_id: int, submitter_id: int, data: object, type: str="model") -> bool:
        """
        上传数据到中台
        
        :param task_id: 任务号
        :param submitter_id: 对于收集类任务是上传者id, 对于分发任务是接收方id
        :param data: 字符串数据或模型的state_dict()
        :param type: "txt"或"model"
        :return bool
        """
        data = copy.deepcopy(data)
        if not self.simulator:
            # 创建文件夹
            dir_name = "tmp"
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            # 给指定任务上传文件
            if type=="txt":
                # 写入文件
                file_path = os.path.join(dir_name, f"{task_id}{submitter_id}{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                with open(file_path, "w") as f:
                    f.write(data)
                # 文件上传
                self.uploader.check_upload_and_upload_file(file_path=file_path, task_id=task_id, submitter_id=submitter_id)
                # 文件移除
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
            elif type=="model":
                # 保存权重到文件
                file_path = os.path.join(dir_name, f"{task_id}{submitter_id}{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth")
                torch.save(data, file_path) 
                # 文件上传
                self.uploader.check_upload_and_upload_file(file_path=file_path, task_id=task_id, submitter_id=submitter_id)
                # 文件移除
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
            return False
        else:
            if task_id in self.simulated_data_pool:
                self.simulated_data_pool[task_id][submitter_id] = data
            else:
                self.simulated_data_pool[task_id] = {submitter_id: data}


    def download_data(self, task_id: int, submitter_id: int, type: str="model"):
        """
        从中台获取数据
        
        :param contract_id: 合约名
        :param key: 由任务号+round号+客户端id组成的键
        :param value: 对应的filehash值
        :return bool: list或torch model的collections.OrderedDict, 未查找到返回None
        """
        if not self.simulator:
            # 创建文件夹
            dir_name = "tmp"
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            # 根据任务id查询文件, 对于每个提交者只会查到最新的
            result = self.get_file_info_by_task_id(task_id)
            info = None
            for file_info in result["data"]:
                if file_info["submitterId"]==submitter_id:
                    info = file_info
            if not info:
                return None
            file_key = info["fileKey"]

            if type=="txt":
                # 下载文件
                file_path = os.path.join(dir_name, f"{task_id}{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                self.uploader.download_file(file_key, file_path)
                # 读取文件
                lines = []
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                # 文件移除
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return lines
            elif type=="model":
                # 下载文件
                file_path = os.path.join(dir_name, f"{task_id}{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth")
                self.uploader.download_file(file_key, file_path)
                # 读取文件
                weight = torch.load(file_path)
                # 文件移除
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return weight
            return None
        else:
            return self.simulated_data_pool.get(task_id, {}).get(submitter_id, None)


    def create_task(self, task_name: str, submitter_id: int, task_type: str="", task_status: str="", file_number: int=-1, 
                    metadata: str=json.dumps({"message": "This is a test task"})):
        """
        发送POST请求到指定URL以创建任务。
        
        参数:
            task_name (str): 任务名称。
            submitter_id (int): 提交者的ID。
            task_type (str): 任务类型。
            task_status (str): 任务状态。
            file_number (int): 文件数量。
            metadata (str): 元数据JSON字符串。
            
        返回:
            dict: 服务器响应的内容，通常为JSON格式。
            
        异常:
            Exception: 如果请求失败或服务器返回非200状态码。
        """
        if not self.simulator:
            url = self.real_backend_ip_and_port + "/task-info"
            payload = {
                "taskName": task_name,
                "submitterId": submitter_id,
                "taskType": task_type,
                "taskStatus": task_status,
                "fileNumber": file_number,
                "metadata": metadata
            }

            try:
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Failed to create task. Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                print(f"Error creating task: {e}")
                raise
        else:
            if task_name in self.simulated_task_pool:
                raise Exception(f"Task name used.")
            idx = len(self.simulated_task_pool)
            self.simulated_task_pool[task_name] = {
                "id": idx,
                "submitterId": submitter_id,
                "taskType": task_type,
                "taskStatus": task_status,
                "fileNumber": file_number,
                "metadata": metadata
            }
            self.simulated_task_pool_idx[idx] = task_name

    
    def get_task_info_by_task_name(self, task_name: str):
        """
        发送GET请求以获取指定任务名相关的任务信息。

        返回例子: {'msg': '任务获取成功', 'code': 200, 'data': {'tasks': [{'id': 208, 'taskName': 'global_net123', 'submitterId': 103, 'taskType': 'network', 'taskStatus': 'notfinish', 'submitTime': '2025-04-01T11:49:42.000+00:00', 'updateTime': '2025-04-01T11:49:42.000+00:00', 'fileNumber': 1, 'metadata': '{"message": "This is a test task"}'}]}}

        参数:
            task_name (str): 任务名。
            
        返回:
            dict: 服务器响应的内容, 通常为JSON格式。
            
        异常:
            Exception: 如果请求失败或服务器返回非200状态码。
        """
        if not self.simulator:
            url = self.real_backend_ip_and_port + "/task-info/name"
            params = {
                'taskName': task_name
            }

            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Failed to get file info. Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                print(f"Error getting file info: {e}")
                raise
        else:
            task = self.simulated_task_pool.get(task_name, False)
            tasks = [task] if task else []
            return {'msg': '任务获取成功', 'code': 200, 'data': {'tasks': tasks}}
    

    def get_file_info_by_task_id(self, task_id: int):
        """
        发送GET请求以获取指定任务ID相关的文件信息, 对于每个提交者只会查到最新的。
        
        真实中台返回:{'msg': '', 'code': 200, 'data': [{'id': 364, 'fileName': 'file', 'submitterId': 0, 'taskId': None, 'fileBucket': 'default', 'fileKey': 'C:\\Users\\keqiu\\Desktop\\tmp\\8388608068053af2923e00204c3ca7c6a3150cf7.txt', 'version': '1.0', 'dataStatus': 'active', 'submitTime': '2025-04-01T16:49:10.000+00:00', 'metadata': '{"message": "This is a test file"}'}, {'id': 365, 'fileName': 'file', 'submitterId': 1, 'taskId': None, 'fileBucket': 'default', 'fileKey': 'C:\\Users\\keqiu\\Desktop\\tmp\\83886080f57b40c2a1a74b2fa154ac1f48f6eabf.pth', 'version': '1.0', 'dataStatus': 'active', 'submitTime': '2025-04-01T20:15:04.000+00:00', 'metadata': '{"message": "This is a test file"}'}]}

        模拟器返回: {submitter_id1: object, submitter_id2: object, ...}

        参数:
            task_id (int): 任务ID。
            
        返回:
            dict: 服务器响应的内容，通常为JSON格式。
            
        异常:
            Exception: 如果请求失败或服务器返回非200状态码。
        """
        if not self.simulator:
            url = self.real_backend_ip_and_port + "/file/key-with-id"
            params = {
                'taskId': task_id
            }

            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Failed to get file info. Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                print(f"Error getting file info: {e}")
                raise
        else:
            return self.simulated_data_pool.get(task_id,{})


    def wait_for_callback(self, callback, timeout=False, poll_interval=1, *callback_args, **callback_kwargs) -> bool:
        """
        等待回调返回true, 并允许在每次轮询前执行回调方法。

        :param timeout: 最大等待时间（秒），如果为 None 则无限期等待。
        :param poll_interval: 每次检查文件存在与否之间的间隔时间（秒）。
        :param callback: 在每次轮询前执行的回调方法，默认为空方法。
        :return: 文件存在时返回 True: 如果指定了超时时间并且超时则返回 False。
        """
        start_time = time.time()
        
        # 执行回调方法
        while not callback(*callback_args, **callback_kwargs):
            # 判断超时
            elapsed_time = time.time() - start_time
            if timeout and elapsed_time > timeout:
                print(f"警告: 回调方法在 {timeout} 秒内未返回true。")
                return False
            
            # 睡眠
            # print(f"回调方法未返回true, 等待中...")
            time.sleep(poll_interval)

        # print(f"回调方法返回true, 继续执行...")
        return True
    

    def wait_for_task(self, task_name: str) -> bool:
        """
            等待任务创建
            :return: 任务存在时返回 True: 如果指定了超时时间并且超时则返回 False。
        """
        def tmp():
            result = self.get_task_info_by_task_name(task_name)
            return len(result.get("data",{}).get("tasks",[]))>0
        return self.wait_for_callback(callback=tmp)


    def wait_for_task_num(self, task_name: str, num: int) -> bool:
        """
            等待任务下文件数足够
            :return: 文件存在时返回 True: 如果指定了超时时间并且超时则返回 False。
        """
        def tmp():
            # 先拿到task id才能查到文件数
            result = self.get_task_info_by_task_name(task_name)
            # 获取第一个任务的id
            task_id = result["data"]["tasks"][0]["id"] if "data" in result and "tasks" in result["data"] and len(result["data"]["tasks"])>0 else -1
            result = self.get_file_info_by_task_id(task_id)
            if self.simulator:
                return len(result)>=num
            else:
                return len(result.get("data",[]))>=num
        return self.wait_for_callback(callback=tmp)


class FileUploader:
    """
    文件分片上传工具
    """
    
    def __init__(self, real_backend_ip_and_port: str):
        """
        :param real_backend_ip_and_port: 真实后端IP+端口, 如http://10.1.114.115:9091
        """
        self.real_backend_ip_and_port = real_backend_ip_and_port


    def calculate_md5(self, file_path):
        """
        计算文件的MD5值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


    def check_upload(self, upload_addr, identifier, chunk_size, filename, task_id, submitter_id):
        """
        检查文件是否已经完全上传
        """
        params = {
            'identifier': identifier,
            'chunkSize': chunk_size,
            'filename': filename,
            'taskId': task_id,
            'submitterId': submitter_id,
        }
        response = requests.get(upload_addr, params=params)
        # print(response)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('uploadedChunks', []), data.get('data', {}).get('uploaded')
        else:
            raise Exception("Failed to check upload status")


    def upload_chunk(self, upload_addr, chunk_data):
        """
        分片上传文件
        """
        # 不要手动设置 Content-Type 头，让 requests 自动处理
        response = requests.post(upload_addr, files=chunk_data)
        
        if response.status_code != 200:
            raise Exception(f"Failed to upload chunk: {response.text}")
        
        return response.json()
    

    def get_upload_info(self):
        """
        获取上传信息的函数
        """
        response = requests.get(self.real_backend_ip_and_port + "/upload-service")
        if response.status_code == 200:
            data = response.json()
            upload_addr = "http://" + data['data']['addr'] + '/file/upload'
            chunk_size = data['data']['chunk']
            return upload_addr, chunk_size
        else:
            raise Exception("Failed to get upload info")


    def check_upload_and_upload_file(self, file_path, task_id, submitter_id):
        """
        主函数 - 检查并上传文件
        """
        
        # 获取上传地址和分片大小
        upload_addr, chunk_size = self.get_upload_info()

        # 计算文件的MD5值
        identifier = self.calculate_md5(file_path)
        
        # 获取文件总大小和文件名
        total_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        # 检查文件是否已经完全上传
        uploaded_chunks, is_uploaded = self.check_upload(upload_addr, identifier, chunk_size, filename, task_id, submitter_id)
        if is_uploaded:
            # print("文件已上传")
            return

        # 如果文件未完全上传，则继续上传剩余的分片
        for i in range(math.ceil(total_size / chunk_size)):
            chunk_number = i + 1
            if uploaded_chunks and chunk_number in uploaded_chunks:
                print(f"Chunk {chunk_number} already uploaded, skipping.")
                continue
            
            start = i * chunk_size
            end = min(start + chunk_size, total_size)
            
            # 创建分片数据
            with open(file_path, 'rb') as f:
                f.seek(start)
                chunk = f.read(end - start)
            
            chunk_data = {
                'taskId': (None, task_id),
                'subId': (None, submitter_id),
                'identifier': (None, identifier),
                'chunkNumber': (None, str(chunk_number)),
                'chunkSize': (None, str(chunk_size)),
                'currentChunkSize': (None, str(end - start)),
                'totalSize': (None, str(total_size)),
                'totalChunks': (None, str(math.ceil(total_size / chunk_size))),
                'filename': (None, filename),
                'file': ('file', chunk),
            }
            try:
                response = self.upload_chunk(upload_addr, chunk_data)
                print(f'Chunk {chunk_number} uploaded successfully:', response)
            except Exception as e:
                print(f'Error uploading chunk {chunk_number}:', e)
                break
    

    def download_file(self, file_key, save_path) -> bool:
        """
        发送GET请求以获取下载链接，然后使用该链接下载指定fileKey对应的文件。
        
        参数:
            file_key (str): 文件的唯一标识符（key）。
            save_path (str): 文件保存路径，包括文件名。
            
        返回:
            bool: 如果下载成功返回True，否则返回False。
            
        异常:
            Exception: 如果请求失败或服务器返回非200状态码。
        """
        # 第一步：获取下载链接
        url = self.real_backend_ip_and_port + "/file/download"
        params = {
            'fileKey': file_key
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                response_data = response.json()
                # print(response_data)
                if 'data' in response_data:
                    download_url = response_data['data']
                else:
                    raise Exception("Invalid response format, missing downloadUrl")
                
                # 第二步：使用下载链接下载文件
                download_response = requests.get(download_url, stream=True)
                if download_response.status_code == 200:
                    with open(save_path, 'wb') as file:
                        file.write(download_response.content)
                    # print(f"File downloaded successfully and saved to {save_path}")
                    return True
                else:
                    raise Exception(f"Failed to download file from {download_url}. Status code: {download_response.status_code}, Response: {download_response.text}")
            else:
                raise Exception(f"Failed to get download URL. Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False


class Knowledge:
    """
    用于保存持续学习相关知识
    """
    
    def __init__(self, dataLoader: DataLoader):
        """
        :param dataLoade: 数据集的dataloader
        """
        self.dataLoader = dataLoader


    def calculate_md5(self):
        """
        计算数据集的MD5值
        """
        md5_hash = hashlib.md5()

        for batch in self.dataLoader:
            # 如果 batch 是一个 tuple 或 dict，提取其中的数据部分
            if isinstance(batch, (list, tuple)):
                data = batch[0]  # 假设第一个元素是数据
            elif isinstance(batch, dict):
                data = batch['data']  # 假设字典中键 'data' 对应数据
            else:
                data = batch
            
            # 确保数据是张量
            if not isinstance(data, torch.Tensor):
                raise ValueError("Data in the dataloader must be a PyTorch Tensor.")
            
            # 将张量转换为 numpy 数组并转为字节流
            data_bytes = data.cpu().detach().numpy().tobytes()
            
            # 更新 MD5 哈希对象
            md5_hash.update(data_bytes)
        
        # 返回最终的 MD5 哈希值
        return md5_hash.hexdigest()
        


if __name__ == '__main__':
    connector = DataCenterConnector("http://10.1.114.115:9091", simulator=False)

    # 1) 创建任务、查询任务demo
    task_name = "global_net123"
    # result = connector.create_task(task_name, 103, "network", "notfinish", 1, json.dumps({"message": "This is a test task"}))
    # print("create result:", result)
    # task_id = result.get("data").get("taskId") if "data" in result and "taskId" in result.get("data") else -1
    # print("task_id", task_id)
    # result = connector.get_task_info_by_task_name(task_name)
    # print("get result", result)
    # # 获取第一个任务的id
    # task_id = result["data"]["tasks"][0]["id"] if "data" in result and "tasks" in result["data"] and len(result["data"]["tasks"])>0 else -1
    # result = connector.get_file_info_by_task_id(task_id)
    # print("get result", result)



    # 2) 上传字符串数据、查询字符串数据demo
    # # 查询任务获取任务id
    # result = connector.get_task_info_by_task_name(task_name)
    # # print("get result", result)
    # task_id = result["data"]["tasks"][0]["id"]
    # print("task_id", task_id)
    # # 上传
    # connector.upload_data(
    #     task_id=task_id,
    #     submitter_id=0,
    #     data="789",
    #     type="txt"
    #     )
    # # 根据任务id下载数据
    # print(connector.download_data(task_id=task_id, submitter_id=0, type="txt"))

    

    # 3) 上传模型串数据、查询模型数据demo
    # # 查询任务获取任务id
    # result = connector.get_task_info_by_task_name(task_name)
    # # print("get result", result)
    # task_id = result["data"]["tasks"][0]["id"]
    # print("task_id", task_id)
    # # 上传
    # model = torch.nn.Linear(2, 1)  # 最简单的线性模型 (y = w*x + b)
    # print(model.state_dict())  # 打印模型参数 (weight & bias)
    # connector.upload_data(
    #     task_id=task_id,
    #     submitter_id=1,
    #     data=model.state_dict(),
    #     type="model"
    #     )
    # # 根据任务id下载数据
    # weight = connector.download_data(task_id=task_id, submitter_id=1, type="model")
    # print(weight)


    # 4) 计算Knowledge的md5例子
    dataset = get_server_dataset(5, "CIFAR100")
    dataloader = DataLoader(dataset,batch_size=1, shuffle=False)
    knowledge = Knowledge(dataloader)
    print(knowledge.calculate_md5())

