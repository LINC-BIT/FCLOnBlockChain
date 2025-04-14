# from socket import  *
# #创建套接字
# tcp_server = socket(AF_INET,SOCK_STREAM)
# #绑定ip，port
# #这里ip默认本机
# address = ('',8000)
# tcp_server.bind(address)
# # 启动被动连接
# #多少个客户端可以连接
# tcp_server.listen(128)
# client_socket, clientAddr = tcp_server.accept()
# #接收对方发送过来的数据
# from_client_msg = client_socket.recv(1024)#接收1024给字节,这里recv接收的不再是元组，区别UDP
# print("接收的数据：",from_client_msg)
# #发送数据给客户端
# send_data = client_socket.send("客户端你好，服务器端收到，公众号【Python研究者】".encode("gbk"))
# #关闭套接字
# #关闭为这个客户端服务的套接字，就意味着为不能再为这个客户端服务了
# #如果还需要服务，只能再次重新连
# client_socket.close()

import flwr as fl
strategy = fl.server.strategy.FedAvg(
    min_available_clients=1,
    min_fit_clients=1,
    min_eval_clients=1,

    # model = MetaLearner(10)
    # Minimum number of clients that need to be connected to the server before a training round can start
)
fl.server.start_server(server_address='10.1.114.64:8000',config={"num_rounds": 3})

import torchvision.models as models
resnet18 = models.resnet18(pretrained=True)