import logging
from datetime import datetime
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
parent_dir2 = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, parent_dir2)


def create_setup_logger():
    # 单例模式
    _logger = None
    _initialized = False

    def setup_logger():
        nonlocal _logger, _initialized
        if not _initialized:
            # 创建日志目录
            # log_dir = "logs"
            log_dir = "C:/Users/keqiu/Desktop/zt/FedAgg/log"
            os.makedirs(log_dir, exist_ok=True)
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 配置日志文件名
            log_filename = f"{log_dir}/app_{timestamp}.log"
            
            # 配置日志记录器
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_filename, encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            
            # 获取当前模块的logger
            _logger = logging.getLogger(__name__)
            _initialized = True
        return _logger

    return setup_logger

# 将闭包函数赋值给setup_logger变量
get_logger = create_setup_logger()

# 使用示例
if __name__ == "__main__":
    logger = get_logger()  # 调用闭包函数获取单例logger
    logger.info("这是一条测试日志信息")
    logger = get_logger()  
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")