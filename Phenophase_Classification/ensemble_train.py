import gc
import json
import os
import re

from tensorflow.keras.callbacks import EarlyStopping
from  tensorflow.keras.backend import clear_session
import tensorflow as tf

from .define_models import define_model
from .generator_dataset import get_generators
from .utils import (BATCH_SIZE, EPOCHS, MODELS_DIR, NB_TRANSFORMATIONS,
                   RESULTS_DIR, TRANSFORM, K)

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


""" Start Training """
if __name__ == '__main__':
    results = {}

    model_save_dir = MODELS_DIR + 'iteration_{}/'.format(len([item for item in os.listdir(MODELS_DIR)]))

    callbacks = [EarlyStopping(monitor='loss', min_delta=0.001, patience=5, mode='min')]

    # k-fikd Cross-Validation Ensemble Training
    for k in range(K):
        print('\n\n\n*** STARTING ITERATION {} out of {} ***\n'.format(k+1, K))
        train_gen, val_gen = get_generators(k, batch_size=params['batch_size'], transform=params['transform_bool'],
                                            nb_transformations=params['nb_transformations'], shuffle=params['shuffle'])
        model = define_model(k)

        # train
        history = model.fit(train_gen, validation_data=val_gen, epochs=params['epochs'], verbose=1, callbacks=callbacks,
                                use_multiprocessing=True, workers=6, max_queue_size=6)

        # save model
        save_dir = model_save_dir + 'k_{}'.format(k)
        model.save(save_dir)

        # save results
        results['iteration_{}'.format(k)] = history.history
        
        # manage memory leaks
        del model, history
        gc.collect()
        clear_session()
        tf.compat.v1.reset_default_graph()
        

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

    # calculate F1 scores
    for entry in results.keys():
        precision, recall, val_precision, val_recall = None, None, None, None
        for metric in results[entry].keys():
            if metric.find('precision') != -1 and metric.find('val_') == -1:
                precision = results[entry][metric]
            elif metric.find('val_precision') != -1:
                val_precision = results[entry][metric]
            elif metric.find('recall') != -1 and metric.find('val_') == -1:
                recall = results[entry][metric]
            elif metric.find('val_recall') != -1:
                val_recall = results[entry][metric]

        def calc_f1_score(presc, rcll):
            if isinstance(precision, list) and isinstance(recall, list):
                f1_scores = []
                for p, r in zip(presc, rcll):
                    if p == 0.0 and r == 0.0:
                        return [0.0 for _ in presc]
                    f1_scores.append(2 * p * r / (p + r))
                return f1_scores
            return 2 * presc * rcll / (presc + rcll)

        f1_score = calc_f1_score(precision, recall)
        val_f1_score = calc_f1_score(val_precision, val_recall)

        results[entry]['f1_score'] = f1_score
        results[entry]['val_f1_score'] = val_f1_score

    results['model_summary'] = []
    define_model(None).summary(print_fn=lambda x: results['model_summary'].append(x))

    results['params'] = params

    num_result = len(os.listdir(RESULTS_DIR))
    save_to = RESULTS_DIR + 'ensemble_result_{}.json'.format(num_result)

    with open(save_to, 'w') as file:
        json.dump(results, file, indent=4)

    print('\n\n *** TRAINING AND EVALUATING FINISHED ***')
