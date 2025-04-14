#!/bin/bash

conda activate <> # your enviroment
cd ClientTrain
python main_multiclient_bc.py --clmethod GEM --dataset miniimagenet --model Resnet18 --model-name sixcnn --num_users 10 --server-gpu -1 --kd_epoch 10