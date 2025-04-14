from operator import itemgetter
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from Agg.AggModel.sixcnn import SixCNN
from Agg.Datasets import ServerDataset, get_server_dataset
from Agg.OTFusion import utils, parameters, wasserstein_ensemble
from random import sample
import copy

from ClientTrain.utils.logger import get_logger

logger = get_logger()

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
class FedDag():
    def __init__(self, center_nums, candidate_nums, datasize=None, sample_num=5, dataname=None, output=100, model=None):
        if model is not None:
            self.center_models = [{'client': 1, 'model': copy.deepcopy(model)} for i in
                                  range(center_nums)]
            self.candidate_models = [copy.deepcopy(model) for i in range(candidate_nums)]
        else:
            self.center_models = [{'client':1,'model':SixCNN(datasize,outputsize=output)} for i in range(center_nums)]
            self.candidate_models = [SixCNN(datasize,output) for i in range(candidate_nums)]
        self.select_his_num = candidate_nums - center_nums
        self.output=output
        self.sample_num = sample_num
        self.agg_args = parameters.get_parameters()
        self.dataname=dataname
        # TODO device选择可能有问题
        # self.device = torch.device("cuda:"+str(self.agg_args.server_gpu))
        self.device = torch.device('cuda:{}'.format(self.agg_args.server_gpu) if torch.cuda.is_available() and self.agg_args.server_gpu != -1 else 'cpu')
        self.k = 4
        self.his_knowledge = []
        # if sample_type is None:
        #     dataset = get_server_dataset(sample_num,name='CIFAR100')
        #     self.dataloader = DataLoader(dataset,batch_size=1, shuffle=False)

    def decode_candidate_model(self, model, encode_dict):
        encode_flag = True
        for k in encode_dict.keys():
            if len(encode_dict[k]) == 1:
                encode_flag = False
            break
        if encode_flag:
            print('decode')
            for name, parameter in model.named_parameters():
                cur_all_data = torch.flatten(parameter.data)
                cur_position = encode_dict[name]['position']
                big_weight = encode_dict[name]['weight']
                new_weight = torch.zeros(cur_all_data.shape)
                new_weight.scatter_(0, cur_position, big_weight)
                parameter.data = new_weight.view(parameter.data.shape)
        else:
            model.load_state_dict(encode_dict)
        return model

    def upload_model(self, all_models):
        """
        将模型集合1 self.center_models和模型集合2 self.candidate_models清空, 
        然后将模型上传至模型集合1和模型集合2中, 模型集合1表示聚类中心模型, 模型集合2表示
        被聚类模型, 但还未进行聚类
        """
        center_index = 0
        candidate_index = 0
        self.number_id_map = {}
        for client in all_models:
            client_id = client['client']
            model_dict = client['models']
            # self.center_models和self.candidate_models不会包含上轮训练信息
            # 将模型加载到中心模型集合
            self.center_models[center_index]['model'].load_state_dict(model_dict)
            self.center_models[center_index]['model'] = self.center_models[center_index]['model'].to(self.device)
            self.center_models[center_index]['client'] = client_id
            center_index += 1

             # 将同样的模型加载到候选模型集合
            self.candidate_models[candidate_index].load_state_dict(model_dict)
            self.candidate_models[candidate_index] = self.candidate_models[candidate_index].to(self.device)
            self.number_id_map[candidate_index] = client_id
            candidate_index += 1
        if self.select_his_num >= len(self.his_knowledge):
            for know in self.his_knowledge:
                # 根据know对self.candidate_models[candidate_index]中的部分参数进行解码
                self.candidate_models[candidate_index] = self.decode_candidate_model(self.candidate_models[candidate_index], know)
                self.candidate_models[candidate_index] = self.candidate_models[candidate_index].to(self.device)
                candidate_index += 1
        else:
            select_his_know = sample(self.his_knowledge, self.select_his_num)
            for know in select_his_know:
                # 根据know对self.candidate_models[candidate_index]中的部分参数进行解码
                self.candidate_models[candidate_index] = self.decode_candidate_model(
                    self.candidate_models[candidate_index], know)
                self.candidate_models[candidate_index] = self.candidate_models[candidate_index].to(self.device)
                candidate_index += 1
        # 返回最终的候选模型数量
        return candidate_index

    def upload_dataset(self,task):
        """
        将总数据集上传至self.dataloader
        """
        dataset = get_server_dataset(self.sample_num,name=self.dataname,t=task)
        if self.dataname =='MiniGC':
            self.dataloader = dataset
        else:
            self.dataloader = DataLoader(dataset,batch_size=1, shuffle=False)
            
    def select_model(self, task: int, model_num: int):
        """
            聚类, 根据任务task从self.candidate_models集合的候选模型中选择与self.center_models集合中中心模型最相似的模型;
            返回所有中心模型信息列表, 列表每个单位的模型信息中包含了一个模型、client_id和一个similarity列表, similarity列表中包含了候选模型编号和相似度
            参数:
                task: int当前任务号
                model_num: 候选模型的数量
            返回: [{'model':nn.Module, 'client': int id, 'similarity':[{'number':number,'id':id,'sim':loss}, ...] },...]
        """
        # 聚合数
        agg_num = self.k
        if model_num < self.k:
            agg_num = model_num
        
        # 遍历所有中心集中的模型, 选择候选模型
        select_models=[]
        # for model_dict in self.center_models:
        for i in range(model_num):
            model_dict = self.center_models[i]
            cur_center = model_dict['model']
            cur_center.eval()

            # 初始化相似度列表
            similarity=[]

            # 遍历所有候选集中的候选模型, 使用数据集评估得到模型的loss, loss越小越和中心模型接近
            # for number, cur_candidate in enumerate(self.candidate_models):
            for number in range(model_num):
                cur_candidate = self.candidate_models[number]
                if number < model_num:
                    loss=0
                    cur_candidate.eval()
                    for x in self.dataloader:
                        # 模型的 前向传播逻辑 需要根据不同的task生成不同的输出
                        cen_y = cur_center(x.to(self.device), task)
                        can_y = cur_candidate(x.to(self.device), task)
                        loss += MultiClassCrossEntropy(cen_y,can_y)
                    similarity.append({'number':number, 'id':self.number_id_map[number], 'sim':loss})

            # 记录候选模型编号和相似度
            similarity = sorted(similarity, key=itemgetter('sim'), reverse=False)
            # 保存排序结果
            model_dict['similarity']=similarity[0:agg_num]
            select_models.append(model_dict)
        return select_models

    def update(self, all_models, task: int):
        """
        return: [ {'client':client_id,'model':geometric_model.state_dict()}, ... ]
        """
        # agg_num指模型数量
        
        agg_num = self.upload_model(all_models)

        # self.upload_dataset(task)
        dataset = get_server_dataset(self.sample_num,name=self.dataname,t=task)
        if self.dataname =='MiniGC':
            self.dataloader = dataset
        else:
            self.dataloader = DataLoader(dataset,batch_size=1, shuffle=False)

        # 使用数据计算相似度
        select_models = self.select_model(task, agg_num)

        similarity_result = [{"id":item["client"], "similarity":item["similarity"]} for item in select_models]
        # print("similarity_result:", similarity_result)
        logger.info("similarity_result:"+str(similarity_result))
        # exit()

        agg_models = self.aggregate_model(select_models)

        return agg_models
    

    def calculate_similarity(self, all_models: list, task: int):
        """
        all_models: [{'client':idx, 'models': weight},...]
        return: [{'model':nn.Module, 'client': int id, 'similarity':[{'number':number,'id':id,'sim':loss}, ...] },...]
        """
        # agg_num指模型数量
        
        agg_num = self.upload_model(all_models)

        # self.upload_dataset(task)
        dataset = get_server_dataset(self.sample_num,name=self.dataname,t=task)
        if self.dataname =='MiniGC':
            self.dataloader = dataset
        else:
            self.dataloader = DataLoader(dataset,batch_size=1, shuffle=False)

        # 使用数据计算相似度
        select_models = self.select_model(task, agg_num)

        similarity_result = [{"id":item["client"], "similarity":item["similarity"]} for item in select_models]
        # print("similarity_result:", similarity_result)
        logger.info("similarity_result:"+str(similarity_result))

        return select_models


    def aggregate_model(self,select_models):
        """
        根据similarity查找相似模型, 然后将相似模型聚合至中心模型, 然后将中心模型和client_id加入列表中, 返回列表
        select_models: [{'model':objct, 'client_id': xx, 'similarity':[{'number':number,'sim':loss}, ...] },...]
        return: [ {'client':client_id,'model':geometric_model.state_dict()}, ... ]
        """
        agg_models=[]
        for select_model in select_models:
            center_model = select_model['model']
            client_id = select_model['client']
            candidate_models = [self.candidate_models[i['number']] for i in select_model['similarity']]
            # center_activation = utils.get_model_activations(self.agg_args, [center_model], dataloader=self.dataloader)
            candidate_activations  = utils.get_model_activations(self.agg_args, candidate_models, dataloader=self.dataloader)
            # 中心模型
            geometric_model = center_model
            for candidate_model, candidate_activation in zip(candidate_models,candidate_activations):
                geometric_activation = utils.get_model_activations(self.agg_args, [geometric_model], dataloader=self.dataloader)
                fusion_models = [candidate_model , geometric_model]
                fusion_activations = {0: candidate_activations[candidate_activation],1:geometric_activation[0]}
                _, geometric_model = wasserstein_ensemble.geometric_ensembling_modularized(self.agg_args, fusion_models,
                                                                                           self.dataloader,
                                                                                           self.dataloader,
                                                                                           fusion_activations,output=self.output)

            agg_models.append({'client':client_id,'model':geometric_model.state_dict()})



            # if type(center_activation) == type([]):
            #     all_activations = [[candidate_activation, center_activation] for candidate_activation in candidate_activations]
            # else:
            #     all_activations = [{0:candidate_activations[candidate_activation], 1:center_activation[0]} for candidate_activation in candidate_activations]
            # all_models = [[candidate_model, center_model] for candidate_model in candidate_models]
            # for activations, models in zip(all_activations,all_models):
            #     _, geometric_model = wasserstein_ensemble.geometric_ensembling_modularized(self.agg_args, models,
            #                                                                                        self.dataloader,
            #                                                                                        self.dataloader,
            #                                                                                        activations)
            #     agg_models.append(geometric_model)
        return agg_models


    def aggregate_model_test(self, center_model, candidate_models):
        """
        测试将其它模型聚合到一个模型的效果
        """
        dataset = get_server_dataset(self.sample_num,name=self.dataname)
        if self.dataname =='MiniGC':
            self.dataloader = dataset
        else:
            self.dataloader = DataLoader(dataset,batch_size=1, shuffle=False)

        candidate_activations  = utils.get_model_activations(self.agg_args, candidate_models, dataloader=self.dataloader)
        # 中心模型
        geometric_model = center_model
        for candidate_model, candidate_activation in zip(candidate_models,candidate_activations):
            geometric_activation = utils.get_model_activations(self.agg_args, [geometric_model], dataloader=self.dataloader)
            fusion_models = [candidate_model , geometric_model]
            fusion_activations = {0: candidate_activations[candidate_activation],1:geometric_activation[0]}
            _, geometric_model = wasserstein_ensemble.geometric_ensembling_modularized(self.agg_args, fusion_models,
                                                                                        self.dataloader,
                                                                                        self.dataloader,
                                                                                        fusion_activations,output=self.output)


        return geometric_model.state_dict()


    def add_history(self,client_dict):
        self.his_knowledge.append(client_dict)





