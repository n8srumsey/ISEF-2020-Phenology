import json
import os
import re

from tensorflow.keras.callbacks import EarlyStopping

from .define_models import define_model
from .generator_dataset import get_generators
from .utils import (BATCH_SIZE, EPOCHS, NB_TRANSFORMATIONS, RESULTS_DIR,
                   TRANSFORM, K)

# training parameters
params = {
    # dataset and model architechture
    'k': K,
    'batch_size': BATCH_SIZE,
    'transform_bool': TRANSFORM,
    'nb_transformations': NB_TRANSFORMATIONS,
    'shuffle': True,

    # training
    'epochs': EPOCHS,
}

callbacks = [EarlyStopping(monitor='val_loss', min_delta=0.005, patience=5, mode='min')]


""" Start Training """
if __name__ == '__main__':
    results = {}

    # k-fold cross validation loop
    for k in range(K):
        print('\n\n\n*** STARTING ITERATION {} out of {} ***\n'.format(k+1, K))
        train_gen, val_gen = get_generators(k, batch_size=params['batch_size'], transform=params['transform_bool'],
                                            nb_transformations=params['nb_transformations'], shuffle=params['shuffle'])
        model = define_model(k)

        # train
        history = model.fit(train_gen, validation_data=val_gen, epochs=params['epochs'], verbose=1, callbacks=callbacks,
                            use_multiprocessing=True, workers=8)

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
    save_to = RESULTS_DIR + 'kfold_result_{}.json'.format(num_result)

    with open(save_to, 'w') as file:
        json.dump(results, file, indent=4)
