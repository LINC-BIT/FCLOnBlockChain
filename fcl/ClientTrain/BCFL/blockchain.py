import requests
from typing import Tuple


class BlockchainConnector:
    """
    连接 模拟区块链 或 真实区块链后端 的工具
    """
    
    def __init__(self, real_backend_ip_and_port: str, simulator: bool=True):
        """
        :param real_backend_ip_and_port: 真实后端IP+端口, 如http://10.1.114.115:18001
        """
        # 模拟区块链池
        self.simulated_blockchain_pool = {}  
        self.simulator = simulator

        self.real_backend_ip_and_port = real_backend_ip_and_port
    
    # def upload(self, contract_id: str, key: str, value: str) -> None:
    #     """
    #     上传方法1 - 每个客户端对应一个智能合约
        
    #     :param contract_id: 合约名
    #     :param key: 由任务号+round号组成的键
    #     :param value: 对应的filehash值
    #     """
    #     pass
    
    def upload2contract(self, key: str, value: str, contract_id: str="test1" ) -> bool:
        """
        上传方法2 - 所有客户端对应一个智能合约
        
        :param contract_id: 合约名
        :param key: 由任务号+round号+客户端id组成的键
        :param value: 对应的filehash值
        :return bool: 上传成功True, 失败False
        """
        if not self.simulator:
            url = self.real_backend_ip_and_port + "/demo/contract/save"
            payload = {
                # 后端键值对填反了, 用file_hash作为键
                "file_hash": key,
                "file_name": value,
                "contract_name": contract_id,
            }
            try:
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    result: dict = response.json()
                    if result['code']==200 and result['message']=="OK":
                        return True
                    else:
                        print(f"Failed to upload data. Status code: {result['code']}, Message: {result['message']}")
                        return False
                else:
                    raise Exception(f"Failed to upload data. Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                print(f"Error creating task: {e}")
                raise
        else:
            if contract_id in self.simulated_blockchain_pool:
                self.simulated_blockchain_pool[contract_id][key] = value
            else:
                self.simulated_blockchain_pool[contract_id] = {key:value}
    
    def get_from_contract(self, key: str, contract_id: str = "test1") -> Tuple[bool, str]:
        """
        获取合约数据方法
        :param contract_id: 合约名(默认"test1")
        :param key: 由任务号+round号+客户端id组成的键
        :return: bool+对应的file_name值或空字符串, False表示查询运行错误, 未查询到返回True+""
        """
        if not self.simulator:
            url = self.real_backend_ip_and_port + "/demo/contract/get"
            payload = {
                "contract_name": contract_id,
                "file_hash": key  # 根据上传逻辑，这里使用key作为file_hash查询
            }
            
            try:
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    result: dict = response.json()
                    if result['code'] == 200 and result['message'] == "SUCCESS":
                        # 根据上传时的payload结构，返回file_name对应的值
                        return True, result.get('data', {}).get('file_name', '')
                    else:
                        print(f"Failed to fetch data. Code: {result['code']}, Message: {result['message']}")
                        return False, ""
                else:
                    raise Exception(f"Bad response status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                print(f"Error retrieving data: {e}")
                raise  # 保持与上传方法一致的异常处理方式
        else:
            if contract_id in self.simulated_blockchain_pool: 
                return True, self.simulated_blockchain_pool[contract_id].get(key, "")  
            else:
                return True, ""
    
if __name__ == '__main__':
    # upload demo
    # bc = BlockchainConnector("http://10.1.114.115:18001", simulator=False)
    # print(bc.upload2contract("ababc","zxzxc"))

    # get demo
    bc = BlockchainConnector("http://10.1.114.115:18001", simulator=False)
    print(bc.get_from_contract("ababc")) 