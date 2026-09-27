from sklearn.metrics import confusion_matrix, classification_report, precision_recall_fscore_support
import seaborn as sn
import pandas as pd
import matplotlib.pyplot as plt

def create_matrix(y_true, y_pred, labels):
    """
    Creates two confusion matrices. One with normalize="pred" and one with normalize="true" and saves 
    them as a .png image.

    Args:
        y_true: List of true positive labels.
        y_pred: List of prediction labels
        labels: List of labels
    """
    labels = labels + ["O"]
    num_labels = len(labels)
    fig_size = 1 + num_labels * 0.6
    annot_font_size = max(8, 20 - len(labels)) 
    matrix = confusion_matrix(y_true, y_pred, labels=labels, normalize='pred')
        
    df_cm = pd.DataFrame(matrix, index = [i for i in labels],
                  columns = [i for i in labels])
    

    plt.figure(figsize=(fig_size, fig_size))        

    sn.heatmap(df_cm, cmap="Blues", annot=True, fmt='.0%', vmax=1, vmin=0, square=True, cbar_kws={"shrink": 0.80}, linewidths=.1, linecolor="black", annot_kws={"fontsize":annot_font_size})

    plt.title('Precision Confusion Matrix')

    plt.savefig("precision-confusion-matrix.png", format="png", bbox_inches='tight', dpi=300)
    plt.close()

    matrix = confusion_matrix(y_true, y_pred, labels=labels, normalize='true')
        
    df_cm = pd.DataFrame(matrix, index = [i for i in labels],
                  columns = [i for i in labels])
    
    plt.figure(figsize=(fig_size, fig_size))

    sn.heatmap(df_cm, cmap="Blues", annot=True, fmt='.0%', vmax=1, vmin=0, square=True, cbar_kws={"shrink": 0.80}, linewidths=.1, linecolor="black", annot_kws={"fontsize":annot_font_size})

    plt.title('Recall Confusion Matrix')

    plt.savefig("recall-confusion-matrix.png", format="png", bbox_inches='tight', dpi=300)
    plt.close()

def visualize_classification_report(y_true, y_pred, labels):
    """
    Creates two bar charts. One for all the labels and one with the average values and saves
    them as a .png image.

    Args:
        y_true: List of true positive labels.
        y_pred: List of prediction labels
        labels: List of labels
    """
    class_report = classification_report(y_true, y_pred, output_dict=True, zero_division=0, labels=labels)
    num_labels = len(labels)
    fig_size = 1 + num_labels * 1.3
    
    custom_palette = {
    "precision": "#f4c245",  
    "recall": "#4bb140",     
    "f1-score": "#0066cc"   
    }
    metrics = ["precision", "recall", "f1-score"]
    data = {metric: [] for metric in metrics}
    class_labels = []
    for cls, metrics_values in class_report.items():
        if isinstance(metrics_values, dict) and cls not in ['macro avg', 'weighted avg', 'micro avg']:
            class_labels.append(cls)
            for metric in metrics:
                data[metric].append(metrics_values.get(metric, None))

    df = pd.DataFrame(data, index=class_labels)

    df_melted = df.reset_index().melt(id_vars='index', var_name='Metric', value_name='Score')
    df_melted.rename(columns={'index': 'Class'}, inplace=True)
    plt.figure(figsize=(fig_size, fig_size))
    sn.barplot(x='Score', y='Class', hue='Metric', data=df_melted, palette=custom_palette)
    annot_font_size = max(6, 14 - int(0.4 * len(class_labels)))
    for container in plt.gca().containers:
        plt.gca().bar_label(container, fmt='%.2f', fontsize=annot_font_size)
    plt.xlabel('')
    plt.ylabel('')
    plt.xlim(0, 1.19)
    plt.legend(title='Metric', loc='lower right',)
    plt.tight_layout()
    # Save the figure
    plt.savefig("class_report.png", format="png", dpi=300)
    plt.close()
 
    micro_p, micro_r, micro_f, _ = precision_recall_fscore_support(y_true, y_pred, average="micro", zero_division=0)
    avg_labels = ['micro avg', 'macro avg', 'weighted avg']
    data = {metric: [] for metric in metrics}
    for cls in avg_labels:
        if cls == 'micro avg':
            data['precision'].append(micro_p)
            data['recall'].append(micro_r)
            data['f1-score'].append(micro_f)
        else:
            metrics_values = class_report.get(cls, {})
            for metric in metrics:
                data[metric].append(metrics_values.get(metric, None))
    df2 = pd.DataFrame(data, index=avg_labels)
    df_melted = df2.reset_index().melt(id_vars='index', var_name='Metric', value_name='Score')
    df_melted.rename(columns={'index': 'Class'}, inplace=True)
    sn.barplot(x='Class', y='Score', hue='Metric', data=df_melted, palette=custom_palette)
    for container in plt.gca().containers:
        plt.gca().bar_label(container, fmt='%.2f', fontsize=annot_font_size)
    plt.xlabel('')
    plt.ylabel('')
    plt.ylim(0, 1.25)
    plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    plt.legend(title='Metric', loc='best',)
    plt.tight_layout()
    # Save the figure
    plt.savefig("class_report_avg.png", format="png", dpi=300)
    plt.close()
