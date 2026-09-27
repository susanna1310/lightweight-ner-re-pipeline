import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import typer
from pathlib import Path
import spacy
from spacy.tokens import DocBin, Doc
from spacy.training.example import Example
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# make the factory work
from rel_files.rel_pipe import make_relation_extractor, score_relations_with_temporal_closure, score_relations_all_keys, evaluate_re_softmax_full, temporal_closure_dict

# make the config work
from rel_files.rel_model import create_relation_model, create_classification_layer, create_instances, create_tensors

def evaluate_re_model(trained_pipeline: Path, test_data: Path, data_type: str, use_gold_named_entities: bool, print_details: bool):
    nlp = spacy.load(trained_pipeline)

    doc_bin = DocBin(store_user_data=True).from_disk(test_data)
    docs = doc_bin.get_docs(nlp.vocab)
    examples = []
    for gold in docs:
        pred = Doc(
            nlp.vocab,
            words=[t.text for t in gold],
            spaces=[t.whitespace_ for t in gold],
        )

        if use_gold_named_entities:
            pred.ents = gold.ents

        for name, proc in nlp.pipeline:
            if name != "ner":
                pred = proc(pred)
            else: 
                if not use_gold_named_entities:
                    pred = proc(pred)
        
        examples.append(Example(pred, gold))

        # Print the gold and prediction, if gold label is not 0
        if print_details:
            print()
            print(f"spans: {[(e.start, e.text, e.label_) for e in pred.ents]}")
            for value, rel_dict in pred._.rel.items():
                gold_dict = gold._.rel.get(value, {})
                gold_labels = [k for (k, v) in gold_dict.items() if v == 1.0]
                if gold_labels:
                    print(
                        f" pair: {value} --> gold labels: {gold_labels} --> predicted values: {rel_dict}"
                    )
            print()

    thresholds = [0.000, 0.050, 0.100, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99, 0.999]

    print()
    print("Results of the trained model:")
    _score_and_format(examples, thresholds, data_type)

    print()
    _score_and_format_softmax(examples, data_type)

    print("\nConfusion matrix:")
    _plot_confusion_matrix(examples, threshold=0.5, apply_temporal_closure=(data_type=="2012"))

def _score_and_format(examples, thresholds, data_type):
    for threshold in thresholds:
        if data_type == "2012":
            r = score_relations_with_temporal_closure(examples, threshold)
        else:
            r = score_relations_all_keys(examples, threshold, data_type)
        results = {k: "{:.2f}".format(v * 100) for k, v in r.items()}
        print(f"threshold {'{:.2f}'.format(threshold)} \t {results}")

def _score_and_format_softmax(examples, data_type):
    print("Softmax Relation Full\n")
    report = evaluate_re_softmax_full(examples, data_type)
    print(report)

def _plot_confusion_matrix(examples, threshold=0.5, apply_temporal_closure=False):
    y_true = []
    y_pred = []

    for example in examples:
        gold_pairs = example.reference._.rel
        pred_pairs = example.predicted._.rel

        if apply_temporal_closure:
            gold_pairs = temporal_closure_dict(gold_pairs)
            pred_pairs = temporal_closure_dict(pred_pairs)

        all_pairs = set(gold_pairs.keys()) | set(pred_pairs.keys())

        for pair in all_pairs:
            gold_dict = gold_pairs.get(pair, {})
            pred_dict = pred_pairs.get(pair, {})

            gold_labels = [k for k, v in gold_dict.items() if v == 1.0]
            gold_label = gold_labels[0] if gold_labels else "NO_RELATION"

            if pred_dict:
                pred_label = max(pred_dict, key=pred_dict.get)
                if pred_dict[pred_label] < threshold:
                    pred_label = "NO_RELATION"
            else:
                pred_label = "NO_RELATION"

            y_true.append(gold_label)
            y_pred.append(pred_label)

    labels = sorted(list(set(y_true) | set(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(xticks_rotation=45)
    plt.savefig("matrix.png", format="png", dpi=300)
    plt.show()

if __name__ == "__main__":
    typer.run(evaluate_re_model)