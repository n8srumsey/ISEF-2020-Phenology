"""
Organizes and resizes images from the PhenoCam v2.0 Dataset to be used in the training of a deciduous forest phehnophase classification. 
"""

import os
from PIL import Image
from tqdm import tqdm

directory = './PhenoCam_v2/sorted_images/'
target_directory = './Phenophase_Classification/data/images/'

image_dim = (86, 64)
image_shape = (86, 64, 3)

if __name__=='__main__':
    # sort images classified as 'rising'
    files_in_directory = os.listdir(directory + 'rising')
    for file in tqdm(files_in_directory):
        im = Image.open(directory + 'rising/' + file)
        im = im.resize(image_dim)
        im.save(target_directory + 'rising_' + file)

    # sort images classified as 'falling'
    files_in_directory = os.listdir(directory + 'falling')
    for file in tqdm(files_in_directory):
        im = Image.open(directory + 'falling/' + file)
        im = im.resize(image_dim)
        im.save(target_directory + 'falling_' + file)