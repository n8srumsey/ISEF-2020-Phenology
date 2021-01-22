import json
import math
import os
import random
import re

import numpy as np
from skimage.io import imread
from skimage.util import random_noise
from sklearn.utils import shuffle
from tensorflow.keras import Sequential
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import (BatchNormalization, Conv2D, Dense,
                                     Dropout, Flatten, MaxPool2D)
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.metrics import AUC, BinaryAccuracy, Precision, Recall
from tensorflow.keras.regularizers import l1_l2, l2
from tensorflow.keras.utils import Sequence

from utils import K, BATCH_SIZE, TRANSFORM, NB_TRANSFORMATIONS
from data_preprocessing import image_shape
from tfdataset_creation import load_dataset


DATA_DIR = './Phenophase_Classification/data/'
IMAGES_DIR = './Phenophase_Classification/data/images/'
RESULTS_DIR = './Phenophase_Classification/results/'


# define the data subsets
all_images = np.array(os.listdir(IMAGES_DIR))
if len(all_images) % K != 0:
    all_images = all_images[:-(len(all_images) % K)]
data_partitions = np.split(all_images, K)
tf_data_partitions = [os.path.join(DATA_DIR, filename) for filename in os.listdir(DATA_DIR) if filename.endswith('.tfrecord')]


"""Define k-fold cross validation generators"""


class Generator(Sequence):
    def __init__(self, img_list, batch_size, image_transformations=True, nb_transformations=16, shuffle=False):
        self.img_list = img_list
        self.batch_size = batch_size
        self.effective_batch_size = int(batch_size / nb_transformations)
        self.image_transformations = image_transformations
        self.nb_transformations = nb_transformations
        self.shuffle = shuffle
        self.x = [IMAGES_DIR + img_name for img_name in self.img_list]

        def to_binary_lable(img_name):
            if 'rising' in img_name:
                return [1.0, 0.0]
            return [0.0, 1.0]
        self.y = [to_binary_lable(img) for img in self.img_list]

    def __len__(self):
        if self.image_transformations:
            return math.ceil(len(self.img_list) / self.effective_batch_size)
        return math.ceil(len(self.img_list) / self.batch_size)

    def __getitem__(self, idx):
        if self.image_transformations:
            base_batch_x = self.x[idx * self.effective_batch_size:(idx + 1) * self.effective_batch_size]
            base_batch_y = self.y[idx * self.effective_batch_size:(idx + 1) * self.effective_batch_size]

            batch_x = []
            batch_y = []

            # image augmentation (num transformations per image, rotation, translation, brightness_range, {fill mode}, flips, zoom)
            for im, label in zip(base_batch_x, base_batch_y):
                image = imread(im)
                batch_x.append(image)
                batch_y.append(label)
                for _ in range(self.nb_transformations - 1):
                    new_im = imread(im)

                    # random flip
                    if bool(random.getrandbits(1)):
                        new_im = np.fliplr(new_im)
                    if bool(random.getrandbits(1)):
                        new_im = np.flipud(new_im)

                    # horizontral translation
                    new_im = np.roll(new_im, shift=int(np.random.normal(0.0, image_shape[0]/6)), axis=1)

                    # random brightness
                    new_im = new_im + np.random.normal(0.0, 50.0) / 255.0

                    # random noise
                    if bool(random.getrandbits(1)):
                        new_im = random_noise(new_im, clip=True)

                    batch_x.append(new_im)
                    batch_y.append(label)

            return np.array(batch_x).astype('float32'), np.array(batch_y).astype('float32')
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]
        return np.array([imread(file) for file in batch_x]).astype('float32'), np.array(batch_y).astype('float32')

    def on_epoch_end(self):
        print('\n\n\n')  # if multiproccessing is on
        if self.shuffle:
            self.x, self.y = shuffle(self.x, self.y)


def get_generators(num_fold, batch_size, transform=True, nb_transformations=16, shuffle=False):
    train_imgs = []
    val_imgs = data_partitions[num_fold]
    for i in range(K):
        if i != num_fold:
            train_imgs.extend(data_partitions[i])

    train_gen = Generator(train_imgs, batch_size, transform, nb_transformations, shuffle)
    val_gen = Generator(val_imgs, batch_size, False, shuffle)
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
    'batch_size': BATCH_SIZE,
    'transform_bool': TRANSFORM,
    'nb_transformations': NB_TRANSFORMATIONS,
    'shuffle': True,
    'tf_dataset': True,

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
        if not params['tf_dataset']:
            train_gen, val_gen = get_generators(k, batch_size=params['batch_size'], transform=params['transform_bool'],
                                                nb_transformations=params['nb_transformations'], shuffle=params['shuffle'])
            model = define_model(k)
            
            # train
            history = model.fit(train_gen, validation_data=val_gen, epochs=params['epochs'], verbose=1, callbacks=callbacks,
                                use_multiprocessing=True, workers=6)

        else:
            train_partitions = tf_data_partitions.copy()
            val_partition = train_partitions[k]
            del train_partitions[k]
            train_dataset = load_dataset(train_partitions)
            val_datasaet = load_dataset(val_partition)
            model = define_model(k)

            #train
            history = model.fit(train_dataset, validation_data=val_datasaet, epochs=params['epochs'], verbose=1, callbacks=callbacks,
                                use_multiprocessing=True, workers=6)

        # save results
        results['iteration_{}'.format(k)] = history.history

    # summarize results
    iteration_summaries = {'loss': [], 'binary_accuracy': [], 'auc': [], 'precision': [], 'recall': [], 'val_loss': [],
                           'val_binary_accuracy': [], 'val_auc': [], 'val_precision': [], 'val_recall': []}

    for result in results.values():
        for metric in result.keys():
            metric_name = metric + ''
            if re.search('_\d', metric):
                metric_name = re.sub('_\d', '', metric_name)
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
