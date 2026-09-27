from spacy.tokens import DocBin, Doc
import json
import typer
from tqdm import tqdm
from spacy.util import filter_spans
from pathlib import Path
from spacy.vocab import Vocab
from typing import Tuple
from spacy.lang.en import English 
from spacy.util import compile_infix_regex
from spacy.attrs import ORTH
from spacy.tokenizer import Tokenizer
from string import whitespace
nlp = English()
# Tokenizer adjustments needed to improve i2b2 2014 De-Identification dataset tokenization
# All characters considered special
special_chars = r"""[!&:?*\.,\-_()\[\]{}"'=;<>@#$%^|~`\\\/]"""
# Custom infix rules to split:
custom_infixes = [
    r'(?<=[0-9])(?=[a-zA-Z])',       # number → letter
    r'(?<=[a-zA-Z])(?=[0-9])',       # letter → number
    rf'(?<=[a-zA-Z])(?={special_chars})',  # letter → special
    rf'(?<={special_chars})(?=[a-zA-Z])',  # special → letter
    rf'(?<=[0-9])(?={special_chars})',     # number → special
    rf'(?<={special_chars})(?=[0-9])',      # special → number
]
infixes = list(nlp.Defaults.infixes) + custom_infixes
infix_re = compile_infix_regex(infixes)
# Override tokenizer
nlp.tokenizer = Tokenizer(nlp.vocab,
    rules=nlp.Defaults.tokenizer_exceptions,
    prefix_search=nlp.tokenizer.prefix_search,
    suffix_search=nlp.tokenizer.suffix_search,
    infix_finditer=infix_re.finditer,
    token_match=None
)
# Special tokenize cases
case = [{ORTH: "F"}, {ORTH: "A"}, {ORTH: "T"}]
nlp.tokenizer.add_special_case("FAT", case)
case = [{ORTH: "T"}, {ORTH: "T"}, {ORTH: "S"}]
nlp.tokenizer.add_special_case("TTS", case)
case = [{ORTH: "S"}, {ORTH: "T"}, {ORTH: "Th"}]
nlp.tokenizer.add_special_case("STTh", case)
case = [{ORTH: "M"}, {ORTH: "W"}, {ORTH: "F"}]
nlp.tokenizer.add_special_case("MWF", case)
case = [{ORTH: "M"}, {ORTH: "W"}, {ORTH: "F"}, {ORTH: "S"}]
nlp.tokenizer.add_special_case("MWFS", case)
case = [{ORTH: "T"}, {ORTH: "Th"}, {ORTH: "Sa"}]
nlp.tokenizer.add_special_case("TThSa", case)
case = [{ORTH: "s"}, {ORTH: "."}]
nlp.tokenizer.add_special_case("s.", case)
case = [{ORTH: "Inc"}, {ORTH: "."}]
nlp.tokenizer.add_special_case("Inc.", case)
case = [{ORTH: "Nov"}, {ORTH: "."}]
nlp.tokenizer.add_special_case("Nov.", case)
case = [{ORTH: "Sept"}, {ORTH: "."}]
nlp.tokenizer.add_special_case("Sept.", case)

def convert_training_data(TRAIN_DATA, nlp):
    """
    Used for the JSON file generated in generate_training_data.py
    Converts JSON training data into .spacy file.

    JSON format: 
    [
      [
        "She is 28 year old."
        { 
          "entities": [[7, 9, "AGE"]]
        }
      ]
    ]

    Args:
    TRAIN_DATA: path to json file with training data
    nlp: SpaCy model 
    """
    db = DocBin()
    for text, annotation in tqdm(TRAIN_DATA):
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in annotation["entities"]:
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is None:
                print("Skipping entity")
            else:
                ents.append(span)
        doc.ents = ents
        db.add(doc)
    return (db)

def clean_span(text: str, start: int, end:int) -> Tuple[int, int]:
    """
    Cleans a character span by trimming leading and trailing whitespace.

    Args:
        text: The full text containing the span.
        start: The starting character index of the span.
        end: The ending character index of the span.

    Returns:
        Tuple[int, int]: A tuple containing the cleaned start and end indices.
    """
    while start < end and text[start] in whitespace:
        start += 1
    while end > start and text[end - 1] in whitespace:
        end -= 1
    return start, end

def json_to_spacy(json_path: Path, output_path: Path):
    """
    Converts a JSON file with token-level annotations into a spaCy `DocBin` object
    and saves it to disk for use in training spaCy models.

    JSON format:
    [
      {
        "text": "She is 28 year old.",
        "tokens": [
            {
                "text": "28",
                "start": 7,
                "end": 9,
                "label": "AGE",
                "token_start": 2
            }
        ]
      }
    ]

    Args:
        json_path: Path to the input JSON file containing annotated data.
        output_path: Path to save the serialized `DocBin` file.
    """
    db = DocBin()
    vocab = Vocab()
    with open(json_path, encoding='utf-8') as json_file:
        file = json.load(json_file)
        for example in file:
            tokens = nlp(example["text"])
            words = [t.text for t in tokens]
            spaces = [True if t.whitespace_ else False for t in tokens]
            doc = Doc(vocab, words=words, spaces=spaces)
            temp_dict = []
            entities = example["tokens"]
            for entity in entities:
                start, end = clean_span(example["text"], entity["start"], entity["end"])
                span = doc.char_span(start, end, label=entity["label"])
                if span is None:
                    print("Skipping entity: ", entity)
                else:
                    temp_dict.append(span)
            doc.ents = filter_spans(temp_dict)
            db.add(doc)
        db.to_disk(output_path)
    print(json_path)

if __name__ == "__main__":
    typer.run(json_to_spacy)


