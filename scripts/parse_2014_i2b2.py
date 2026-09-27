import os
from  pathlib import Path
from typing import List, Dict, Union
import sys
import typer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.generate_labels import get_text, get_tags, get_attributes
from scripts.utils import filter_entities, save_data, tokenize_text

def parse_xml(file: Union[str, Path], tokens: dict) -> List[Dict[str, Union[str, int]]]:
    """
    Parses an XML file and extracts entities.
    
    Args:
        file (Path or str): Path to the XML file.
        tokens (dict): Tokenized representation of the text.
    
    Returns:
        List[Dict[str, Union[str, int]]]: Extracted entities.
    """
    entities = []
    tag_map = {}

    entity_tags = get_tags(file, "2014")
    for tag in entity_tags:
        tag_id, start, end, text, type = get_attributes(tag)
        if start in tokens:
            token_start = tokens[start]["index"]
            last_word = text.split()[-1]
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
    return filtered_entities

def create_json(directory: Path, output_path: Path):
    """
    Creates a dataset by extracting text and tokens relations from XML files in a directory.
    
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
        entities = parse_xml(file_path, tokens)
        data.append({"text": text, "tokens": entities}) 
         
    save_data(output_path, data)

if __name__ == "__main__":
    typer.run(create_json)