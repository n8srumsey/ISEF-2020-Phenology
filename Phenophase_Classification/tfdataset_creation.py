import tensorflow as tf
import numpy as np
import imageio
import os
from tqdm import tqdm

from train import K

BATCH_SIZE = 64

im_dir = './Phenophase_Classification/data/images/'
target_dir = './Phenophase_Classification/data/'


def create_tfrecords_dataset():
    all_images = np.array(os.listdir(im_dir))
    np.random.shuffle(all_images)
    all_images = all_images[:-(len(all_images) % K)]
    data_partitions = np.split(all_images, K)

    # create TFRecords dataset
    for k in range(K):
        num_im = len(data_partitions[k])
        print ('Partition ' + str(k))
        for bn in tqdm(range(num_im // BATCH_SIZE)):
            images = data_partitions[k][bn*BATCH_SIZE : (bn+1)*BATCH_SIZE]
            x, y = [], []
            with tf.io.TFRecordWriter(target_dir + 'data_{}.tfrecord'.format(k)) as file_writer:
                for image in images:
                    def to_binary_label(img_name):
                        if 'binary' in img_name:
                            return np.array([1.0])
                        return np.array([0.0])

                    im = imageio.imread(im_dir + image, as_gray=False, pilmode='RGB').astype(np.float)
                    label = to_binary_label(image)

                    x.append(im)
                    y.append(label)

                x_tnsr = tf.convert_to_tensor(x, dtype=tf.float32)
                serialized_x = tf.io.serialize_tensor(x_tnsr)
                y_tnsr = tf.convert_to_tensor(y, dtype=tf.float32)
                serialized_y = tf.io.serialize_tensor(y_tnsr)

                def _bytes_feature(value):
                    ## Returns a bytes_list from a string / byte.
                    if isinstance(value, type(tf.constant(0))):  # if value ist tensor
                        value = value.numpy()  # get value of tensor
                    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

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


def load_dataset(tfrecord_filename):
    tfr_dataset = tf.data.TFRecordDataset(tfrecord_filename)
    dataset = tfr_dataset.map(_parse_tfr_element)
    return dataset


# create_tfrecords_dataset()

test_tfrecords = True
if test_tfrecords:
    # print out
    filenames = [os.path.join(target_dir, filename) for filename in os.listdir(target_dir) if filename.endswith('.tfrecord')]

    for batch in tf.data.TFRecordDataset(filenames).map(_parse_tfr_element):
        # print function
        print(batch[0].shape)
