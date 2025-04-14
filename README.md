# FCLOnBlockChain

## Table of contents
- [1 Introduction](#1-introduction)
- [2 How to get started](#2-how-to-get-started)
    * [2.1 Setup](#21-setup)
    * [2.2 Usage](#22-usage)
- [3 Supported FL methods](#3-supported-fl-methods)
    * [3.1 Method introduction](#31-method-introduction)
    * [3.2 Method usage](#32-method-usage)
- [4 Supported FCL methods](#4-supported-fcl-methods)
    * [4.1 Method introduction](#41-method-introduction)
    * [4.2 Method usage](#42-method-usage)
## 1 Introduction
For CV application, we supports 5 models:
- [ResNet](https://openaccess.thecvf.com/content_cvpr_2016/html/He_Deep_Residual_Learning_CVPR_2016_paper.html): this model consists of multiple convolutional layers and pooling layers that extract the information in image. Typically, ResNet suffers from gradient vanishing (exploding) and performance degrading when the network is  deep. ResNet thus adds BatchNorm to alleviate gradient vanishing (exploding) and adds residual connection to alleviate the performance degrading.
- [MobileNet](https://arxiv.org/abs/1801.04381): MobileNet is a lightweight convolutional network which widely uses the depthwise separable convolution.
- [DenseNet](https://arxiv.org/pdf/1707.06990.pdf): DenseNet extends ResNet by adding connections between each blocks to aggregate all multi-scale features.
- [WideResNet](https://arxiv.org/pdf/1605.07146): WideResNet (Wide Residual Network) is a deep learning model that builds on the ResNet architecture by increasing the width of residual blocks (using more feature channels) to improve performance and efficiency while reducing the depth of the network.
- [Vit](https://arxiv.org/abs/2010.11929): The Vision Transformer (ViT) applies the Transformer architecture to image recognition tasks. It segments the image into multiple patches, then inputs these small blocks as sequence data into the Transformer model, using the self-attention mechanism to capture global and local information within the image, thereby achieving efficient image classification.

For NLP application, it cupports 6 models:
- [RNN](https://arxiv.org/pdf/1406.1078): RNN (Recurrent Neural Network) is a type of neural network specifically designed for sequential data, excelling at handling time series and natural language with temporal dependencies.
- [LSTM](https://arxiv.org/pdf/1406.1078): LSTM (Long Short-Term Memory) is a special type of RNN that can learn long-term dependencies, suitable for tasks like time series analysis and language modeling.
- [Bert](https://arxiv.org/abs/1810.04805): BERT (Bidirectional Encoder Representations from Transformers) is a pre-trained language representation model based on the Transformer architecture, which captures contextual information in text through deep bidirectional training. The BERT model excels in natural language processing (NLP) tasks and can be used for various applications such as text classification, question answering systems, and named entity recognition.
## 2 How to get started
### 2.1 Setup
**Requirements**
- Edge devices such as Jetson AGX, Jetson TX2, Jetson Xavier NX, Jetson Nano and Rasperry Pi.
- Linux and Windows
- Python 3.6+
- PyTorch 1.9+
- CUDA 10.2+

**Preparing the virtual environment**

1. Create a conda environment and activate it.
   ```shell
   conda create -n FCLOnBlockChain python=3.7
   conda active FCLOnBlockChain
   ```

2. Install PyTorch 1.9+ in the [offical website](https://pytorch.org/). A NVIDIA graphics card and PyTorch with CUDA are recommended.

![image](https://p3-juejin.byteimg.com/tos-cn-i-k3u1fbpfcp/ec360791671f4a4ab322eb4e71cc9e62~tplv-k3u1fbpfcp-zoom-1.image)

3. Clone this repository and install the dependencies.
  ```shell
  git clone https://github.com/LINC-BIT/FCLOnBlockChain.git
  pip install -r requirements.txt
  ```

### 2.2 Usage
Run FCLOnBlockChain:
```shell
python main_multiclient_bc.py --clmethod [clmethod] --dataset [dataset --model [mdoel] 
--model-name [kd_model_name]  --local_bs [local_bs] --lr [lr] --task [task] --epoch [epoch] 
--local_ep [local_ep] --num_users [num_users] --server-gpu [gpu]

example: python main_multiclient_bc.py --clmethod GEM --dataset miniimagenet --model Resnet18 --model-name sixcnn --num_users 10 --server-gpu -1 --kd_epoch 10
```
Arguments:

- `dataset` : the dataset, e.g. `cifar100`, `MiniImageNet`, `TinyImageNet`, `ASC`, `DSC`

- `model`: the model, e.g. `6-Layers CNN`, `ResNet18`, `DenseNet`, `MobiNet`, `RNN`, `LSTM`, `Bert`

- `num_users`: the number of clients

- `lr`: the learning rate

- `task`: the number of tasks

- `epochs`: the number of communications between each client

- `local_ep`:the number of epochs in clients

- `model-name`: name of kd model

- `server-gpu`: GPU id
  
More details refer to `utils/option.py`.

## 3 Supported FL methods
### 3.1 Method introduction
Our system not only implements Loci, but also implements classic and latest federated learning methods with heterogeneous model and clustered federated learning, mainly including the following:
- **[FedMD](https://arxiv.org/abs/2107.08517)**: This paper is from AIR(2017). It uses public datasets to update the distillation model during aggregation. You can find the method description [here](Baselines/FedMD)
- **[FedKD](https://arxiv.org/abs/2003.13461)**: This paper is from AIR(2017). It designs various distillation losses based on the network layer on the client-side. You can find the method description [here](Baselines/FedKD)
- **[FedKEMF](https://proceedings.mlr.press/v139/collins21a.html)**: This paper is from ICML(2021).  It considers merging all teacher networks during aggregation, and uses a common dataset to distill a better server-side global network. You can find the method description [here](Baselines/FedKEMF)
- **[FedGKT](https://proceedings.neurips.cc/paper/2020/hash/a1d4c20b182ad7137ab3606f0e3fc8a4-Abstract.html)** : This paper is from NIPS(2023) .It designs a variant of the alternating minimization approach to train small models on edge nodes and periodically transfer their knowledge by knowledge distillation to a large server-side model. You can find the method description [here](Baselines/FedGKT)
- **[CFL](https://ieeexplore.ieee.org/abstract/document/9174890)** : This paper is from NNLS(Volume: 32, 2020). It divides clients into clusters based on the cosine-similarity of their gridients parameters, and performs global aggregation for clients in the same cluster. You can find the method description [here](Baselines/CFL)
- **[IFCA](https://proceedings.neurips.cc/paper_files/paper/2020/hash/e32cc80bf07915058ce90722ee17bb71-Abstract.html)** : This paper is from NIPS(2020). It estimates the clustering dentity of clients, optimizes the model parameters for each cluster, and also allows parameter sharing among different clusters. You can find the method description [here](Baselines/IFCA)
- **[GradMFL](https://link.springer.com/chapter/10.1007/978-3-030-95384-3_38)** : This paper is from ICAAPP(2021). It introduces a hierarchical cluster to organize clients and supports knowledge transfer among different hierarchies. You can find the method description [here](Baselines/GradMFL)
### 3.2 Method usage
You can find the "main" file in the "baseline" folder corresponding to each method, and then run the method according to the following command

	```shell
 	cd baseline
	python mainXXX.py --task_number=10 --class_number=100 --dataset=cifar100 # XXX is the method name
	```
## 4 Supported FCL methods
### 4.1 Method introduction
- **[FedKNOW](https://ieeexplore.ieee.org/abstract/document/10184531/)**: This paper is from ICDE(2023). It introduces a novel communication-efficient federated learning algorithm that employs adaptive gradient quantization and selective client aggregation to dynamically adjust model updates based on network conditions and client heterogeneity, thereby reducing communication overhead while accelerating convergence. You can find the method description [here](Baselines/FedKNOW)
- **[FedViT](https://www.sciencedirect.com/science/article/abs/pii/S0167739X23004879)**: This paper is from Future Generation Computer Systems (Volume: 154, 2024). It presents a novel integrated optimization framework that combines advanced machine learning with heuristic search methods to dynamically optimize complex industrial systems through adaptive, iterative parameter tuning. You can find the method description [here](Baselines/FedViT)
- **[FedCL](https://ieeexplore.ieee.org/abstract/document/9190968/)**: This paper is from ICIP (2020). It proposes a novel federated learning framework that integrates blockchain technology to ensure secure and decentralized model updates among clients, thereby enhancing data privacy and system robustness. You can find the method description [here](Baselines/FedCL)
- **[FedWEIT](https://proceedings.mlr.press/v139/yoon21b.html?ref=https://githubhelp.com)** : This paper is from ICML(2021). It introduces a novel approach that leverages self-supervised learning to enhance the performance of few-shot learning models by effectively utilizing unlabeled data during the meta-training phase. You can find the method description [here](Baselines/FedWEIT)
- **[Cross-FCL](https://ieeexplore.ieee.org/abstract/document/9960821/)**: This paper is from TMC(Volume: 23, 2024). It proposes a novel federated learning framework that integrates blockchain technology to ensure secure and decentralized model updates among clients, thereby enhancing data privacy and system robustness. You can find the method description [here](Baselines/Cross-FCL)
- **[TFCL](https://openaccess.thecvf.com/content/CVPR2024/html/Wang_Traceable_Federated_Continual_Learning_CVPR_2024_paper.html)** : This paper is from CVPR(2024). It proposes a novel Traceable Federated Continual Learning (TFCL) paradigm, introducing the TagFed framework that decomposes models into marked sub-models for each client task, enabling precise tracing and selective federation to handle repetitive tasks effectively. You can find the method description [here](Baselines/TFCL)

### 4.2 Method usage
You can find the "main" file in the "baseline" folder corresponding to each method, and then run the method according to the following command

	```shell
 	cd baseline
	python mainXXX.py --task_number=10 --class_number=100 --dataset=cifar100 # XXX is the method name
	```