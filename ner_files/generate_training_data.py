import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from spacy.lang.en import English
from spacy.pipeline import EntityRuler
from spacy.language import Language
import xml.etree.ElementTree as ET
import json
from scripts.generate_labels import get_data, get_text
import nltk
import re

#------USED IN KAP FOR GENERATING JSON FILES----#

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
from nltk.tokenize import sent_tokenize

patterns = []

def save_data(file, data):
    """
    Saves the given data in the give path.

    Args: 
        file: file in which the data should be written
        data: data that should go into the file 
    """
    with open (file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def create_training_data(tags):
    """
    Returns a lsit of tuples including the label and the text. 

    Args:
        tags: list of tags including start offset, end offset, text and type
    """
    patterns = []
    for tag in tags:
        root = ET.fromstring(tag)
        text = ""
        type = ""
        if 'text' in root.attrib:
            text = root.attrib['text']
        if 'type' in root.attrib:
            type = root.attrib['type']
        elif 'TYPE' in root.attrib:
            type = root.attrib['TYPE']
        if text != "" and type != "":
            pattern = {"label": type, "pattern": text}
            patterns.append(pattern)
    return (patterns)

@Language.factory("ent_ruler")
def get_ruler(nlp, name):
    """
    Creates ruler and adds pattern to it. 

    Args: 
        nlp : receives the current nlp object and lets you access the vocab
        name : the name of the component instance
    """
    ruler = EntityRuler(nlp)
    ruler.add_patterns(patterns)
    return ruler

def generate_rules():
    """
    Generates rules and adds them into nlp. Return nlp with generated rules.
    """
    nlp = English()
    Language.factory("ent_ruler", func=get_ruler)
    nlp.add_pipe("ent_ruler", name="med_ner", last="True")
    return nlp

def test_model(model,text):
    """
    Returns a list of tupels including the given text and the found entity, by start offset, end offset and label.

    Args:
        model : nlp with pattern
        text : text to look for entities in 
    """
    doc = model(text)
    results = []
    entities = []
    for ent in doc.ents:
        entities.append((ent.start_char, ent.end_char, ent.label_))
    if len(entities) > 0:
        results = [text, {"entities": entities}]
    return (results)

def normalize_text(text):
    """
    Normalizes text by reducing consecutive white spaces 
    to a single space, and separates punctuation from adjacent words by adding a space.

    Args:
        text: text to normalize
    """
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\w)([,;!?])', r'\1 \2', text)
    return text.strip()


def generate_tag(directory, dataset):
    """
    Iterates over all xml files in the given directory and extracts the tags
    
    Args:
        directory: path to directory with xml files
    """
    xml_files = os.listdir(directory)
    tags = []
    for file in xml_files:
        text = get_text(directory + "/" + file)
        new_tags, _ , _= get_data(text, directory + "/" + file, dataset)
        tags += new_tags
    return (tags)

def create_iob_patterns(directory):
    """
    Filters out the labels and texts of the iob file and returns them as list of tuples

    Args:
        directory: path to directory containing iob files
    """
    iob_files = [f for f in os.listdir(directory) if f.endswith('.iob')]
    patterns = []
    for file_path in iob_files:
        with open((directory + "/" + file_path), 'r') as file:
            current_label = None
            current_words = []
            for line in file:
                if line.strip() == "":
                    continue  
                
                word, tag = line.split()

                if tag == 'O':  
                    if current_label is not None:
                        patterns.append({"label": current_label, "pattern": " ".join(current_words)})
                        current_label = None
                        current_words = []
                else:
                    prefix, label = tag.split('-')
                    if prefix == 'B':  # Beginning of a new entity
                        if current_label is not None:
                            patterns.append({"label": current_label, "pattern": " ".join(current_words)})
                        current_label = label
                        current_words = [word]
                    elif prefix == 'I' and label == current_label:  # Inside of an existing entity
                        current_words.append(word)
                    else:
                        if current_label is not None:
                            patterns.append({"label": current_label, "pattern": " ".join(current_words)})
                        current_label = label
                        current_words = [word]

            if current_label is not None:
                patterns.append({"label": current_label, "pattern": " ".join(current_words)})

    return patterns

def get_txt_text(file):
    """
    Returns the text of the txt file

    Args:
        file: path to txt file
    """
    with open(file, 'r', encoding='utf-8') as f:
        text = f.read()
        return text

def generate_iob_data(path, output):
    global patterns 
    patterns = create_iob_patterns(path)
    nlp = generate_rules()
    TRAIN_DATA = []
    txt_files = [f for f in os.listdir(path) if f.endswith('.txt')]
    for file in txt_files:
        text = get_txt_text(path + "/" + file)
        sentences = sent_tokenize(text)
        for sentence in sentences:
            sentence = normalize_text(sentence)
        
            results = test_model(nlp, sentence)
            if results is not None and len(results) > 0:
                TRAIN_DATA.append(results)
    save_data(output, TRAIN_DATA)
    print("Data successfully saved!")

def generate_data(path, output, dataset):
    """
    Uses the path to get the xml data and creates train or dev data with it and saves it to the output path as json.
    
    Args: 
        path: path to xml data
        output: output file 
    """
    tags = generate_tag(path, dataset)
    global patterns 
    patterns = create_training_data(tags)
    nlp = generate_rules()
    TRAIN_DATA = []

    xml_files = [f for f in os.listdir(path) if f.endswith('.xml')]
    for file in xml_files:
        text = get_text(path + "/" + file)
        sentences = sent_tokenize(text)
        for sentence in sentences:
            sentence = normalize_text(sentence)
        
            results = test_model(nlp, sentence)
            if results is not None and len(results) > 0:
                TRAIN_DATA.append(results)

    save_data(output, TRAIN_DATA)
    print("Data successfully saved!")


