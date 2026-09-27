from invoke import task

# These are shortcuts for `invoke evaluate-ner/evaluate-re <year>` only.
# The trained model files and .spacy test data aren't included in this repo
# (i2b2/n2c2 clinical data requires its own signed Data Use Agreement - see
# README). Fill these back in once you have your own copies, e.g.:
#   MODELS = {"2010": "re_models/re_model_2010/model-best", ...}
#   TEST_DATA = {"2010": "path/to/test_2010.spacy", ...}
# Until then, use the explicit-path form instead:
#   invoke evaluate-ner path/to/model --test-data path/to/test.spacy
MODELS = {}
TEST_DATA = {}

NER_CONFIG = "./configs/ner_config.cfg"
RE_CONFIG = "./configs/re_config.cfg"


@task(help={
    "train_json": "Path to train data",
    "dev_json": "Path to dev data",
    "test_json": "Path to test data",
    "output": "Path to output folder of the NER-model",
})
def ner(ctx, train_json, dev_json, test_json, output):
    """
    Workflow for NER
    - Creates .spacy files
    - Trains NER-model
    - Evaluates NER-model
    """
    create_spacy(ctx, train_json, "./files/train.spacy", "ner")
    create_spacy(ctx, dev_json, "./files/dev.spacy", "ner")
    create_spacy(ctx, test_json, "./files/test.spacy", "ner")
    train_ner(ctx, output, "./files/train.spacy", "./files/dev.spacy")
    model = output + '/model-best'
    evaluate_ner(ctx, model, "./files/test.spacy")

@task(help={
    "train_json": "Path to train data",
    "dev_json": "Path to dev data",
    "test_json": "Path to test data",
    "output": "Path to output folder of the RE-model",
})
def re(ctx, train_json, dev_json, test_json, output):
    """
    Workflow for RE
    - Creates .spacy files
    - Trains NER- und RE-model
    - Evaluates NER- und RE-model
    """
    create_spacy(ctx, train_json, "./files/train.spacy", "re")
    create_spacy(ctx, dev_json, "./files/dev.spacy", "re")
    create_spacy(ctx, test_json, "./files/test.spacy", "re")
    train_ner(ctx, "./ner_model", "./files/train.spacy", "./files/dev.spacy")
    train_re(ctx, output, "./files/train.spacy", "./files/dev.spacy", "./ner_model/model-best")
    model = output + '/model-best'
    print("EVALUATION OF NER MODEL")
    evaluate_ner(ctx, "./ner_model/model-best", "./files/test.spacy")
    print("EVALUATION OF RE MODEL")
    evaluate_re(ctx, model, "./files/test.spacy")

@task(help={
    "directory": "Path to data of type .xml, .ann or .con",
    "file_type": "Type of data eiter xml, ann or con",
    "txt_directory": "Path .txt data needed for .ann and .con",
    "rel_directory": "Path .rel data needed for .con",
})
def split(ctx, directory, file_type, txt_directory="None", rel_directory="None"):
    if file_type == "xml":
        ctx.run(f"python scripts/split_data.py {directory} {file_type}", echo=True)
    elif file_type == "ann":
        if txt_directory != "None":
            ctx.run(f"python scripts/split_data.py {directory} {file_type} --txt-directory {txt_directory}", echo=True)
        else:
            raise ValueError("Missing argument! txt-directory is missing!") 
    elif file_type == "con":
        if txt_directory != "None" and rel_directory != "None":
            ctx.run(f"python scripts/split_data.py {directory} {file_type} --txt-directory {txt_directory} --rel-directory {rel_directory}", echo=True)
        else:
            raise ValueError("Missing argument! txt-directory or rel-directory is missing!") 
    else:
       raise ValueError("Invalid file-type! Data format needs to be either xml, ann or con") 

@task(help={
    "data": "Path to dataset",
    "output": "Path for output .JSON file",
    "year": "i2b2 Dataset year"
})
def create_json(ctx, data, output, year):
    """
    Convert data to JSON file
    """
    if year == "2010":
        ctx.run(f"python scripts/parse_2010_i2b2.py {data} {output}", echo=True)
    elif year == "2012":
        ctx.run(f"python scripts/parse_2012_i2b2.py {data} {output}", echo=True)
    elif year == "2014":
        ctx.run(f"python scripts/parse_2014_i2b2.py {data} {output}", echo=True)
    elif year == "2018":
        ctx.run(f"python scripts/parse_2018_i2b2.py {data} {output}", echo=True)
    else:
        raise ValueError("Invalid year! Year needs to be either 2010, 2012, 2014 or 2018")

@task(help={
    "json_file": "Path to JSON data",
    "output": "Path for output .spacy file",
    "data_type": "Type of data format, either ner or re"
})
def create_spacy(ctx, json_file, output, data_type):
    """
    Convert JSON to .spacy file
    """
    if data_type == "ner":
        ctx.run(f"python ner_files/json2spacy.py {json_file} {output}", echo=True)
    elif data_type == "re":
        ctx.run(f"python rel_files/json2spacy_re.py {json_file} {output}", echo=True)
    else:
        raise ValueError("Invalid data_type! Type needs to be either ner or re")

@task(help={
    "output": "Path where the model should be saved",
    "train": "Path to .spacy file with training data",
    "dev": "Path to .spacy file with dev data",
    "config": "Path to .cfg file"
})
def train_ner(ctx, output, train, dev, config=NER_CONFIG):
    """
    Train NER-Model
    Usage:
    - invoke train-ner ./output ./path/to/train  ./path/to/dev
    """
    ctx.run(f"python -m spacy train {config} --output {output} --paths.train {train} --paths.dev {dev}", echo=True)

@task(help={
    "output": "Path where the model should be saved",
    "train": "Path to .spacy file with training data",
    "dev": "Path to .spacy file with dev data",
    "model": "Path to NER-model",
    "config": "Path to .cfg file"
})
def train_re(ctx, output, train, dev, model, config=RE_CONFIG):
    """
    Train RE-Model
        Usage:
    - invoke train-re ./output ./path/to/train  ./path/to/dev ./path/to/ner_model
    """
    ctx.run(f"python -m spacy train {config} --output {output} --paths.train {train} --paths.dev {dev} --paths.ner_model {model}", echo=True)

@task(help={
    "year_or_model": "Dataset year OR pass explicit model path",
    "test_data": "Path to .spacy test file"})
def evaluate_ner(ctx, year_or_model, test_data=None):
    """
    Evaluate NER.
    Usage:
    - invoke evaluate-ner 2010
    - invoke evaluate-ner path/to/model --test-data path/to/test.spacy
    """
    if test_data:
        model = year_or_model
    else:
        year = year_or_model
        model = MODELS.get(year)
        test_data = TEST_DATA.get(year)

    if not model or not test_data:
        raise ValueError("Invalid inputs. Use a year of a dataset (2010,2012,2014,2018), or provide model and test paths explicitly.")

    ctx.run(f"python ./testing/evaluate_ner_model.py {model} {test_data}", echo=True)

@task(help={
    "year_or_model": "Dataset year OR pass explicit model and test paths",
    "use_gold_ne": "Whether to use gold named entities (default: False)",
    "print_details": "Whether to print detailed output (default: False)"
})
def evaluate_re(ctx, year_or_model, test_data=None, data_type=None, use_gold_ne=False, print_details=False):
    """
    Evaluate RE.
    Usage:
    - invoke evaluate-re 2018
    - invoke evaluate-re 2018 --use-gold-ne --print-details
    - invoke evaluate-re path/to/model --test-data path/to/test.spacy --data-type <year>
    """
    if test_data is None:
        data_type = year_or_model
        model = MODELS.get(data_type)
        test_data = TEST_DATA.get(data_type)

    # Case 2: custom model + test data
    else:
        model = year_or_model

    # Validate
    if not model or not test_data:
        raise ValueError("Invalid inputs.")

    # Run script
    cmd = (
    f"python ./testing/evaluate_re_model.py "
    f"{model} {test_data} {data_type} {use_gold_ne} {print_details}")

    ctx.run(cmd, echo=True)

@task
def clean(ctx):
    """Remove intermediate training files."""
    ctx.run("rm -rf files/*", echo=True)
