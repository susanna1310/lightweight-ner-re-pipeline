import os
from  pathlib import Path
from typing import List, Tuple, Dict, Union
import sys
import typer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.generate_labels import get_text, get_tags, get_attributes, get_relation_tags, get_relation_tag_attributes
from scripts.utils import filter_entities, filter_relations, save_data, tokenize_text

def parse_xml(file: Path, tokens: dict) -> Tuple[List[Dict[str, Union[str, int]]], List[Dict[str, Union[str, int]]]]:
    """
    Parses an XML file and extracts entities and relations.
    
    Args:
        file (Path): Path to the XML file.
        tokens (dict): Tokenized representation of the text.
    
    Returns:
        Tuple[List[Dict[str, Union[str, int]]], List[Dict[str, Union[str, int]]]]: Extracted entities and relations.
    """
    entities = []
    relations = []
    tag_map = {}

    entity_tags = get_tags(file, "2012")
    for tag in entity_tags:
        tag_id, start, end, text, type = get_attributes(tag)
        if start in tokens:
            token_start = tokens[start]["index"]
            last_word = text.split()[-1]
            tag_map[token_start] = tag_id
            token_key = end - len(last_word)
            try:
                token_end = tokens[token_key]["index"]
                tag_map[token_start] = tag_id
                entities.append({
                    "text": text,
                    "start": start,
                    "end": end,
                    "token_start": token_start,
                    "token_end": token_end,
                    "label": type
                })
            except KeyError:
                error_info = {
                        "file": file,
                        "end": end,
                        "text": text,
                        "missing_token_key": token_key,
                    }
                print(error_info)

    filtered_entities = filter_entities(entities)
    token_map = {}
    for entity in filtered_entities:
        token_index = entity["token_start"]
        if token_index in tag_map:
            token_map[tag_map[token_index]] = token_index
    rel_tags = get_relation_tags(file)
    for tag in rel_tags:
        from_ID, to_ID, type = get_relation_tag_attributes(tag)
        if from_ID in token_map and to_ID in token_map:
            relations.append({"child": token_map[to_ID], "head": token_map[from_ID], "relation": type})  
    
    filtered_relations = filter_relations(filtered_entities, relations)
    return filtered_entities, filtered_relations

def create_json(directory: Path, output_path: Path):
    """
    Creates a dataset by extracting text, tokens, and relations from XML files in a directory.
    
    Args:
        directory (Path): Path to the directory containing XML files.
        output_path (Path): Path to save the extracted dataset as JSON.
    """
    xml_files = [f for f in os.listdir(directory) if f.endswith('.xml')]
    data = []
    for file in xml_files:
        file_path = str(directory) + "/" + file
        text = get_text(file_path)
        tokens = tokenize_text(text)
        entities, relations = parse_xml(file_path, tokens)
        if entities:
            data.append({"text": text, "tokens": entities, "relations": relations, "file": file}) 
         
    save_data(output_path, data)

if __name__ == "__main__":
    typer.run(create_json)