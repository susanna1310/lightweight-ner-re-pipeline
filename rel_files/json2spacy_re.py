# SOURCE OF THIS CODE: https://github.com/explosion/projects/blob/v3/tutorials/rel_component/scripts/parse_data.py
# Adjustments to the orignial code were made 
import os
from  pathlib import Path
import json
import typer
from spacy.tokens import Doc, DocBin
from spacy.vocab import Vocab
from spacy.lang.en import English 
import sys
from spacy.util import filter_spans
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
nlp = English()
#Tokenizer adjustments needed to improve n2c2 2018 ADE dataset tokenization
""" from spacy.util import compile_infix_regex
for special_token in ["):", "k.", "q.", "g."]:
    if special_token in nlp.tokenizer.rules:
        del nlp.tokenizer.rules[special_token]

custom_infixes = [r"[():]"]
infixes = list(nlp.Defaults.infixes) + custom_infixes
nlp.tokenizer.infix_finditer = compile_infix_regex(infixes).finditer """

def json_to_spacy(json_path: Path, output_path: Path): 
    """
    Converts a JSON dataset containing entity and relation annotations into a spaCy DocBin format.
    This function prepares data for training spaCy pipelines with custom entity and relation annotations.

    Args:
        json_path: Path to the input JSON file. Each example must contain 'text', 'tokens', and 'relations'.
        output_path: Path to save the serialized DocBin file (.spacy format).
    """
    Doc.set_extension("rel", default={},force=True)
    vocab = Vocab()

    docs = []

    with open(json_path, encoding='utf-8') as json_file:
        file = json.load(json_file)
        for example in file:
            span_starts = set()
            pos = 0


            tokens = nlp(example["text"])
            words = [t.text for t in tokens]
            spaces = [True if t.whitespace_ else False for t in tokens]
            doc = Doc(vocab, words=words, spaces=spaces)

            spans = example["tokens"]
            entities = []
            span_end_to_start = {}
            for span in spans:
                entity = doc.char_span(
                    span["start"], span["end"], label=span["label"]
                )
                if entity is None:
                    print("Could not create entity for span:", span)
                else:
                    span_end_to_start[(span["start"], span["end"])] = entity.start
                    entities.append(entity)
                    span_starts.add(entity.start)
        
            doc.ents = filter_spans(entities)

            rels = {}
            for x1 in span_starts:
                for x2 in span_starts:
                    if x1 != x2:
                        rels[(x1,x2)] = {}
            relations = example["relations"]
            for relation in relations:
                try:
                    head_char = next((s for s in spans if s["token_start"] == relation["head"]), None)
                    child_char = next((s for s in spans if s["token_start"] == relation["child"]), None)

                    if not head_char or not child_char:
                        print(f"Missing head/child span in relation: {relation}")
                        continue

                    head_token_start = span_end_to_start.get((head_char["start"], head_char["end"]))
                    child_token_start = span_end_to_start.get((child_char["start"], child_char["end"]))

                    if head_token_start is None or child_token_start is None:
                        print(f"Could not map span to tokens for relation: {relation}")
                        continue

                    start = head_token_start
                    end = child_token_start
                    label = relation["relation"]

                    if label not in rels[(start, end)]:
                        rels[(start, end)][label] = 1.0
                        pos += 1
                except KeyError as e:
                    print("Could not find entities for relation:", relation)
            
            doc._.rel = rels

            if pos > 0:
                docs.append(doc)

        docbin = DocBin(docs=docs, store_user_data=True)
        docbin.to_disk(output_path)
        print("Sucessfuly converted .json to .spacy")

if __name__ == "__main__":
    typer.run(json_to_spacy)