import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import spacy
import typer
from sklearn.metrics import classification_report
from testing.visualize_data import create_matrix, visualize_classification_report as class_report
from pathlib import Path
from spacy.training import Example
from spacy.tokens import DocBin
from typing import List, Tuple
# make the factory work
from rel_files.rel_pipe import make_relation_extractor, score_relations

# make the config work
from rel_files.rel_model import create_relation_model, create_classification_layer, create_instances, create_tensors

def get_entity_label_lists(example: Example) -> Tuple[List[str], List[str], List[str]]:
    """
    Extracts predicted and reference entity labels from a spaCy Example object for evaluation.
    It generates aligned label lists for both, based on character span matches, and determines
    the set of unique entity labels present (excluding the "O" label for no-entity).

    Args:
        example: A spaCy Example object containing a predicted and reference Doc.

    Returns:
        Tuple[List[str], List[str], List[str]]:
            - y_true: List of true entity labels.
            - y_pred: List of predicted entity labels.
            - unique_labels: Sorted list of all unique entity labels (excluding "O").
    """
    # Collect predicted and reference entities as dicts keyed by character span
    pred_ents = {(ent.start_char, ent.end_char): ent.label_ for ent in example.predicted.ents}
    ref_ents = {(ent.start_char, ent.end_char): ent.label_ for ent in example.reference.ents}
    
    all_spans = sorted(set(pred_ents.keys()) | set(ref_ents.keys()))
    
    y_true = []
    y_pred = []

    for span in all_spans:
        y_true.append(ref_ents.get(span, "O")) 
        y_pred.append(pred_ents.get(span, "O"))

    # Create a sorted set of labels (excluding "O") for confusion matrix
    unique_labels = sorted({label for label in y_true + y_pred if label != "O"})

    return y_true, y_pred, unique_labels

def evaluate_ner_model(model: Path, test_data: Path):
    """
    Evaluates a spaCy NER model on a given test dataset and prints out detailed performance metrics.
    Additionally prints a scikit-learn classification report and confusion matrix.

    Args:
        model (Path): Path to the trained spaCy model directory.
        test_data (Path): Path to the .spacy file containing the serialized test data.

    Returns:
        None. Prints out:
            - Entity-level F1 score
            - Classification report (precision, recall, F1)
            - Confusion matrix (via helper function `create_matrix`)
    """
    nlp = spacy.load(model)
    doc_bin = DocBin(store_user_data=True).from_disk(test_data)
    docs = doc_bin.get_docs(nlp.vocab)
    labels_all = []
    y_true_all = []
    y_pred_all = []
    for gold in docs:
        text = gold.text
        pred = nlp(text)
        y_true, y_pred, labels = get_entity_label_lists(Example(pred, gold))
        y_true_all.extend(y_true)
        y_pred_all.extend(y_pred)
        labels_all.extend(labels)
    
    labels_all = list(set(labels_all))
    filtered_labels = [label for label in labels_all if label != "O"]
    filtered_labels.sort()
    print(classification_report(y_true_all, y_pred_all, zero_division=0, labels=filtered_labels, digits=6))
    # Uncomment for visualization
    #labels_all.sort()
    #class_report(y_true_all, y_pred_all, labels=labels_all)
    #create_matrix(y_true_all, y_pred_all, labels=labels_all)


if __name__ == "__main__":
    typer.run(evaluate_ner_model)
