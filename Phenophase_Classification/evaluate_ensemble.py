"""Evaluate the ensemble of models trained with k-fold cross validation."""
import os
from statistics import mode

import numpy as np
from tensorflow.keras.models import load_model
from tqdm import tqdm

from .generator_dataset import get_generators
from .utils import MODELS_DIR, RESULTS_DIR


def load_models(path):
    directories = os.listdir(MODELS_DIR + path)
    models = [load_model(directory) for directory in directories]
    return models


def eval_ensemble(models, eval_dataset=get_generators(), mthd_mode=True, mthd_mean=False, mthd_weighted=False, model_results=None, mthd_stacked=False, train_dataset=get_generators()):
    print('\n\n\n ***EVALUATING DATASET ***')

    def eval_mode():
        print('\n   Mode Method:')
        mode_predictions = []
        generator = eval_dataset.gen_iter()
        # loop through batches
        for _ in tqdm(range(len(eval_dataset))):
            x, y = next(generator)
            pred = []
            for model in models:
                output = model.predict(x, batch_size=1)
                pred.append(output[0])
            for i in range(len(pred[0])):
                item_predicitons = [predictions[i] for predictions in pred]
                if mode([np.argmax(item) for item in item_predicitons]) == np.argmax(y):
                    mode_predictions.append(1)
                else:
                    mode_predictions.append(0)
        mode_binary_accuracy = float(np.sum(np.array(mode_predictions)) / len(mode_predictions))
        return mode_binary_accuracy

    def eval_mean():
        print('\n   Mean Method:')
        mean_predictions = []
        generator = eval_dataset.gen_iter()
        # loop through batches
        for _ in tqdm(range(len(eval_dataset))):
            x, y = next(generator)
            pred = []
            for model in models:
                output = model.predict(x, batch_size=1)
                pred.append(output[0])
            for i in range(len(pred[0])):
                item_predicitons = [predictions[i] for predictions in pred]
                mean = np.argmax(np.sum(item_predicitons, axis=0) / len(pred))
                if mean == np.argmax(y):
                    mean_predictions.append(1)
                else:
                    mean_predictions.append(0)
        mean_binary_accuracy = float(np.sum(np.array(mean_predictions)) / len(mean_predictions))
        return mean_binary_accuracy

    def eval_weighted():
        print('\n   Weighted Method:')

        pass

    def eval_stacked():
        print('\n   Stacked Method:')

        pass

    eval_results = {'mode_binary_accuracy': None, 'mean_binary_accuracy': None, 'weighted_binary_accuracy': None, 'stacked_binary_accuracy': None}

    if mthd_mode:
        eval_results['mode_binary_accuracy'] = eval_mode()
    if mthd_mean:
        eval_results['mean_binary_accuracy'] = eval_mean()
    if mthd_weighted:
        eval_results['weighted_binary_accuracy'] = eval_weighted()
    if mthd_stacked:
        eval_results['stacked_binary_accuracy'] = eval_stacked()

    print(eval_results)
    return eval_results
