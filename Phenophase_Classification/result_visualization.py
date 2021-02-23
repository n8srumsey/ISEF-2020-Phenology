import json
import os
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

results_folder_path = "./Phenophase_Classification/results"
results = sorted(os.listdir(results_folder_path))

jsons = []
for file_name in results:
    file_path = os.path.join(results_folder_path, file_name)
    with open(file_path) as file:
        j = json.load(file)
    jsons.append(j)

def get_data():

    metrics = ["loss", "binary_accuracy", "auc", "precision", "recall", "f1_score"]
    titles = ['Training Dataset Cross-Entropy Loss', 'Training Dataset Binary Accuracy', 'Training Dataset AUC', 'Training Dataset Precision', 'Training Dataset Recall', 'Validation Dataset Cross-Entropy Loss', 
              'Validation Dataset Binary Accuracy', 'Validation Dataset AUC', 'Validation Dataset Precision', 'Validation Dataset Recall', 'Training Dataset F1 Score', 'Validation Dataset F1 Score']

    xlabel = 'Epoch'
    ylabel = '{train_val} {metric_title}'
    title = '{train_val} {metric_title} vs. Epoch'

    data = []

    for r, results in enumerate(jsons):
        iterations = [key for key in results.keys() if bool(re.search(r'\d', key))]
        main_metrics = [metric for metric in results[iterations[0]].keys()]
        
        for i, iteration in enumerate(iterations):
            metrics = [metric for metric in results[iteration].keys()]
            iteration_results = {'Training Iteration': r, 'Fold': i+1}

            for e in range(len(results[iteration][metrics[0]])):
                if e > 100: continue
                epoch_results = {'Epoch': e + 1}
                for m, metric in enumerate(metrics):
                    epoch_results[titles[m]] = results[iteration][metric][e]
                epoch_data = {**iteration_results, **epoch_results}
                data.append(epoch_data)
    df = pd.DataFrame(data)
    return df

def plot_learning_curves(df):
    sns.set_theme()
    
    titles = ['Training Dataset Cross-Entropy Loss', 'Training Dataset Binary Accuracy', 'Training Dataset AUC', 'Training Dataset Precision', 'Training Dataset Recall', 'Validation Dataset Cross-Entropy Loss', 
              'Validation Dataset Binary Accuracy', 'Validation Dataset AUC', 'Validation Dataset Precision', 'Validation Dataset Recall', 'Training Dataset F1 Score', 'Validation Dataset F1 Score']

    xlabel = 'Epoch'
    ylabel = '{}'
    plot_title = '{} vs. Epochs'    
    
    for i in range(len(titles)):
        _, ax = plt.subplots(1, 1, constrained_layout=True, facecolor='white', edgecolor='white')

        nb_colors = df['Training Iteration'].nunique()

        colors = sns.color_palette(n_colors=nb_colors)
        
        plot = sns.lineplot(data=df, x=xlabel, y=ylabel.format(titles[i]), hue='Training Iteration', palette=colors, ax=ax)
        xlabels = [label for label in sorted(df['Epoch'].unique()) if label < 26]
        ylabels = [label for label in sorted(df[titles[i]].unique())]   
        if 'Loss' not in titles[i]:
            plot.set(xlim=(min(xlabels), max(xlabels)),
                xticks = xlabels[::3],
                ylim=(0.0, 1.0))
        else:
            plot.set(xlim=(min(xlabels), max(xlabels)),
                xticks = xlabels[::3],
                ylim=(0.0, max(sorted(ylabels[:-4]))))
            if 'Training' in titles[i]:
                plot.set(xlim=(min(xlabels), max(xlabels)),
                    xticks = xlabels[::3],
                    ylim=(0.0, 2.0))
        plt.show()

if __name__=='__main__':
    df = get_data()
    plot_learning_curves(df)
