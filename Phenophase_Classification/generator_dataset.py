import math
import os
import random

import numpy as np
from skimage.io import imread
from skimage.util import random_noise
from sklearn.utils import shuffle
from tensorflow.keras.utils import Sequence

from data_preprocessing import image_shape
from utils import BATCH_SIZE, IMAGES_DIR, K

"""Define generators"""

# define the data subsets
all_images = np.array(os.listdir(IMAGES_DIR))
if len(all_images) % K != 0:
    all_images = all_images[:-(len(all_images) % K)]
data_partitions = np.split(all_images, K)


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

    def gen_iter(self):
        for idx in range(len(self)):
            batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
            batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]
            yield np.transpose(np.array([imread(file) for file in batch_x]).astype('float32'), (0, 2, 1, 3)), np.array(batch_y).astype('float32')


def get_generators(num_fold=None, batch_size=BATCH_SIZE, transform=True, nb_transformations=16, shuffle=False):
    if num_fold is not None:
        train_imgs = []
        val_imgs = data_partitions[num_fold]
        for i in range(K):
            if i != num_fold:
                train_imgs.extend(data_partitions[i])

        train_gen = Generator(train_imgs, batch_size, transform, nb_transformations, shuffle)
        val_gen = Generator(val_imgs, batch_size, image_transformations=False, shuffle=False)
        return train_gen, val_gen
    else:
        data = []
        for i in range(K):
            data.extend(data_partitions[i])
        return Generator(data, batch_size=batch_size, image_transformations=False)
