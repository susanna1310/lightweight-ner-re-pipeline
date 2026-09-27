import optuna
from spacy.cli.train import train
from pathlib import Path
import spacy
from spacy.scorer import Scorer
from spacy.training import Example
from spacy.tokens import DocBin


def make_objective(config_path: Path, test_data_path: Path):
    """
    Create an Optuna objective function for hyperparameter tuning of a spCy NER model.

    Args:
        config_path: Path to the spaCy config file used for training.
        test_data_path: Path to a .spacy file containing the evaluation data.

    Returns:
        function: An objective function that Optuna will call with different hyperparameter values.
    """
    def objective(trial):
        """
        Inner objective function to be passed to Optuna. Trains a spaCy model using the current 
        trial's suggested hyperparameters and evaluates it on the provided test data.

        Args:
            trial (optuna.trial.Trial): The current Optuna trial
        
        Returns:
            float: The F-score for named entities on the test set.
        """
        dropout = trial.suggest_float("dropout", 0.1, 0.4, step=0.05)
        learn_rate = trial.suggest_float("learn_rate", 1e-4, 5e-3, log=True)
        hidden_width = trial.suggest_int("hidden_width", 32, 256, step=32)
        batch_size = trial.suggest_int("batch_size", 128, 2048, step=128)

        overrides = {
            "training.dropout": dropout,
            "training.optimizer.learn_rate": learn_rate,
            "components.ner.model.hidden_width": hidden_width,
            "nlp.batch_size": batch_size
        }

        model_path = f"./optuna/model_trial_{trial.number}"
        train(config_path, model_path, overrides=overrides)

        nlp = spacy.load(Path(str(model_path) + "/model-best"))
        doc_bin = DocBin(store_user_data=True).from_disk(test_data_path)
        docs = doc_bin.get_docs(nlp.vocab)
        examples = []
        for gold in docs:
            text = gold.text 
            pred_doc = nlp.make_doc(text)
            pred = nlp(pred_doc)
            examples.append(Example(pred, gold))

        scorer = Scorer()
        score = scorer.score_spans(examples, "ents")
        print(score)
        return score["ents_f"]
    return objective
    
# Optuna's storage backend for this study - points at a MySQL instance and is
# specific to whoever is running the tuning, so it isn't safe to hardcode here.
# Set this to your own DB before running this script, e.g.:
#   "mysql+pymysql://<user>:<password>@<host>/<database>"
OPTUNA_STORAGE = "mysql+pymysql://<user>:<password>@<host>/<database>"

study = optuna.load_study(
    study_name="study_2012", storage=OPTUNA_STORAGE
)

objective_fn = make_objective(config_path=Path("./configs/ner_config.cfg"), test_data_path=Path("./path/test.spacy"))
study.optimize(objective_fn, n_trials=30)
best_trial = study.best_trial
print("Best trial number:", best_trial.number)
print("Best value:", best_trial.value)
print("Best params:", best_trial.params)

