import os
import json
from pathlib import Path
from typing import List, Dict, Union
from spacy.lang.en import English 
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_entities_dict(entities: List[dict]) -> Dict[int, Dict[str, Union[str, int]]]:
    """
    Converts the list of entities into a dict, with the token_start being the key.

    Args:
        entities : A list of entity dictionaries
    
    Returns:
        Dict[int, Dict[str, Union[str, int]]]
    """
    return {entity["token_start"]: entity for entity in entities}

def filter_entities(entities: List[dict]) -> List[Dict[str, Union[str, int]]]:
    """
    Removes overlapping entities, keeping the shortest one in case of overlap.
    
    Args:
        entities : List of entity dictionaries
    
    Returns:
        List[Dict[str, Union[str, int]]]: A new list with duplicates removed and sorted my offset.
    """
    entities = sorted(entities, key=lambda x: (x["start"], x["end"] - x["start"]))
   
    filtered_entities = []
    seen = set()
    for entity in entities:
        entity_tuple = tuple(entity.items())
        if entity_tuple not in seen:
            if not filtered_entities or entity["start"] >= filtered_entities[-1]["end"]:
                filtered_entities.append(entity)
                seen.add(entity_tuple)
            elif entity["end"] - entity["start"] < filtered_entities[-1]["end"] - filtered_entities[-1]["start"]:
                filtered_entities[-1] = entity
                seen.add(entity_tuple) 
    return filtered_entities

def filter_relations(entities: List[dict], relations: List[dict]) -> List[Dict[str, Union[str, int]]]:
    """
    Filters out relations where either the 'head' or 'child' entity is missing 
    and removes duplicate relations.

    Args:
        entities : A list of entity dictionaries.
        relations : A list of relation dictionaries with 'child', 'head', and 'relation' keys.

    Returns:
        List[Dict[str, Union[str, int]]]: A filtered and deduplicated list of relations.
    """
    entities_dict = create_entities_dict(entities)
    
    filtered_relations = []
    seen = set()

    for relation in relations:
        if relation["head"] in entities_dict and relation["child"] in entities_dict:
            relation_tuple = (relation['child'], relation['head'], relation['relation'])
            
            if relation_tuple not in seen:
                seen.add(relation_tuple)
                filtered_relations.append(relation)

    return filtered_relations

def tokenize_text(text: str) -> Dict[int, Dict[str, Union[str, int]]]:
    """
    Tokenizes the input text and returns metadata for each token.
    
    Args:
        text (str): The input text to be tokenized.
    
    Returns:
        Dict[int, Dict[str, Union[str, int]]]: Dictionary mapping token start index to token metadata.
    """
    nlp = English()
    tokens = {}
    doc = nlp(text)
    for token in doc:
        tokens[token.idx] = {
            "text": token.text,
            "start": token.idx,
            "end": token.idx + len(token.text),
            "index": token.i
        }
    return tokens

def save_data(file: Path, data: List[dict]):
    """
    Save the data as a JSON file at the specified path.
    
    Args:
        file (Path): The path to save the data to.
        data (List[dict]): The data to save in JSON format.
    """
    with open (file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        print(f"saved data in: {file}")
