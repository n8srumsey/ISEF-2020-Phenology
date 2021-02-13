import multiprocessing as mp
import os
import random
from multiprocessing import process

import imageio
import numpy as np
import tensorflow as tf
from skimage.util import random_noise
from tqdm import tqdm

from .data_preprocessing import image_shape
from .utils import (BATCH_SIZE, EFFECTIVE_BATCH_SIZE, NB_TRANSFORMATIONS,
                   TRANSFORM, K)

im_dir = './Phenophase_Classification/data/images/'
target_dir = './Phenophase_Classification/data/'

all_images = np.array(os.listdir(im_dir))
np.random.shuffle(all_images)
all_images = all_images[:-(len(all_images) % K)]
data_partitions = np.split(all_images, K)

def _bytes_feature(value):
                        ## Returns a bytes_list from a string / byte.
                        if isinstance(value, type(tf.constant(0))):  # if value ist tensor
                            value = value.numpy()  # get value of tensor
                        return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def to_binary_label(img_name):
    if 'binary' in img_name:
        return np.array([1.0])
    return np.array([0.0])

def create_all_tfrecords():
    # create TFRecords files
    for k in range(K):
        num_im = len(data_partitions[k])
        print ('Partition ' + str(k))
        if TRANSFORM:
            for bn in tqdm(range(num_im // EFFECTIVE_BATCH_SIZE)):
                images = data_partitions[k][bn*EFFECTIVE_BATCH_SIZE : (bn+1)*EFFECTIVE_BATCH_SIZE]
                x, y = [], []

                with tf.io.TFRecordWriter(target_dir + 'data_{}.tfrecord'.format(k)) as file_writer:
                    for image in images:
                        im = imageio.imread(im_dir + image, as_gray=False, pilmode='RGB').astype(np.float)
                        label = to_binary_label(image)
                        x.append(im)
                        y.append(label)
                        
                        for _ in range(NB_TRANSFORMATIONS - 1):
                            new_im = imageio.imread(im_dir + image, as_gray=False, pilmode='RGB').astype(np.float)
                            # random flip
                            if bool(random.getrandbits(1)): new_im = np.fliplr(new_im)
                            if bool(random.getrandbits(1)): new_im = np.flipud(new_im)

                            # horizontral translation
                            new_im = np.roll(new_im, shift=int(np.random.normal(0.0, image_shape[0]/6)), axis=1)

                            # random brightness
                            new_im = new_im + np.random.normal(0.0, 50.0) / 255.0

                            # random noise
                            if bool(random.getrandbits(1)): new_im = random_noise(new_im, clip=True)

                            x.append(im)
                            y.append(label)

                    x_tnsr = tf.convert_to_tensor(x, dtype=tf.float32)
                    serialized_x = tf.io.serialize_tensor(x_tnsr)
                    y_tnsr = tf.convert_to_tensor(y, dtype=tf.float32)
                    serialized_y = tf.io.serialize_tensor(y_tnsr)

                    record_bytes = tf.train.Example(features=tf.train.Features(feature={
                        'x': _bytes_feature(serialized_x),
                        'y': _bytes_feature(serialized_y),
                    })).SerializeToString()
                    file_writer.write(record_bytes)
        if not TRANSFORM:
            for bn in tqdm(range(num_im // BATCH_SIZE)):
                images = data_partitions[k][bn*BATCH_SIZE : (bn+1)*BATCH_SIZE]
                x, y = [], []
                with tf.io.TFRecordWriter(target_dir + 'data_{}.tfrecord'.format(k)) as file_writer:
                    for image in images:
                        im = imageio.imread(im_dir + image, as_gray=False, pilmode='RGB').astype(np.float)
                        label = to_binary_label(image)

                        x.append(im)
                        y.append(label)

                    x_tnsr = tf.convert_to_tensor(x, dtype=tf.float32)
                    serialized_x = tf.io.serialize_tensor(x_tnsr)
                    y_tnsr = tf.convert_to_tensor(y, dtype=tf.float32)
                    serialized_y = tf.io.serialize_tensor(y_tnsr)

                    record_bytes = tf.train.Example(features=tf.train.Features(feature={
                        'x': _bytes_feature(serialized_x),
                        'y': _bytes_feature(serialized_y),
                    })).SerializeToString()
                    file_writer.write(record_bytes)

def create_single_tfrecord(k):
    num_im = len(data_partitions[k])
    print ('Partition ' + str(k))
    if TRANSFORM:
        for bn in range(num_im // EFFECTIVE_BATCH_SIZE):
            images = data_partitions[k][bn*EFFECTIVE_BATCH_SIZE : (bn+1)*EFFECTIVE_BATCH_SIZE]
            x, y = [], []

            with tf.io.TFRecordWriter(target_dir + 'data_{}.tfrecord'.format(k)) as file_writer:
                for image in images:
                    im = imageio.imread(im_dir + image, as_gray=False, pilmode='RGB').astype(np.float)
                    label = to_binary_label(image)
                    x.append(im)
                    y.append(label)
                    
                    for _ in range(NB_TRANSFORMATIONS - 1):
                        new_im = imageio.imread(im_dir + image, as_gray=False, pilmode='RGB').astype(np.float)
                        # random flip
                        if bool(random.getrandbits(1)): new_im = np.fliplr(new_im)
                        if bool(random.getrandbits(1)): new_im = np.flipud(new_im)

                        # horizontral translation
                        new_im = np.roll(new_im, shift=int(np.random.normal(0.0, image_shape[0]/6)), axis=1)

                        # random brightness
                        new_im = new_im + np.random.normal(0.0, 50.0) / 255.0

                        # random noise
                        if bool(random.getrandbits(1)): new_im = random_noise(new_im, clip=True)

                        x.append(im)
                        y.append(label)

                x_tnsr = tf.convert_to_tensor(x, dtype=tf.float32)
                serialized_x = tf.io.serialize_tensor(x_tnsr)
                y_tnsr = tf.convert_to_tensor(y, dtype=tf.float32)
                serialized_y = tf.io.serialize_tensor(y_tnsr)

                record_bytes = tf.train.Example(features=tf.train.Features(feature={
                    'x': _bytes_feature(serialized_x),
                    'y': _bytes_feature(serialized_y),
                })).SerializeToString()
                file_writer.write(record_bytes)
    if not TRANSFORM:
        for bn in tqdm(range(num_im // BATCH_SIZE)):
            images = data_partitions[k][bn*BATCH_SIZE : (bn+1)*BATCH_SIZE]
            x, y = [], []
            with tf.io.TFRecordWriter(target_dir + 'data_{}.tfrecord'.format(k)) as file_writer:
                for image in images:
                    im = imageio.imread(im_dir + image, as_gray=False, pilmode='RGB').astype(np.float)
                    label = to_binary_label(image)

                    x.append(im)
                    y.append(label)

                x_tnsr = tf.convert_to_tensor(x, dtype=tf.float32)
                serialized_x = tf.io.serialize_tensor(x_tnsr)
                y_tnsr = tf.convert_to_tensor(y, dtype=tf.float32)
                serialized_y = tf.io.serialize_tensor(y_tnsr)

                record_bytes = tf.train.Example(features=tf.train.Features(feature={
                    'x': _bytes_feature(serialized_x),
                    'y': _bytes_feature(serialized_y),
                })).SerializeToString()
                file_writer.write(record_bytes)

# Read TFRecord file
def _parse_tfr_element(element):
    parse_dic = {'x': tf.io.FixedLenFeature([], tf.string),
                 'y': tf.io.FixedLenFeature([], tf.string)}
    example = tf.io.parse_single_example(element, parse_dic)

    x = example['x']  # get byte string
    y = example['y']
    X = tf.io.parse_tensor(x, out_type=tf.float32)  # restore 2D array from byte string
    Y = tf.io.parse_tensor(y, out_type=tf.float32)
    return X, Y


def load_dataset(tfrecord_filename, shuffle=False, batch_size=1, buffer_size=256, repeat_count=1):
    tfr_dataset = tf.data.TFRecordDataset(tfrecord_filename)
    dataset = tfr_dataset.map(_parse_tfr_element)
    if shuffle: dataset = dataset.shuffle(buffer_size=buffer_size)
    dataset = dataset.repeat(repeat_count)
    dataset = dataset.batch(batch_size)
    return dataset

multiprocessing = False
create_new_tfrecords = False
test_tfrecords = False

if __name__=='__main__':
    if multiprocessing and create_new_tfrecords: 
        processes = [mp.Process(target=create_single_tfrecord, args=(k,)) for k in range(K)]
        for p in processes: p.start()
        for p in processes: p.join()
    elif create_new_tfrecords: create_all_tfrecords()
    if test_tfrecords:
        # print out
        filenames = [os.path.join(target_dir, filename) for filename in os.listdir(target_dir) if filename.endswith('.tfrecord')]

        for batch in load_dataset(filenames):
            # print function
            print()
