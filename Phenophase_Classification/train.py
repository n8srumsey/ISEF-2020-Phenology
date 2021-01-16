import os
import math
import json
import uuid
import numpy as np

from skimage.io import imread
from sklearn.utils import shuffle

from keras import Sequential
from keras.layers import BatchNormalization, Conv2D, Dense, Dropout, Flatten, MaxPool2D
from keras.losses import BinaryCrossentropy
from keras.metrics import AUC, BinaryAccuracy, Precision, Recall
from keras.utils import Sequence
from keras.callbacks import History, EarlyStopping

from data_preprocessing import image_shape


K = 10
DATA_DIR = './Phenophase_Classification/data/'
IMAGES_DIR = './Phenophase_Classification/data/images/'
RESULTS_DIR = './Phenophase_Classification/results/'


# define the data subsets
all_images = np.array(os.listdir(IMAGES_DIR))
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
def define_model():
    model = Sequential([
        Conv2D(filters=16, kernel_size=(3, 3), strides=(2, 2), activation='relu', input_shape=image_shape),
        BatchNormalization(),
        MaxPool2D(pool_size=(3, 3), strides=(2, 2)),
        Conv2D(filters=8, kernel_size=(3, 3), strides=(1, 1), activation='relu', padding="same"),
        BatchNormalization(),
        MaxPool2D(pool_size=(3, 3), strides=(2, 2)),
        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(64, activation='relu'),
        Dense(2, activation='sigmoid')
    ])
    model_summary = model.summary()
    model.compile(optimizer='adam', loss=BinaryCrossentropy(), metrics=[BinaryAccuracy(threshold=0.5), AUC(), Precision(), Recall()])
    return model, model_summary


# training parameters
params = {
    # dataset and model architechture
    'batch_size': 256,
    'shuffle': True,
    'mode': 'binary',

    # training
    'epochs': 3,

}

callbacks = [History(),
             EarlyStopping(monitor='val_binary_accuracy', min_delta=0.005, patience=3, mode='max', baseline=0.8),
             ]

if __name__ == '__main__':
    results = {}

    # k-fold cross validation loop
    for k in range(K):
        train_gen, val_gen = get_generators(k, batch_size=params['batch_size'], shuffle=params['shuffle'])
        model, model_summary = define_model()
        results['model_summary'] = model_summary

        # train
        history = model.fit(train_gen, validation_data=val_gen, epochs=params['epochs'], verbose=1, callbacks=callbacks)

        # save results
        results['iteration_{}'.format(k)] = history.history

    # summarize results
    summary = {'loss': [], 'binary_accuracy': [], 'auc': [], 'precision': [], 'recall': [], 'val_loss': [],
               'val_binary_accuracy': [], 'val_auc': [], 'val_precision': [], 'val_recall': []}
    for result in results.values():
        for metric in result.keys():
            summary[metric].append(result[metric][-1])
    results['summary'] = summary

    instance_uuid = uuid.uuid1()[:8]
    results['uuid'] = instance_uuid

    with open(RESULTS_DIR + instance_uuid + '_results.json', 'w') as file:
        json.dumps(results, file, indent=4)
