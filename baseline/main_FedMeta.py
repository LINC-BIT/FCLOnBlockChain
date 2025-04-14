import copy
import itertools
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.tensorboard import SummaryWriter

from utils.options import args_parser
from utils.train_utils import get_data, get_model, read_data
from models.Update import LocalUpdate,DatasetSplit
from models.test import test_img_local_all
from LongLifeMethod.FedMeta import Appr,LongLifeTest,LongLifeTrain
from models.Nets import RepTail
from torch.utils.data import DataLoader
import time
class Adam:

    """
    全局 Adam, 用来基于从客户端收集的梯度, 来更新全局网络的参数
    """

    def __init__(self, lr=0.01, betas=(0.9, 0.999), eps=1e-08):
        """

        :param lr:
        :param betas:
        :param eps:
        """
        self.lr = lr
        self.beta1 = betas[0]
        self.beta2 = betas[1]
        self.eps = eps
        self.m = dict()
        self.v = dict()
        self.n = 0
        self.creted_momtem_grad_index = set()

    def __call__(self, params, grads, i):
        # 创建对应的 id
        params.requires_grad = False
        grads = grads.to('cpu')
        if i not in self.m:
            self.m[i] = torch.zeros_like(params)
        if i not in self.v:
            self.v[i] = torch.zeros_like(params)

        self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grads
        self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * torch.square(grads)

        alpha = self.lr * np.sqrt(1 - np.power(self.beta2, self.n))
        alpha = alpha / (1 - np.power(self.beta1, self.n))

        params.sub_(alpha * self.m[i] / (torch.sqrt(self.v[i]) + self.eps))

    def increase_n(self):
        self.n += 1
if __name__ == '__main__':
    # parse args
    args = args_parser()
    args.device = torch.device('cuda:{}'.format(args.gpu) if torch.cuda.is_available() and args.gpu != -1 else 'cpu')

    lens = np.ones(args.num_users)
    if 'cifar' in args.dataset or args.dataset == 'mnist':
        dataset_train, dataset_test, dict_users_train, dict_users_test = get_data(args)
        for idx in dict_users_train.keys():
            np.random.shuffle(dict_users_train[idx])
    else:
        if 'femnist' in args.dataset:
            train_path = './leaf-master/data/' + args.dataset + '/data/mytrain'
            test_path = './leaf-master/data/' + args.dataset + '/data/mytest'
        else:
            train_path = './leaf-master/data/' + args.dataset + '/data/train'
            test_path = './leaf-master/data/' + args.dataset + '/data/test'
        clients, groups, dataset_train, dataset_test = read_data(train_path, test_path)
        lens = []
        for iii, c in enumerate(clients):
            lens.append(len(dataset_train[c]['x']))
        dict_users_train = list(dataset_train.keys())
        dict_users_test = list(dataset_test.keys())
        print(lens)
        print(clients)
        for c in dataset_train.keys():
            dataset_train[c]['y'] = list(np.asarray(dataset_train[c]['y']).astype('int64'))
            dataset_test[c]['y'] = list(np.asarray(dataset_test[c]['y']).astype('int64'))

    print(args.alg)
    write = SummaryWriter('./log/FedMeta_' + args.dataset+'_'+'round' + str(args.round) + '_frac' + str(args.frac))
    # build model
    # net_glob = get_model(args)
    net_glob = RepTail([3, 32, 32])
    net_glob.train()
    if args.load_fed != 'n':
        fed_model_path = './save/' + args.load_fed + '.pt'
        net_glob.load_state_dict(torch.load(fed_model_path))

    total_num_layers = len(net_glob.state_dict().keys())
    print(net_glob.state_dict().keys())
    net_keys = [*net_glob.state_dict().keys()]

    # specify the representation parameters (in w_glob_keys) and head parameters (all others)
    if args.alg == 'fedrep' or args.alg == 'fedper':
        if 'cifar' in args.dataset:
            # w_glob_keys = [[k] for k,_ in net_glob.feature_net.named_parameters()]
            w_glob_keys = [net_glob.weight_keys[i] for i in [j for j in range(14)]]
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
    print(w_glob_keys)
    print(net_keys)
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
    apprs = [Appr(copy.deepcopy(net_glob).to(args.device), None,lr=args.lr, nepochs=args.local_ep, args=args) for i in range(args.num_users)]
    print(args.round)
    outer_opt = Adam(lr=args.lr)
    for iter in range(args.epochs):
        if iter % (args.round) == 0:
            task+=1
        loss_locals = []
        w_glob_grad = {}
        m = max(int(args.frac * args.num_users), 1)
        if iter == args.epochs:
            m = args.num_users
        idxs_users = np.random.choice(range(args.num_users), m, replace=False)
        w_keys_epoch = w_glob_keys
        times_in = []
        total_len = 0
        tr_dataloaders= None
        for ind, idx in enumerate(idxs_users):
            start_in = time.time()
            if 'femnist' in args.dataset or 'sent140' in args.dataset:
                if args.epochs == iter:
                    local = LocalUpdate(args=args, dataset=dataset_train[list(dataset_train.keys())[idx][:args.m_ft]],
                                        idxs=dict_users_train, indd=indd)
                else:
                    local = LocalUpdate(args=args, dataset=dataset_train[list(dataset_train.keys())[idx][:args.m_tr]],
                                        idxs=dict_users_train, indd=indd)
            else:
                tr_dataloaders = DataLoader(DatasetSplit(dataset_train[task],dict_users_train[idx][:args.m_ft]),batch_size=args.local_bs, shuffle=True)
                # if args.epochs == iter:
                #     local = LocalUpdate(args=args, dataset=dataset_train[task], idxs=dict_users_train[idx][:args.m_ft])
                # else:
                #     local = LocalUpdate(args=args, dataset=dataset_train[task], idxs=dict_users_train[idx][:args.m_tr])

                # appr = Appr(net, sbatch=args.batch_size, lr=args.lr, nepochs=args.nepochs, args=args, log_name=log_name)
            net_local = copy.deepcopy(net_glob)
            w_local = net_local.state_dict()
            # if args.alg != 'fedavg' and args.alg != 'prox':
            #     for k in w_locals[idx].keys():
            #         if k not in w_glob_keys:
            #             w_local[k] = w_locals[idx][k]
            net_local.load_state_dict(w_local)
            appr = apprs[idx]
            appr.set_model(net_local.to(args.device))
            appr.set_trData(tr_dataloaders)
            last = iter == args.epochs
            if 'femnist' in args.dataset or 'sent140' in args.dataset:
                w_local, loss, indd = local.train(net=net_local.to(args.device), ind=idx, idx=clients[idx],
                                                  w_glob_keys=w_glob_keys, lr=args.lr, last=last)
            else:
                w_local,loss, indd = LongLifeTrain(args,appr,iter,None,idx)
            loss_locals.append(copy.deepcopy(loss))
            total_len += lens[idx]
            if len(w_glob_grad) == 0:
                w_glob_grad = w_local
                for k in range(len(w_glob_grad)):
                    w_glob_grad[k] = w_glob_grad[k] * lens[idx]
            else:
                for k in range(len(w_glob_grad)):
                    w_glob_grad[k] += w_local[k] * lens[idx]
            times_in.append(time.time() - start_in)
        loss_avg = sum(loss_locals) / len(loss_locals)
        loss_train.append(loss_avg)

        # get weighted average for global weights
        for k in range(len(w_glob_grad)):
            w_glob_grad[k] = torch.div(w_glob_grad[k], total_len)
        outer_opt.increase_n()
        w_glob = net_glob.state_dict()
        for k,para in enumerate(w_glob.values()):
            outer_opt(para, w_glob_grad[k], i=k)
        net_glob.state_dict(w_glob)
        if iter % args.round == args.round-1:
            if times == []:
                times.append(max(times_in))
            else:
                times.append(times[-1] + max(times_in))
            acc_test, loss_test = test_img_local_all(net_glob, args, dataset_test, dict_users_test,task,
                                                     w_glob_keys=w_glob_keys, w_locals=w_locals, indd=indd,
                                                     dataset_train=dataset_train, dict_users_train=dict_users_train,
                                                     return_all=False,write=write,meta=True)
            accs.append(acc_test)
            # for algs which learn a single global model, these are the local accuracies (computed using the locally updated versions of the global model at the end of each round)
            if iter != args.epochs:
                print('Round {:3d}, Train loss: {:.3f}, Test loss: {:.3f}, Test accuracy: {:.2f}'.format(
                    iter, loss_avg, loss_test, acc_test))
            else:
                # in the final round, we sample all users, and for the algs which learn a single global model, we fine-tune the head for 10 local epochs for fair comparison with FedRep
                print('Final Round, Train loss: {:.3f}, Test loss: {:.3f}, Test accuracy: {:.2f}'.format(
                    loss_avg, loss_test, acc_test))
            if iter >= args.epochs - 10 and iter != args.epochs:
                accs10 += acc_test / 10

            # below prints the global accuracy of the single global model for the relevant algs
            # if args.alg == 'fedavg' or args.alg == 'prox':
            #     acc_test, loss_test = test_img_local_all(net_glob, args, dataset_test, dict_users_test,
            #                                              w_locals=None, indd=indd, dataset_train=dataset_train,
            #                                              dict_users_train=dict_users_train, return_all=False,meta=True)
            #     if iter != args.epochs:
            #         print(
            #             'Round {:3d}, Global train loss: {:.3f}, Global test loss: {:.3f}, Global test accuracy: {:.2f}'.format(
            #                 iter, loss_avg, loss_test, acc_test))
            #     else:
            #         print(
            #             'Final Round, Global train loss: {:.3f}, Global test loss: {:.3f}, Global test accuracy: {:.2f}'.format(
            #                 loss_avg, loss_test, acc_test))
            if iter >= args.epochs - 10 and iter != args.epochs:
                accs10_glob += acc_test / 10

            model_save_path = './save/FedMeta/0.25/accs_Fedavg_lambda_'+str(args.lamb) +str('_') + args.alg + '_' + args.dataset + '_' + str(args.num_users) + '_' + str(
                args.shard_per_user) + '_iter' + str(iter) + '_frac_'+str(args.frac)+'.pt'
            torch.save(net_glob.state_dict(), model_save_path)

    # print('Average accuracy final 10 rounds: {}'.format(accs10))
    # if args.alg == 'fedavg' or args.alg == 'prox':
    #     print('Average global accuracy final 10 rounds: {}'.format(accs10_glob))
    end = time.time()
    print(end - start)
    print(times)
    print(accs)
    base_dir = './save/FedMeta/0.25/accs_Fedavg_lambda_'+str(args.lamb) +str('_') + args.alg + '_' + args.dataset + '_' + str(args.num_users) + '_' + str(
                args.shard_per_user) + '_iterFinal' + '_frac_'+str(args.frac)+ '.csv'
    user_save_path = base_dir
    accs = np.array(accs)
    accs = pd.DataFrame(accs, columns=['accs'])
    accs.to_csv(base_dir, index=False)
