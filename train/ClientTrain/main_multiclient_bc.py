import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import copy
import itertools
from random import shuffle

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.tensorboard import SummaryWriter

from ClientTrain.utils.options import args_parser
from ClientTrain.utils.train_utils import get_data, get_model, read_data
from ClientTrain.models.Update import LocalUpdate,DatasetSplit
from ClientTrain.models.test import test_img_local_all, test_img_local_all_channel
from ClientTrain.LongLifeMethod.EWC import Appr as EWC_Appr
from ClientTrain.LongLifeMethod.EWC import LongLifeTrain as EWC_LongLifeTrain
from ClientTrain.LongLifeMethod.MAS import Appr as MAS_Appr
from ClientTrain.LongLifeMethod.MAS import LongLifeTrain as MAS_LongLifeTrain
from ClientTrain.LongLifeMethod.GEM import Appr as GEM_Appr
from ClientTrain.LongLifeMethod.GEM import LongLifeTrain as GEM_LongLifeTrain
from ClientTrain.LongLifeMethod.FedKNOW import Appr as FedKNOW_Appr
from ClientTrain.LongLifeMethod.MAS import LongLifeTrain as FedKNOW_LongLifeTrain
from ClientTrain.LongLifeMethod.Packnet import Appr as Packnet_Appr
from ClientTrain.LongLifeMethod.Packnet import LongLifeTrain as Packnet_LongLifeTrain
from ClientTrain.LongLifeMethod.ChannelGate import Appr as ChannelGate_Appr
from ClientTrain.LongLifeMethod.ChannelGate import LongLifeTrain as ChannelGate_LongLifeTrain
from ClientTrain.models.ChannelGatemodel.model import ChannelGatedCL

from ClientTrain.AggModel.sixcnn import SixCNN
from ClientTrain.AggModel.resnet import Resnet18
from torch.utils.data import DataLoader
from Agg.AggModel.sixcnn import SixCNN as KDmodel
import time
from Agg.FedDag import FedDag
from Agg.Datasets import ServerDataset, get_server_dataset
from ClientTrain.models.Packnet import PackNet
from ClientTrain.utils.MultiModelDict import get_model_dict
import copy
from ClientTrain.config import cfg
from ClientTrain.utils.logger import get_logger

from BCFL.attack import modify_weights, get_attack_dataset, train_attack_model_epoch, train_attack_model_for_epochs
from BCFL.community import Community
from BCFL.data_center import DataCenterConnector

logger = get_logger()

if __name__ == '__main__':
    # parse args
    args = args_parser()
    args.device = torch.device('cuda:{}'.format(args.gpu) if torch.cuda.is_available() and args.gpu != -1 else 'cpu')

    print(args.alg)
    write = SummaryWriter('/data/lpyx/FedAgg/ClientTrain/log/FC/'+args.clmethod+'/server_epoch10_high20_dag_' + args.dataset+'_'+'round' + str(args.round) + '_frac' + str(args.frac))
    # build model
    # net_glob = get_model(args)
    # net_glob = SixCNN([3,32,32],outputsize=100)
    
    # if args.model=='sixcnn':
    #     net_glob = SixCNN([3,32,32],outputsize=100)
    # elif args.model=='resnet18':
    #     net_glob = Resnet18([3, 32, 32], outputsize=100)

    # TODO 要改模型、cl_method和dataloader
    multi_model_dict_list = get_model_dict()
    model_conf = {}
    for conf in multi_model_dict_list:
        if conf["name"] == args.model:
            model_conf = conf
    net_glob = conf.get("model", None)
    # args.clmethod = conf.get("cl_method", None)

    dataset_train, dataset_test, dict_users_train, dict_users_test = get_data(args)
    print("dataset_train", dataset_train)
    # dict_users_test = [copy.deepcopy(dict_users_test) for i in range(2) for dict_user in dict_users_test]
    # dict_users_test 键是用户ID(0到num_users-1),值是该用户分配到的数据样本索引数组
    # 例子: {0: array([590, 591, 592, 593, 594, 595, 596, , 120, 121, 122, ...]), 1: array([850, 851, 852, ...]), ...}
    for idx in dict_users_train.keys():
        np.random.shuffle(dict_users_train[idx])
    client_task=[[j for j in range(args.task)] for i in range(args.num_users)]
    for i in client_task:
        shuffle(i)
    # client_task表示每个客户端训练任务的队列, 会根据任务去取训练数据, 按目前数据集是划分为10个任务
    # 例子: [[7, 8, 0, 2, 9, 6, 5, 4, 1, 3], [2, 8, 5, 4, 1, 3, 9, 0, 6, 7], ...]

    net_glob.train()
    net_glob_cl = ChannelGatedCL(in_ch=cfg.IN_CH, out_dim=cfg.OUT_DIM,
                   conv_ch=cfg.CONV_CH,
                   sparsity_patience_epochs=cfg.SPARSITY_PATIENCE_EPOCHS,
                   lambda_sparse=cfg.LAMBDA_SPARSE,
                   freeze_fixed_proc=cfg.FREEZE_FIXED_PROC,
                   freeze_top_proc=cfg.FREEZE_TOP_PROC,
                   freeze_prob_thr=cfg.FREEZE_PROB_THR).to(cfg.DEVICE)
    total_num_layers = len(net_glob.state_dict().keys())
    print(net_glob.state_dict().keys())
    net_keys = [*net_glob.state_dict().keys()]

    # specify the representation parameters (in w_glob_keys) and head parameters (all others)
    if args.alg == 'fedrep' or args.alg == 'fedper':
        if 'cifar' in args.dataset or 'miniimagenet' in args.dataset:
            # w_glob_keys = [[k] for k,_ in net_glob.feature_net.named_parameters()]
            w_glob_keys = [net_glob.weight_keys[i] for i in [j for j in range(len(net_glob.weight_keys))]]
        elif 'mnist' in args.dataset:
            w_glob_keys = [net_glob.weight_keys[i] for i in [0, 1, 2]]
        elif 'sent140' in args.dataset:
            w_glob_keys = [net_keys[i] for i in [0, 1, 2, 3, 4, 5]]
        else:
            w_glob_keys = net_keys[:-2]
    elif args.alg == 'lg':
        if 'cifar' in args.dataset:
            w_glob_keys = [net_glob.weight_keys[i] for i in [1, 2]]
        elif 'mnist' in args.dataset:
            w_glob_keys = [net_glob.weight_keys[i] for i in [2, 3]]
        elif 'sent140' in args.dataset:
            w_glob_keys = [net_keys[i] for i in [0, 6, 7]]
        else:
            w_glob_keys = net_keys[total_num_layers - 2:]

    if args.alg == 'fedavg' or args.alg == 'prox':
        w_glob_keys = []
    if 'sent140' not in args.dataset:
        w_glob_keys = list(itertools.chain.from_iterable(w_glob_keys))

    print(total_num_layers)
    if args.alg == 'fedrep' or args.alg == 'fedper' or args.alg == 'lg':
        num_param_glob = 0
        num_param_local = 0
        for key in net_glob.state_dict().keys():
            num_param_local += net_glob.state_dict()[key].numel()
            print(num_param_local)
            if key in w_glob_keys:
                num_param_glob += net_glob.state_dict()[key].numel()
        percentage_param = 100 * float(num_param_glob) / num_param_local
        print('# Params: {} (local), {} (global); Percentage {:.2f} ({}/{})'.format(
            num_param_local, num_param_glob, percentage_param, num_param_glob, num_param_local))
    print("learning rate, batch size: {}, {}".format(args.lr, args.local_bs))

    # generate list of local models for each user
    net_local_list = []
    w_locals = {}
    for user in range(args.num_users):
        w_local_dict = {}
        for key in net_glob.state_dict().keys():
            w_local_dict[key] = net_glob.state_dict()[key]
        w_locals[user] = w_local_dict

    # training
    indd = None  # indices of embedding for sent140
    loss_train = []
    accs = []
    times = []
    accs10 = 0
    accs10_glob = 0
    start = time.time()
    task=-1
    kd_model = KDmodel([3,32,32],100)
    if args.clmethod == 'EWC':
        apprs = [EWC_Appr(copy.deepcopy(net_glob).to(args.device), None,lr=args.lr, nepochs=args.local_ep, args=args,kd_model=kd_model, kd_epoch=args.kd_epoch) for i in range(args.num_users)]
    elif args.clmethod == 'MAS':
        apprs = [MAS_Appr(copy.deepcopy(net_glob).to(args.device), None, lr=args.lr, nepochs=args.local_ep, args=args, kd_epoch=args.kd_epoch,
                      kd_model=kd_model) for i in range(args.num_users)]
    elif args.clmethod == 'GEM':
        apprs = [GEM_Appr(net_glob.to(args.device), kd_model, 3 * 32 * 32, 100, 10, args, kd_epoch=args.kd_epoch) for i in range(args.num_users)]
    elif args.clmethod == 'FedKNOW':
        apprs = [FedKNOW_Appr(copy.deepcopy(net_glob),PackNet(args.task,device=args.device),copy.deepcopy(net_glob), None,lr=args.lr, nepochs=args.local_ep, args=args,kd_model=kd_model, kd_epoch=args.kd_epoch) for i in range(args.num_users)]
    elif args.clmethod == 'Packnet':
        apprs = [Packnet_Appr(copy.deepcopy(net_glob).to(args.device), None, lr=args.lr, nepochs=args.local_ep, args=args,
                      kd_model=kd_model, kd_epoch=args.kd_epoch) for i in range(args.num_users)]
    elif args.clmethod == 'ChannelGate':
        apprs = [ChannelGate_Appr(copy.deepcopy(net_glob_cl).to(args.device), None,lr=args.lr, nepochs=args.local_ep, args=args,kd_model=kd_model, kd_epoch=args.kd_epoch) for i in range(args.num_users)]
    print(args.round)
    # serverAgg = FedDag(int(args.frac * args.num_users),int(args.frac * args.num_users * 5),datasize=[3,32,32],dataname='CIFAR100')
    serverAgg = FedDag(int(args.num_users),int(args.num_users * 5),datasize=[3,32,32],dataname='CIFAR100')
    w_globals = []


    # BCFL相关代码, 初始化变量
    # community = Community("http://10.1.114.115:18001", simulator=False)
    community = Community(simulator=True)
    # dataCenterConnector = DataCenterConnector("http://10.1.114.115:9091", simulator=False)
    dataCenterConnector = DataCenterConnector(simulator=True)
    wrong_dataset = get_attack_dataset(5, "CIFAR100")
    wrong_dataloader = DataLoader(wrong_dataset, batch_size=3, shuffle=True)
    server_dataset = get_server_dataset(samples=5, name='CIFAR100', t=task)
    server_dataloader = DataLoader(server_dataset,batch_size=1, shuffle=False)
    # 初始化委员会机制相关数据, 用于记录权重
    score_weights = { i:10 for i in range(args.num_users)} 
    community.upload_scores(-1, f"{task}-weight", -1, score_weights) # member为-1表示全体成员

    logger.info("malicious_clients: "+str(args.malicious_clients))

    # 多轮任务迭代, iter也是任务号
    for iter in range(args.epochs):
        # task和iter是一致的. 因为当iter是args.round的倍数时，task会自增1, 而args.round默认是1
        if iter % (args.round) == 0:
            # 一个round包含多个iter
            # 一个round的第一个epoch
            task += 1 # task表示任务序列中的第几个任务, 会根据任务取数据
            w_globals = []
        w_glob = {}
        loss_locals = []
        participants_num = max(int(args.frac * args.num_users), 1)
        if iter == args.epochs:
            participants_num = args.num_users

        # idxs_users = [0, 1, 2, 3, 4]
        if iter % (args.round) == args.round - 1: 
            print("*"*100)
            print("Last Train")
            idxs_users = [i for i in range(args.num_users)]
        else:
            idxs_users = [int(idx) for idx in np.random.choice(range(args.num_users), participants_num, replace=False)]
            for attack_idx in args.malicious_clients: # 攻击者积极参与训练
                if attack_idx not in idxs_users: idxs_users.append(attack_idx)
        
        w_keys_epoch = w_glob_keys
        times_in = []
        total_len = 0
        tr_dataloaders= None
        all_kd_models = []


        # BCFL相关代码, 创建本地模型收集任务
        dataCenterConnector.create_task(task_name=f"round-{iter}-collect", submitter_id=0, task_type="collect")


        # 每个客户端, idx是用户端id
        for _, idx in enumerate(idxs_users):
            start_in = time.time()

            # 最后一轮可能会报错 list index out of range, 因为task应该是从0~args.task-1, 但此时task为args.task, args.epochs和args.task不一致导致的
            # print("idx", idx)
            logger.info("idx "+str(idx))
            # print("task", task)
            logger.info("task "+str(task))
            tr_dataloaders = DataLoader(DatasetSplit(dataset_train[client_task[idx][task]],dict_users_train[idx],tran_task=[task,client_task[idx][task]]),batch_size=args.local_bs, shuffle=True)
                # if args.epochs == iter:
                #     local = LocalUpdate(args=args, dataset=dataset_train[task], idxs=dict_users_train[idx][:args.m_ft])
                # else:
                #     local = LocalUpdate(args=args, dataset=dataset_train[task], idxs=dict_users_train[idx][:args.m_tr])

                # appr = Appr(net, sbatch=args.batch_size, lr=args.lr, nepochs=args.nepochs, args=args, log_name=log_name)

            # 第idx个客户端的封装 
            appr = apprs[idx]
            # 从w_globals获取分发的模型
            # if len(w_globals) != 0:
            #     agg_client = [w['client'] for w in w_globals]
            #     if idx in agg_client:
            #         appr.cur_kd.load_state_dict(w_globals[agg_client.index(idx)]['model'])


            # BCFL相关代码, 获取上一轮分发任务分发的模型
            if iter % (args.round) != 0:
                result = dataCenterConnector.get_task_info_by_task_name(f"round-{iter-1}-distribute")
                task_id = result["data"]["tasks"][0]["id"]
                weight = dataCenterConnector.download_data(task_id=task_id, submitter_id=idx, type="model")
                if weight is not None:
                    appr.cur_kd.load_state_dict(weight)


            # 设置数据集并训练
            # appr.set_model(net_local.to(args.device))
            appr.set_trData(tr_dataloaders)
            last = iter == args.epochs
            # kd_models表示蒸馏模型(可能也是教师模型?)
            if args.clmethod == 'EWC':
                kd_models, loss, indd = EWC_LongLifeTrain(args,appr,iter,None,idx)
            elif args.clmethod == 'MAS':
                kd_models, loss, indd = MAS_LongLifeTrain(args, appr, iter, None, idx)
            elif args.clmethod == 'GEM':
                kd_models, loss, indd = GEM_LongLifeTrain(args, appr, tr_dataloaders, iter, idx)
            elif args.clmethod == 'FedKNOW':
                kd_models, loss, indd = FedKNOW_LongLifeTrain(args,appr,iter,None,idx)
            elif args.clmethod == 'Packnet':
                kd_models, loss, indd = Packnet_LongLifeTrain(args, appr, iter, None, idx)
            elif args.clmethod == 'ChannelGate':
                kd_models, loss, indd = ChannelGate_LongLifeTrain(args, appr, iter, None, idx)
            

            # BCFL相关代码
            if idx in args.malicious_clients and hasattr(apprs[args.victim], 'cur_kd'):
                tmp_kd = copy.deepcopy(appr.cur_kd)

                # 恶意节点篡改客户端模型参数
                kd_models = tmp_kd.state_dict()
                kd_models = modify_weights(kd_models, proportion=0.5)
                tmp_kd.load_state_dict(kd_models)

                # # 恶意客户端设置错误训练集, 并训练kd模型
                # appr.set_trData(wrong_dataloader)
                # if args.clmethod == 'MAS':
                #     print("恶意训练")
                #     kd_models, loss, indd = MAS_LongLifeTrain(args, appr, iter, None, idx)

                # 恶意客户端kdmodel训练 针对args.victim客户端
                tmp_kd, attack_loss = train_attack_model_for_epochs(
                        cur_center=apprs[args.victim].cur_kd,
                        cur_candidate=tmp_kd,
                        dataloader=server_dataloader,
                        device=args.device,
                        task=task,
                        epoch=100
                    )
                # 客户端本地appr保留的kd没问题, 只是上传的kd有问题
                kd_models = tmp_kd.state_dict()
                print("恶意训练 loss", attack_loss)


            # all_kd_models.append({'client':idx, 'models': kd_models})

            loss_locals.append(copy.deepcopy(loss))


            # BCFL相关代码，客户端将模型上传至特定任务
            task_name = f"round-{iter}-collect"
            # 等待任务创建
            dataCenterConnector.wait_for_task(task_name)
            # 上传任务数据
            result = dataCenterConnector.get_task_info_by_task_name(task_name)
            task_id = result["data"]["tasks"][0]["id"]
            dataCenterConnector.upload_data(task_id=task_id, submitter_id=idx, data=kd_models, type="model")
            # 求哈希并向区块链上传哈希
            hash_value = community.hash_state_dict(state_dict = kd_models)
            community.upload_file_hash(client_id=str(idx), task_id=str(task), round=iter, hash=hash_value)


        # 聚合 
        if iter % args.round == args.round - 1:
            # 一个round包含多个iter
            # 一个round的最后一个iter
            w_globals = []
        else:
            print("Aggregate.")
            
            
            # BCFL相关代码，从特定任务下载客户端上传的数据，存入all_kd_models中
            # 等待文件数足够
            dataCenterConnector.wait_for_task_num(task_name=task_name, num=participants_num)
            # 获取id用于下载数据
            result = dataCenterConnector.get_task_info_by_task_name(task_name)
            task_id = result["data"]["tasks"][0]["id"]
            # 下载
            all_kd_models = []
            for idx in idxs_users:
                weight = dataCenterConnector.download_data(task_id=task_id, submitter_id=idx, type="model")
                # 求哈希并比较区块链上哈希
                hash_value = community.hash_state_dict(state_dict = weight)
                # real_value = community.upload_file_hash(client_id=str(idx), task_id=str(task), round=iter, hash=hash_value)
                ok, real_value =community.get_hash_from_client(client_id=str(idx), task_id=str(task), round=iter)
                print("比较成功.", end="") if hash_value == real_value else print(f"比较失败:{task}-{idx}")
                # 保存权重
                if weight is not None:
                    all_kd_models.append({'client':idx, 'models': weight})
            

            # 聚合服务器负责聚合
            # w_globals = serverAgg.update(all_kd_models, task)
            # 找出每个模型最相似的几个模型
            models_with_similarity = serverAgg.calculate_similarity(all_kd_models, task)


            # BCFL相关代码
            # 求出相似模型到中心模型的距离
            for model in models_with_similarity:
                center_dict = model["model"].state_dict()
                for similarity_item in model["similarity"]:
                    # similarity_item example: {'number':number,'id':id,'sim':loss}
                    number_item = similarity_item["number"]
                    item_dict = serverAgg.candidate_models[number_item].state_dict()
                    similarity_item["distance"] = community.weight_distance(center_dict, item_dict, args.device)
            # 聚合前打分
            print("打分")
            for member in idxs_users:
                # member 为打分者
                member_weight = dataCenterConnector.download_data(task_id=task_id, submitter_id=member, type="model")
                # 求出对各idx的距离
                distance = {}
                for idx in idxs_users:
                    idx_weight = dataCenterConnector.download_data(task_id=task_id, submitter_id=idx, type="model")
                    dis = community.weight_distance(member_weight, idx_weight, args.device)
                    distance[idx] = dis
                # 和idx的相似模型进行比较
                # 对idx的评分, 0中立, -1差评, 1好评
                score = {idx:0 for idx in idxs_users} 
                score[member] = 1
                for model in models_with_similarity:
                    if member in [item["id"] for item in model["similarity"]]:
                    # similarity_item example: {'number':number,'id':id,'sim':loss,'distance':distance}
                        continue
                    idx = model["client"]
                    distance_member = distance[idx] # member to idx
                    similarity_list = model["similarity"]
                    for similarity_item in similarity_list:
                        distance_item = similarity_item["distance"] # item to idx
                        id_item = similarity_item["id"]
                        if score[id_item] != -1 and distance_item < distance_member:
                            score[id_item] = 1
                        else:
                            score[id_item] = -1
                # 评分上链
                community.upload_scores(member, str(task), iter, score)
                
            # 评分汇总
            score_sum = {idx:0 for idx in idxs_users} 
            for member in idxs_users:
                ok, score = community.get_scores_from_client(member, task, iter)
                for idx, judge in score.items(): score_sum[int(idx)] += judge # 下载的数据key会变str
            print("sum", score_sum)
            # 下载、调整、上传权重
            ok, score_weights = community.get_scores_from_client(-1, f"weight-{task}", iter-1)
            for client, score in score_sum.items():
                if score>0: score_weights[client] = min(10, score_weights[client]+1)
                else: score_weights[client] = max(0, score_weights[client])
            community.upload_scores(-1, f"weight-{task}", iter, score_weights)

            # 是否激活防御机制
            if args.defend:
                blacklist = [ client for client, weight in score_weights.items() if weight<6 ]
                for model in models_with_similarity:
                    model["similarity"] = [ item for item in model["similarity"] if item["id"] not in blacklist ]



            # 将模型和它们的相似模型聚合
            w_globals = serverAgg.aggregate_model(models_with_similarity)


            # BCFL相关代码, 将文件上传到指定任务(得分最高的委员上传, 其它委员监督), 并且文件描述包含用户信息
            task_name = f"round-{iter}-distribute"
            dataCenterConnector.create_task(task_name=task_name, submitter_id=0, task_type="distribute")
            result = dataCenterConnector.get_task_info_by_task_name(task_name)
            task_id = result["data"]["tasks"][0]["id"]

            idx_modelid_map = {w["client"]:modelid for modelid, w in enumerate(w_globals) if w["client"] in idxs_users}
            for idx, model_id in idx_modelid_map.items():
                data = w_globals[model_id]["model"]
                dataCenterConnector.upload_data(task_id=task_id, submitter_id=idx, data=data, type="model")


        # 每次聚合后进行一次测试
        loss_avg = sum(loss_locals) / len(loss_locals)
        loss_train.append(loss_avg)

        if args.clmethod == 'ChannelGate':
            acc_test, loss_test = test_img_local_all_channel(None, args, dataset_test, dict_users_test, task,
                                                             apprs=apprs, w_locals=None, return_all=False, write=write,
                                                             round=iter, client_task=client_task)
        else:
            acc_test, loss_test = test_img_local_all(None, args, dataset_test, dict_users_test,task,apprs=apprs,w_locals=None,return_all=False,write=write,round=iter,client_task=client_task)
        accs.append(acc_test)

        # print('Round {:3d}, Train loss: {:.3f}, Test loss: {:.3f}, Test accuracy: {:.2f}'.format(
        #         iter, loss_avg, loss_test, acc_test))
        logger.info('Round {:3d}, Train loss: {:.3f}, Test loss: {:.3f}, Test accuracy: {:.2f}'.format(
                iter, loss_avg, loss_test, acc_test))
        # 一个round的最后一个iter更新cur_kd
        if iter % (args.round) == args.round - 1:
            # for i in range(args.num_users):
            for i in idxs_users:
                tr_dataloaders = DataLoader(
                    DatasetSplit(dataset_train[client_task[i][task]], dict_users_train[i][:args.m_ft],
                                 tran_task=[task, client_task[i][task]]), batch_size=args.local_bs, shuffle=True)
                # 更新cur_kd
                client_state = apprs[i].prune_kd_model(tr_dataloaders,task)
                serverAgg.add_history(client_state)
