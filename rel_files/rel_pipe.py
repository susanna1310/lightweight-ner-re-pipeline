# SOURCE OF THIS CODE: https://github.com/alimirzaei/spacy-relation-extraction/blob/master/scripts/rel_pipe.py
# Adjustments to the orignial code were made 
from itertools import islice
from typing import Tuple, List, Iterable, Optional, Dict, Callable, Any, DefaultDict, Set
from sklearn.metrics import classification_report, precision_recall_fscore_support
from spacy.scorer import PRFScore
from thinc.types import Floats2d
import numpy
from spacy.training.example import Example
from thinc.api import Model, Optimizer
from spacy.tokens.doc import Doc
from spacy.tokens import Span
from spacy.pipeline import TrainablePipe
from spacy.vocab import Vocab
from spacy import Language
from thinc.model import set_dropout_rate
from wasabi import Printer
from collections import defaultdict
from itertools import product
import logging


Doc.set_extension("rel", default={}, force=True)
msg = Printer()


@Language.factory(
    "relation_extractor",
    requires=["doc.ents", "token.ent_iob", "token.ent_type"],
    assigns=["doc._.rel"],
    default_score_weights={
        "rel_micro_p": None,
        "rel_micro_r": None,
        "rel_micro_f": None,
    },
)
def make_relation_extractor(
    nlp: Language, name: str, model: Model, *, threshold: float
):
    """Construct a RelationExtractor component."""
    return RelationExtractor(nlp.vocab, model, name, threshold=threshold)


class RelationExtractor(TrainablePipe):
    def __init__(
        self,
        vocab: Vocab,
        model: Model,
        name: str = "rel",
        *,
        threshold: float,
    ) -> None:
        """Initialize a relation extractor."""
        self.vocab = vocab
        self.model = model
        self.name = name
        self.cfg = {"labels": [], "threshold": threshold}

    @property
    def labels(self) -> Tuple[str]:
        """Returns the labels currently added to the component."""
        return tuple(self.cfg["labels"])

    @property
    def threshold(self) -> float:
        """Returns the threshold above which a prediction is seen as 'True'."""
        return self.cfg["threshold"]

    def add_label(self, label: str) -> int:
        """Add a new label to the pipe."""
        if not isinstance(label, str):
            raise ValueError("Only strings can be added as labels to the RelationExtractor")
        if label in self.labels:
            return 0
        self.cfg["labels"] = list(self.labels) + [label]
        return 1

    def __call__(self, doc: Doc) -> Doc:
        """Apply the pipe to a Doc."""
        # check that there are actually any candidate instances in this batch of examples
        total_instances = len(self.model.attrs["get_instances"](doc))
        if total_instances == 0:
            msg.info("Could not determine any instances in doc - returning doc as is.")
            return doc

        predictions = self.predict([doc])
        self.set_annotations([doc], predictions)
        return doc

    def predict(self, docs: Iterable[Doc]) -> Floats2d:
        """Apply the pipeline's model to a batch of docs, without modifying them."""
        get_instances = self.model.attrs["get_instances"]
        total_instances = sum([len(get_instances(doc)) for doc in docs])
        if total_instances == 0:
            msg.info("Could not determine any instances in any docs - can not make any predictions.")
        scores = self.model.predict(docs)
        return self.model.ops.asarray(scores)

    def set_annotations(self, docs: Iterable[Doc], scores: Floats2d) -> None:
        """Modify a batch of `Doc` objects, using pre-computed scores."""
        c = 0
        get_instances = self.model.attrs["get_instances"]
        for doc in docs:
            for (e1, e2) in get_instances(doc):
                offset = (e1.start, e2.start)
                if offset not in doc._.rel:
                    doc._.rel[offset] = {}
                for j, label in enumerate(self.labels):
                    doc._.rel[offset][label] = scores[c, j]
                c += 1

    def update(
        self,
        examples: Iterable[Example],
        *,
        drop: float = 0.0,
        set_annotations: bool = False,
        sgd: Optional[Optimizer] = None,
        losses: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """Learn from a batch of documents and gold-standard information,
        updating the pipe's model. Delegates to predict and get_loss."""
        if losses is None:
            losses = {}
        losses.setdefault(self.name, 0.0)
        set_dropout_rate(self.model, drop)

        # check that there are actually any candidate instances in this batch of examples
        total_instances = 0
        for eg in examples:
            total_instances += len(self.model.attrs["get_instances"](eg.predicted))
        if total_instances == 0:
            msg.info("Could not determine any instances in doc.")
            return losses

        # run the model
        docs = [eg.predicted for eg in examples]
        predictions, backprop = self.model.begin_update(docs)
        loss, gradient = self.get_loss(examples, predictions)
        backprop(gradient)
        if sgd is not None:
            self.model.finish_update(sgd)
        losses[self.name] += loss
        if set_annotations:
            self.set_annotations(docs, predictions)
        return losses

    def get_loss(self, examples: Iterable[Example], scores) -> Tuple[float, float]:
        """Find the loss and gradient of loss for the batch of documents and
        their predicted scores."""
        truths = self._examples_to_truth(examples)
        gradient = scores - truths
        mean_square_error = (gradient ** 2).sum(axis=1).mean()
        return float(mean_square_error), gradient

    def initialize(
        self,
        get_examples: Callable[[], Iterable[Example]],
        *,
        nlp: Language = None,
        labels: Optional[List[str]] = None,
    ):
        """Initialize the pipe for training, using a representative set
        of data examples.
        """
        if labels is not None:
            for label in labels:
                self.add_label(label)
        else:
            for example in get_examples():
                relations = example.reference._.rel
                for indices, label_dict in relations.items():
                    for label in label_dict.keys():
                        self.add_label(label)
        self._require_labels()

        subbatch = list(islice(get_examples(), 10))
        doc_sample = [eg.reference for eg in subbatch]
        label_sample = self._examples_to_truth(subbatch)
        if label_sample is None:
            raise ValueError("Call begin_training with relevant entities and relations annotated in "
                             "at least a few reference examples!")
        self.model.initialize(X=doc_sample, Y=label_sample)

    def _examples_to_truth(self, examples: List[Example]) -> Optional[numpy.ndarray]:
        # check that there are actually any candidate instances in this batch of examples
        nr_instances = 0
        for eg in examples:
            nr_instances += len(self.model.attrs["get_instances"](eg.reference))
        if nr_instances == 0:
            return None

        truths = numpy.zeros((nr_instances, len(self.labels)), dtype="f")
        c = 0
        for i, eg in enumerate(examples):
            for (e1, e2) in self.model.attrs["get_instances"](eg.reference):
                gold_label_dict = eg.reference._.rel.get((e1.start, e2.start), {})
                for j, label in enumerate(self.labels):
                    truths[c, j] = gold_label_dict.get(label, 0)
                c += 1

        truths = self.model.ops.asarray(truths)
        return truths

    def score(self, examples: Iterable[Example], **kwargs) -> Dict[str, Any]:
        """Score a batch of examples."""
        return score_relations(examples, self.threshold)

def score_relations(examples: Iterable[Example], threshold: float) -> Dict[str, Any]:
    """Score a batch of examples."""
    micro_prf = PRFScore()
    for example in examples:
        gold = example.reference._.rel
        pred = example.predicted._.rel
        for key, pred_dict in pred.items():
            gold_dict = gold.get(key, {})
            gold_labels = [k for (k, v) in gold_dict.items() if v == 1.0]
            for k, v in pred_dict.items():
                if v >= threshold:
                    if k in gold_labels:
                        micro_prf.tp += 1
                    else:
                        micro_prf.fp += 1
                else:
                    if k in gold_labels:
                        micro_prf.fn += 1
    return {
        "rel_micro_p": micro_prf.precision,
        "rel_micro_r": micro_prf.recall,
        "rel_micro_f": micro_prf.fscore,
    }

def get_ents(doc: Doc, key1: int, key2: int) -> Tuple[Optional[Span], Optional[Span]]:
    """
    Retrieves two named entities from a spaCy Doc object based on their starting token indices.

    Args:
        doc: A spaCy Doc object containing entity annotations.
        key1: The start index of the first entity.
        key2: The start index of the second entity.

    Returns:
        Tuple[Optional[Span], Optional[Span]]: 
            A tuple containing the two matching entity spans, or None if not found.
    """
    ent1 = None
    ent2 = None
    for ent in doc.ents:
        if ent.start == key1:
            ent1 = ent
        elif ent.start == key2:
            ent2 = ent
    return ent1, ent2

def filter_relation_predictions_2010(doc: Doc) -> dict:
    """
    Filters predicted relations in a spaCy Doc object according to relation type constraints
    based on entity type combinations, specific to the 2010 i2b2 dataset.

    Args:
        doc: A spaCy Doc object with predicted relations stored in `doc._.rel`.

    Returns:
        dict: The filtered prediction dictionary with disallowed relations set to 0.0.
    """
    allowed_types = {
        ("problem", "treatment"): {"TrIP", "TrWP", "TrCP", "TrAP", "TrNAP"},
        ("treatment", "problem"): {"TrIP", "TrWP", "TrCP", "TrAP", "TrNAP"},
        ("problem", "test"): {"TeRP", "TeCP"},
        ("test", "problem"): {"TeRP", "TeCP"},
        ("problem", "problem"): {"PIP"}
    }
    pred = doc._.rel
    for (key1, key2), pred_dict in pred.items():
        ent1, ent2 = get_ents(doc, key1, key2)
        valid_labels = allowed_types.get((ent1.label_, ent2.label_), set())

        filtered_pred = {}
        for k, v in pred_dict.items():
            filtered_pred[k] = v if k in valid_labels else 0.0

        pred[(key1, key2)] = filtered_pred
            
    return pred

def score_relations_all_keys(examples: Iterable[Example], threshold: float, data_type: str) -> Dict[str, Any]:
    """
    Computes micro-averaged precision, recall, and F1 score for relation extraction.

    For each example, compares gold-standard and predicted relations across all keys.
    Applies a data-specific filtering step if `data_type` is "2010".

    Args:
        examples: List of spaCy Example objects with predictions and references.
        threshold: Minimum confidence score to consider a predicted relation as positive.
        data_type: Optional dataset identifier to apply dataset-specific processing logic.

    Returns:
        Dict[str, Any]: Dictionary containing micro-averaged precision, recall, and F1 score.
    """
    micro_prf = PRFScore()
    for example in examples:
        gold = example.reference._.rel
        pred = example.predicted._.rel
        if data_type == "2010":
            pred = filter_relation_predictions_2010(example.predicted)

        all_keys = set(gold.keys() | set(pred.keys()))
        for key in all_keys:
            gold_dict = gold.get(key, {})
            pred_dict = pred.get(key, {})

            gold_labels = {k for k, v in gold_dict.items() if v == 1.0}
            pred_labels = set()

            if pred_dict:
                best_label, best_score = max(pred_dict.items(), key=lambda item: item[1])
                sorted_preds = sorted(pred_dict.items(), key=lambda item: item[1], reverse=True)

                if best_score >= threshold:
                    # if (threshold >= 0.999):
                    #     logging.warning(sorted_preds)
                    pred_labels.add(best_label)
            #pred_labels = {k for k, v in pred_dict.items() if v >= threshold}

            micro_prf.tp += len(gold_labels & pred_labels)
            micro_prf.fp += len(pred_labels - gold_labels)
            micro_prf.fn += len(gold_labels - pred_labels)
    return {
        "rel_micro_p": micro_prf.precision,
        "rel_micro_r": micro_prf.recall,
        "rel_micro_f": micro_prf.fscore,
    }

INVERSE = {
    "BEFORE": "AFTER",
    "AFTER": "BEFORE",
    "OVERLAP": "OVERLAP"
}
TRANSITIVE = {
    ("BEFORE", "BEFORE"): "BEFORE",
    ("AFTER", "AFTER"): "AFTER"
}

def temporal_closure_dict(relation_dict: Dict[Tuple[int, int], Dict[str, float]]) -> DefaultDict[Tuple[int, int], Set[str]]:
    """
    Computes the temporal closure of a graph of relations using transitivity and inverse logic.

    Given a dictionary of relations between entity pairs with scores, selects the scoring
    label and infers additional relations using transitive and inverse rules (e.g., A BEFORE B and B BEFORE C → A BEFORE C).

    Args:
        relation_dict: A mapping of entity pairs to a dictionary of relation types with confidence scores.

    Returns:
        DefaultDict[Tuple[int, int], Set[str]]:  A dictionary mapping entity pairs to a set of inferred temporal relations.
    """
    closure = defaultdict(set)

    # Load original relations
    for (a, b), rels in relation_dict.items():
        if not rels:
            continue
        label = max(rels, key=rels.get)
        # Inversion: A BEFORE B => B AFTER A
        closure[(a, b)].add(label)
        closure[(b, a)].add(INVERSE[label])

    added = True
    while added:
        added = False
        new_relations = defaultdict(set)
        keys = list(closure.keys())

        for (a1, b1), (a2, b2) in product(keys, repeat=2):
            # Transitivity: A BEFORE B and B BEFORE C => A BEFORE C
            if b1 == a2:
                r1 = next(iter(closure[(a1, b1)]))
                r2 = next(iter(closure[(a2, b2)]))
                if (r1, r2) in TRANSITIVE:
                    inferred = TRANSITIVE[(r1, r2)]
                    if inferred not in closure[(a1, b2)]:
                        new_relations[(a1, b2)].add(inferred)
                        new_relations[(b2, a1)].add(INVERSE[inferred])

        for (a, b), rels in new_relations.items():
            before = len(closure[(a, b)])
            closure[(a, b)].update(rels)
            if len(closure[(a, b)]) > before:
                added = True
                if len(closure[(a, b)]) > 1:
                    logging.warning(f"Contradictory temporal labels for pair {(a, b)}: {closure[(a, b)]}")

    return closure

def score_relations_with_temporal_closure(examples: Iterable[Example], threshold: float)  -> Dict[str, Any]:
    """
    Computes relation extraction performance using temporal closure on the gold annotations.

    Applies logical inference (transitivity and inversion) on gold relations to augment evaluation.
    Compares inferred gold relations with predicted ones using a confidence threshold.

    Args:
        examples (Iterable[Example]): List of spaCy Example objects with predictions and references.
        threshold (float): Minimum confidence score to consider a predicted relation as positive.

    Returns:
        Dict[str, Any]: Dictionary containing micro-averaged precision, recall, and F1 score.
    """
    micro_prf = PRFScore()
    for example in examples:
        gold = example.reference._.rel
        pred = example.predicted._.rel
        gold_closure = temporal_closure_dict(gold)
        all_keys = set(gold_closure.keys()) | set(pred.keys())

        for key in all_keys:
            gold_labels = gold_closure.get(key, set())
            pred_dict = pred.get(key, {})
            if pred_dict:
                best_label = max(pred_dict, key=pred_dict.get)
                pred_labels = {best_label}
            else:
                pred_labels = set()

            micro_prf.tp += len(gold_labels & pred_labels)
            micro_prf.fp += len(pred_labels - gold_labels)
            micro_prf.fn += len(gold_labels - pred_labels)

    return {
        "rel_micro_p": micro_prf.precision,
        "rel_micro_r": micro_prf.recall,
        "rel_micro_f": micro_prf.fscore,
    }

def evaluate_re_softmax_full(examples: Iterable[Example], data_type: str):

    y_true = []
    y_pred = []

    for example in examples:
        gold_pairs = example.reference._.rel
        pred_pairs = example.predicted._.rel

        if data_type == "2010":
            pred_pairs = filter_relation_predictions_2010(example.predicted)

        if data_type == "2012":
            gold_closure = temporal_closure_dict(gold_pairs)
            # Collect all candidate pairs (union of gold and predicted)
            all_pairs = set(gold_closure.keys()) | set(pred_pairs.keys())
        else:
            # Collect all candidate pairs (union of gold and predicted)
            all_pairs = set(gold_pairs.keys()) | set(pred_pairs.keys())

        
        for pair in all_pairs:
            if data_type == "2012":
                gold_labels = gold_closure.get(pair, set())
                if not gold_labels:
                    continue  # skip pairs that are not in the gold closure
                gold_label = list(gold_labels)[0]  # if multiple labels, just take one (shouldn't happen in closure)
            else:
                gold_dict = gold_pairs.get(pair, {})
                if not gold_dict:
                    continue
                gold_label = [k for k, v in gold_dict.items() if v == 1.0][0]

            pred_dict = pred_pairs.get(pair, {})

            # Determine predicted label (highest score among predicted)
            if pred_dict:
                pred_label = max(pred_dict, key=pred_dict.get)
            else:
                pred_label = "MISSING"  # counts as FN

            y_true.append(gold_label)
            y_pred.append(pred_label)

        # Optional: also count hallucinated extra pairs as FP
        # Uncomment if you want extra pairs that do not exist in gold to be counted
        
        for pair in set(pred_pairs.keys()) - set(gold_pairs.keys()):
            pred_label = max(pred_pairs[pair], key=pred_pairs[pair].get)
            y_true.append("MISSING")  # placeholder, not a real label
            y_pred.append(pred_label)
        

    # Get unique labels
    labels = sorted(set(y_true) - {"MISSING"})

    # Classification report
    report = classification_report(
        y_true, y_pred,
        labels=labels,
        digits=4,
        zero_division=0
    )
    print(report)

    # Micro, macro, weighted
    micro_p, micro_r, micro_f, _ = precision_recall_fscore_support(
        y_true, y_pred, average="micro", labels=labels, zero_division=0
    )
    macro_p, macro_r, macro_f, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", labels=labels, zero_division=0
    )
    weighted_p, weighted_r, weighted_f, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", labels=labels, zero_division=0
    )

    print("micro avg:")
    print(f"precision: {micro_p:.4f}  recall: {micro_r:.4f}  f1-score: {micro_f:.4f}")
    print("macro avg:")
    print(f"precision: {macro_p:.4f}  recall: {macro_r:.4f}  f1-score: {macro_f:.4f}")
    print("weighted avg:")
    print(f"precision: {weighted_p:.4f}  recall: {weighted_r:.4f}  f1-score: {weighted_f:.4f}")