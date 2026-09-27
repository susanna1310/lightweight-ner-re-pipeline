import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import re
import typer
from typing import List, Tuple, Dict, Union
from  pathlib import Path
import glob2 as glob
from scripts.utils import save_data, filter_entities, filter_relations

C_PATTERN = r"c=\"(.+?)\" (\d+):(\d+) (\d+):(\d+)"
T_PATTERN = r"t=\"(.+?)\""
A_PATTERN = r"a=\"(.+?)\""
R_PATTERN = r"r=\"(.+?)\""

def parse_con_line(line: str) -> Dict[str, Union[int, str]]:
    """
    Parse one line from a *.con file and return a dictionary with relevant information.
    A typical line has the form,
        'c="angie cm johnson , m.d." 13:2 13:6||t="person"
    This represents one concept to be placed into a coreference group.
    It can be interpreted as follows,
        'c="<string>" <start_line>:<token_start> <end_line>:<token_end>||t="<concept type>"'
    
    Args:
        line (str): A line from the *.con file.
    
    Returns:
        Dict[str, Union[int, str]]: A dictionary containing parsed data with keys 
                                     "text", "token_start", "token_end", "start_line", and "label".
    """
    c_part, t_part = line.split("||")
    c_match, t_match = re.match(C_PATTERN, c_part), re.match(T_PATTERN, t_part)
    return {
        "text": c_match.group(1),
        "token_start": int(c_match.group(3)),
        "token_end": int(c_match.group(5)),
        "start_line": int(c_match.group(2)),
        "label": t_match.group(1),
    }

def parse_rel_line(line: str) -> Dict[str, Union[Dict[str, int], str]]:
    """
    Parse one line from a *.rel file.
    A typical line has the form,
        'c="coronary artery bypass graft" 115:4 115:7||r="TrAP"||c="coronary artery disease" 115:0 115:2'
    This represents two concepts related to one another.
    It can be interpreted as follows,
        'c="<string>" <start_line>:<token_start> <end_line>:<token_end>||r="<type>"||c="<string>"
        <start_line>:<token_start> <end_line>:<token_end>'
    
    Args:
        line (str): A line from the rel file.
    
    Returns:
        Dict[str, Union[Dict[str, int], str]]: A dictionary containing the "head" and "child" token details 
                                               and the "relation" between them.
    """
    c1_part, r_part, c2_part = line.split("||")
    c1_match, r_match, c2_match = (
        re.match(C_PATTERN, c1_part),
        re.match(R_PATTERN, r_part),
        re.match(C_PATTERN, c2_part),
    )
    return {
        "head": {
            "token_start": int(c1_match.group(3)),
            "start_line": int(c1_match.group(2))

        },
        "child": {
            "token_start": int(c2_match.group(3)),
            "start_line": int(c2_match.group(2)),

        },
        "relation": r_match.group(1)
    }

def parse_text(file: Path) -> List[str]:
    """
    Parse a text file and return a list of lines.
    
    Args:
        file (Path): Path to the text file.
    
    Returns:
        List[str]: A list of lines from the text file.
    """
    lines = []
    with open(file, 'r', encoding='utf-8') as f: 
        for line in f:
            clean_line = line.replace("\n", "")
            lines.append(clean_line)
    return lines

def parse_entities(file: Path) -> Dict[int, List[Dict[str, Union[int, str]]]]:
    """
    Parse a *.con file and return a dictionary where the keys are line indices 
    and the values are lists of entities (each represented by a dictionary).
    
    Args:
        file (Path): Path to the con file.
    
    Returns:
        Dict[int, List[Dict[str, Union[int, str]]]]: A dictionary mapping line indices to lists of entity dictionaries.
    """
    entities = {}
    with open(file, 'r', encoding='utf-8') as f: 
        for line in f:
            if not line.strip():
                continue
            entity_dict = parse_con_line(line)
            index = entity_dict["start_line"]
            if index not in entities:
                entities[index] = []

            if entity_dict not in entities[index]:    
                entities[index].append(entity_dict)

    return entities

def parse_relations(file: Path) -> Dict[int, List[Dict[str, Union[Dict[str, int], str]]]]:
    """
    Parse a *.rel file and return a dictionary where the keys are line indices 
    and the values are lists of relation dictionaries (each containing "head", "child", and "relation").
    
    Args:
        file (Path): Path to the rel file.
    
    Returns:
        Dict[int, List[Dict[str, Union[Dict[str, int], str]]]]: A dictionary mapping line indices to lists of relation dictionaries.
    """
    relations = {}
    with open(file, 'r', encoding='utf-8') as f: 
        for line in f:
            if not line.strip():
                continue
            entity_dict = parse_rel_line(line)
            index = entity_dict["head"]["start_line"]
            if index not in relations:
                relations[index] = []
            
            relations[index].append(entity_dict)

    return relations

def get_offset(text: str, token_start: int, token_end: int) -> Tuple[int, int]:
    """
    Given a text, token start, and token end indices, return the corresponding character offsets 
    in the string for the specified tokens.
    
    Args:
        text (str): The text in which tokens are located.
        token_start (int): The starting token index.
        token_end (int): The ending token index.
    
    Returns:
        Tuple[int, int]: The character offsets of the start and end tokens.
    """
    current_pos = 0
    word_start, word_end = None, None
    tokens = text.split()

    for index, token in enumerate(tokens):
        token_start_pos = text.find(token, current_pos)
        token_end_pos = token_start_pos + len(token)

        if index == token_start:
            word_start = token_start_pos
        if index == token_end:
            word_end = token_end_pos
            break
        
        current_pos = token_end_pos
    return word_start, word_end

def match_entities(index: int, entities_dict: dict, text: str) -> Tuple[List[Dict[str, Union[int, str]]], List[Dict[str, Union[int, str]]]]: 
    """
    Match the attributes of the entities at the given index.
    
    Args:
        index (int): The line index for which to match the attributes.
        entities_dict (dict): A dictionary of entities indexed by line number.
        text (str): The text line where entities and relations should be matched.
    
    Returns:
        List[Dict[str, Union[int, str]]]: 
        A list of matched entities.
    """
    ents = entities_dict.get(index, [])
    entities = []
    for entity in ents:
        start, end = get_offset(text, entity["token_start"], entity["token_end"])
        ent_text = (entity["text"]).replace("&apos;", "'")
        entities.append({"text": ent_text, "start": start, "end": end, "token_start": entity["token_start"], "token_end": entity["token_end"], "label": entity["label"]})
    
    return entities

def match_relations(index: int, relations_dict: dict):
    """
    Match the attributes of the relations at the given index.
    
    Args:
        index (int): The line index for which to match the attributes.
        relations_dict (dict): A dictionary of relations indexed by line number.
    
    Returns:
        List[Dict[str, Union[int, str]]]: 
        A list of matched relations.
    """
    rels = relations_dict.get(index, [])
    relations = []
    for relation in rels:
        relations.append({"child": relation["child"]["token_start"], "head": relation["head"]["token_start"], "relation": relation["relation"]})  
    
    return relations

def create_json(directory: Path, output_path: Path):
    """
    Create a JSON file by matching text, con, and rel files, parsing them, 
    and then saving the processed data.
    
    Args:
        text_path (Path): Path to the directory containing text files.
        con_path (Path): Path to the directory containing con files.
        rel_path (Path): Path to the directory containing rel files.
        output_path (Path): Path where the output JSON file should be saved.
    """
    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    data = []

    for txt_file in txt_files:
        con_file = txt_file.replace('.txt', '.con')
        rel_file = txt_file.replace('.txt', '.rel')
        lines = parse_text(txt_file)
        entities_dict = parse_entities(con_file)
        relations_dict = parse_relations(rel_file)
        for index, line in enumerate(lines):
            text = line.replace("&apos;", "'")

            entities = match_entities(index + 1, entities_dict, text)
            filtered_entities = filter_entities(entities) 
            relations = match_relations(index + 1, relations_dict)
            filtered_relations = filter_relations(filtered_entities, relations)
            if filtered_entities:
                data.append({"text": text.lower(), "tokens": filtered_entities, "relations": filtered_relations, "file": str(txt_file)}) 

    save_data(output_path, data)

if __name__ == "__main__":
    typer.run(create_json)