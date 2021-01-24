from tensorflow.keras import Sequential
from tensorflow.keras.layers import (BatchNormalization, Conv2D, Dense,
                                     Dropout, Flatten, MaxPool2D)
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.metrics import AUC, BinaryAccuracy, Precision, Recall
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l1_l2, l2

from data_preprocessing import image_shape

# define model


def define_model(k):
    model = Sequential([
        Conv2D(filters=32, kernel_size=(3, 3), strides=(2, 2), activation='relu', use_bias=True, input_shape=image_shape, kernel_regularizer=l1_l2(l1=1e-5, l2=1e-4),
               bias_regularizer=l2(1e-4), activity_regularizer=l2(1e-5)),
        # Dropout(0.75),
        BatchNormalization(),
        MaxPool2D(pool_size=(3, 3), strides=(2, 2)),
        Conv2D(filters=16, kernel_size=(3, 3), strides=(1, 1), activation='relu', padding='same', use_bias=True, kernel_regularizer=l1_l2(l1=1e-5, l2=1e-4),
               bias_regularizer=l2(1e-4), activity_regularizer=l2(1e-5)),
        BatchNormalization(),
        MaxPool2D(pool_size=(3, 3), strides=(2, 2)),
        Flatten(),
        Dense(128, activation='relu', use_bias=True, kernel_regularizer=l1_l2(l1=1e-5, l2=1e-4), bias_regularizer=l2(1e-4), activity_regularizer=l2(1e-5)),
        Dropout(0.5),
        Dense(64, activation='relu', use_bias=True, kernel_regularizer=l1_l2(l1=1e-5, l2=1e-4), bias_regularizer=l2(1e-4), activity_regularizer=l2(1e-5)),
        Dropout(0.5),
        Dense(2, activation='sigmoid')
    ])

    if k == None:
        return model
    model.compile(optimizer=Adam(), loss=BinaryCrossentropy(), metrics=[BinaryAccuracy(threshold=0.5), AUC(), Precision(), Recall()])
    return model
