import os
import json

if __name__ == '__main__':
    data_directory = './Phenophase_Classification/phenocam_data/'
    files_in_directory = os.listdir(data_directory)
    filtered_meta_files = [file for file in files_in_directory if file.endswith("meta.json")]
    filtered_img_files = [file for file in files_in_directory if file.endswith("imgs.json")]

    for site in filtered_meta_files:
        with open(data_directory + site, 'r') as f:
            sitename = json.load(f)['']
            longname = json.load(f)['']
            # save site
        for img_file in files_in_directory:
            if img_file[:img_file.find('_')] == sitename:
                with open(data_directory + img_file, 'r') as foo:
                    img_list = json.load(f)['img_file_names']
                for img in img_list:
                    img_path_to = '../' + img
                    # find parent site object??
                    # get date_time (as datetime object) from filename
                    # use Tensorflow model to determine is_rising
                    # save image


    # loop through each image corresponding to a specific site, and then calculate the transition dates based off of transitioning from rising to falling to rising
