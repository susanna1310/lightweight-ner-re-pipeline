import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from  pathlib import Path
from typing import List, Union, Dict, Tuple
from scripts.utils import save_data, filter_entities, filter_relations, tokenize_text
import re
import typer
import glob2 as glob

def read_file(file_path: Path) -> str:
    """
    Read and return the content of a file.
    
    Args:
        file_path (Path): Path to the file.
    
    Returns:
        str: Content of the file.
    """
    with file_path.open(encoding='utf-8') as f:
        text = f.read()
        return text.replace("\n", " ")

def get_entites_and_relations_from_ann_file(file_text: str, ann_file: Path) -> Tuple[List[Dict[str, Union[str, int]]], List[Tuple[str, int, int]]]:
    """
    Extract entities and relations from an annotation (.ann) file.
    
    Args:
        file_text (str): Text content of the associated .txt file.
        ann_file (Path): Path to the .ann file.
    
    Returns:
        Tuple[List[Dict[str, Union[str, int]]], List[Tuple[str, int, int]]]:
            - List of extracted entities.
            - List of relations between entities.
    """
    entities = []
    relations = []
    relations_data = []
    existing_entities = set()
    entity_map = {}
    with open(ann_file, 'r', encoding='utf-8') as file:  
        for line in file:
            if not line.strip():
                continue
            
            parts = line.strip().split()
            if parts[0].startswith("T"):
                label = parts[1]
                start = int(parts[2])

                for part in parts[3:]:
                    if ";" not in part and part.isdigit():
                        end = int(part)
                        break
                   
                #have to use the file_text cuz data sometimes add a space within a word   
                text = re.sub(r'\n', ' ', file_text[start:end])
                
                if file_text[start - 1] == " " and ( (not file_text[end].isalpha()) or file_text[end] == " "):
                #remove entities with two labels
                    key = start
                    if key not in existing_entities:
                        entities.append({"text": text, "start": start, "end": end, "label": label})
                        existing_entities.add(key)
                        entity_map[parts[0]] = start
              
            elif parts[0].startswith("R"):
                rel = parts[1]
                arg1 = parts[2][5:]
                arg2 = parts[3][5:] 
                relations_data.append((rel, arg1, arg2)) 
        for rel, arg1, arg2 in relations_data:
            if arg1 in entity_map and arg2 in entity_map:
                relations.append((rel, entity_map[arg1], entity_map[arg2]))
    filtered_entities = filter_entities(entities)
    return filtered_entities, relations

def process_data(tokens: Dict[int, dict], entities: List[dict], relations: List[tuple]) -> Tuple[List[Dict[str, Union[str, int]]], List[Dict[str, Union[str, int]]], List[str], List[bool]]:
    """
    Processes the text to generate entities and relations.

    Args:
        tokens: Dict of Tokens with offset, index and text
        file_text: The original text from the file.
        entities: A list of entity dictionaries with 'text', 'start', 'end', and 'label'.
        relations: A list of relation tuples (relation type, entity1 start index, entity2 start index).

    Returns:
        Tuple:
            - List[Dict[str, Union[str, int]]]: Processed entities with tokenized start and end indices.
            - List[Dict[str, Union[str, int]]]: Processed relations with mapped token indices.
    """
    token_index_dict = {}
    filtered_entities = []
    filtered_relations = []
    for entity in entities:
        start = entity["start"]
        if start in tokens:
            try:
                token_start = tokens[start]["index"]
                token_index_dict[start] = token_start
                filtered_entities.append({
                    "text": entity["text"],
                    "start": start,
                    "end": entity["end"],
                    "token_start": token_start,
                    "label": entity["label"]
                })
            except KeyError:
                error_info = {
                    "end": entity["end"],
                    "text": entity["text"],
                    "missing_token_key": start,
                }
                print(error_info)

    filtered_relations = [
        {"relation": rel, "head": token_index_dict[head_start], "child": token_index_dict[child_start]}
        for rel, head_start, child_start in relations
        if head_start in token_index_dict and child_start in token_index_dict
    ]
    return filtered_entities, filter_relations(filtered_entities, filtered_relations)
 
def create_json(directory: Path, output_path: Path):
    """
    Reads and processes text and annotation files, then saves the extracted data as JSON.

    Args:
        directory (Path): Path to the directory containing .txt and .ann files.
        output_path (Path): Path where the processed JSON data will be saved.
    """
    ann_files = glob.glob(os.path.join(directory, "*.ann"))
    data = []

    for ann_file in ann_files:
        txt_file = ann_file.replace('.ann', '.txt')
        text = read_file(Path(txt_file))
        tokens = tokenize_text(text)
        entities, relations = get_entites_and_relations_from_ann_file(text, ann_file)
        ents, rels = process_data(tokens, entities, relations)
        if ents:
            data.append({"text": text, "tokens": ents, "relations": rels, "file": txt_file}) 
    
    save_data(output_path, data)

if __name__ == "__main__":
    typer.run(create_json)