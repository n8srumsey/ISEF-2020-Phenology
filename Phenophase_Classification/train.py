import json
import math
import os
import re

import numpy as np
from skimage.io import imread
from sklearn.utils import shuffle
from tensorflow.keras import Sequential
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import (BatchNormalization, Conv2D, Dense,
                                     Dropout, Flatten, MaxPool2D)
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.metrics import AUC, BinaryAccuracy, Precision, Recall
from tensorflow.keras.regularizers import l1_l2, l2
from tensorflow.keras.utils import Sequence

from data_preprocessing import image_shape

K = 10
DATA_DIR = './Phenophase_Classification/data/'
IMAGES_DIR = './Phenophase_Classification/data/images/'
RESULTS_DIR = './Phenophase_Classification/results/'


# define the data subsets
all_images = np.array(os.listdir(IMAGES_DIR))
if len(all_images) % K != 0:
    all_images = all_images[:-(len(all_images) % K)]
data_partitions = np.split(all_images, K)


"""Define k-fold cross validation generators"""


class Generator(Sequence):
    def __init__(self, img_list, batch_size, shuffle=False):
        self.img_list = img_list
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.x = [IMAGES_DIR + img_name for img_name in self.img_list]

        def to_binary_lable(img_name):
            if 'rising' in img_name:
                return [1.0, 0.0]
            return [0.0, 1.0]
        self.y = [to_binary_lable(img) for img in self.img_list]

    def __len__(self):
        return math.ceil(len(self.img_list) / self.batch_size)

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]
        return np.array([imread(file_name) for file_name in batch_x]), np.array(batch_y)

    def on_epoch_end(self):
        if self.shuffle:
            self.x, self.y = shuffle(self.x, self.y)


def get_generators(num_fold, batch_size, shuffle=False):
    train_imgs = []
    val_imgs = data_partitions[num_fold]
    for i in range(K):
        if i != num_fold:
            train_imgs.extend(data_partitions[i])

    train_gen = Generator(train_imgs, batch_size, shuffle)
    val_gen = Generator(val_imgs, batch_size, shuffle)
    return train_gen, val_gen


# define model
def define_model(k):
    model = Sequential([
        Conv2D(filters=16, kernel_size=(3, 3), strides=(2, 2), activation='relu', use_bias=True, input_shape=image_shape, kernel_regularizer=l1_l2(l1=1e-5, l2=1e-4),
               bias_regularizer=l2(1e-4), activity_regularizer=l2(1e-5)),
        BatchNormalization(),
        MaxPool2D(pool_size=(3, 3), strides=(2, 2)),
        Conv2D(filters=8, kernel_size=(3, 3), strides=(1, 1), activation='relu', padding='same', use_bias=True, kernel_regularizer=l1_l2(l1=1e-5, l2=1e-4), 
               bias_regularizer=l2(1e-4), activity_regularizer=l2(1e-5)),
        BatchNormalization(),
        MaxPool2D(pool_size=(3, 3), strides=(2, 2)),
        Flatten(),
        Dense(128, activation='relu', use_bias=True, kernel_regularizer=l1_l2(l1=1e-5, l2=1e-4), bias_regularizer=l2(1e-4), activity_regularizer=l2(1e-5)),
        Dropout(0.5),
        Dense(64, activation='relu', use_bias=True, kernel_regularizer=l1_l2(l1=1e-5, l2=1e-4), bias_regularizer=l2(1e-4), activity_regularizer=l2(1e-5)),
        Dense(2, activation='sigmoid')
    ])
    if k == None:
        return model
    model.compile(optimizer='adam', loss=BinaryCrossentropy(), metrics=[BinaryAccuracy(threshold=0.5), AUC(), Precision(), Recall()])
    return model


# training parameters
params = {
    # dataset and model architechture
    'k': K,
    'batch_size': 256,
    'shuffle': True,
    'mode': 'binary',

    # training
    'epochs': 5,
}

callbacks = [EarlyStopping(monitor='val_loss', min_delta=0.005, patience=5, mode='min')]


""" Start Training """
if __name__ == '__main__':
    results = {}

    # k-fold cross validation loop
    for k in range(K):
        print('\n\n\n*** STARTING ITERATION {} out of {} ***\n'.format(k+1, K))
        train_gen, val_gen = get_generators(k, batch_size=params['batch_size'], shuffle=params['shuffle'])
        model = define_model(k)
        
        # train
        history = model.fit(train_gen, validation_data=val_gen, epochs=params['epochs'], verbose=1, callbacks=callbacks)

        # save results
        results['iteration_{}'.format(k)] = history.history

    # summarize results
    iteration_summaries = {'loss': [], 'binary_accuracy': [], 'auc': [], 'precision': [], 'recall': [], 'val_loss': [],
               'val_binary_accuracy': [], 'val_auc': [], 'val_precision': [], 'val_recall': []}

    for result in results.values():
        for metric in result.keys():
            metric_name = metric + ''
            if re.search('_\d', metric): metric_name = re.sub('_\d', '', metric_name)
            iteration_summaries[metric_name].append(result[metric][-1])
    
    results['iteration_summaries'] = iteration_summaries

    summary = {'loss': [], 'binary_accuracy': [], 'auc': [], 'precision': [], 'recall': [], 'val_loss': [],
               'val_binary_accuracy': [], 'val_auc': [], 'val_precision': [], 'val_recall': []}
    for metric in results['iteration_summaries'].keys():
        sum = 0
        for entry in results['iteration_summaries'][metric]:
            sum += entry
        ln = float(len(results['iteration_summaries'][metric]))
        summary[metric] = sum / ln
    results['summary'] = summary
        
    results['model_summary'] = []
    define_model(None).summary(print_fn=lambda x: results['model_summary'].append(x))
    
    results['params'] = params

    num_result = len(os.listdir(RESULTS_DIR))
    save_to = RESULTS_DIR + 'result_{}.json'.format(num_result)

    with open(save_to, 'w') as file:
        json.dump(results, file, indent=4)
