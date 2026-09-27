import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import spacy
from flask import Flask, jsonify, request
from flask_cors import CORS
from spacy import displacy
import pdfplumber
from spacy.tokens import Doc
from typing import Tuple
import numpy as np
# make the factory work
from rel_files.rel_pipe import make_relation_extractor, score_relations
# make the config work
from rel_files.rel_model import create_relation_model, create_classification_layer, create_instances, create_tensors
app = Flask(__name__)
CORS(app)

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "re_models"))

nlp = spacy.load(os.path.join(MODELS_DIR, "re_model_2010", "model-best"))
threshold = 0.05

def get_relations(doc: Doc) -> Tuple[int,int,str]:
    rels = []
    entities = list(doc.ents)
    for (start1, start2), rel_dict in doc._.rel.items():
        try:
            e1_index = next(i for i, ent in enumerate(entities) if ent.start == start1)
            e2_index = next(i for i, ent in enumerate(entities) if ent.start == start2)
            #for k, v in rel_dict.items():
            label, v = max(rel_dict.items(), key=lambda item: item[1])
            if v > threshold:
                value = np.float32(v)
                native_value = float(value)
                target_ent = entities[e2_index]
                rels.append((e1_index, e2_index, label, native_value, target_ent.text, target_ent.label_))

        except StopIteration:
            print(f"Could not find matching entity for start indices {start1} or {start2}")
            continue
    return rels

# assigns a color from the palette to each entity label
# @param ents: list of entities
def get_colors(ents):
    labels = [ent.label_ for ent in ents]
    labels = list(set(labels))
    labels.sort()
    color_palette = ["#f65356",  "#fb8066",  "#fea671",  "#fec979", "#feea80", "#7ecefd", "#d7e586",  "#a5de94",  "#5daad8",  "#8187c7",  "#c56bba", "#45a2b7","#72aba5"]

    if len(labels) < 6:
        color_palette = [ "#7ecefd", "#feea80", "#d7e586",  "#fec979",  "#fb8066"]

    colors = {label: color for label, color in zip(labels, color_palette)}
    return colors


# processes text data with a given NLP model, extracts entities, assigns colors to them, 
# and returns the rendered HTML along with unique entity labels and the text. 
# @param nlp: NLP model
# @param data: text to process
def get_data(data):
    doc = nlp(data)
    ents = list(doc.ents)
    colors = get_colors(ents)
    html = displacy.render(doc, style="ent", options={"colors": colors})
    labels = []
    
    if ents:
        labels = list(set([ent.label_ for ent in ents]))
    relations = get_relations(doc)
    return jsonify({'html': html, 'labels': labels, 'text': data, 'relations':relations})

# Is called from the FE when a new model was selected. It uses the provided text to run on the given model and 
# returns the rendered HTML along with unique entity labels and the text.
@app.route('/api/model', methods=['POST'])
def change_model():
    global nlp
    if 'text' not in request.json:
        return jsonify({'error': 'No text provided in the request'}), 400
    if 'model' not in request.json:
        return jsonify({'error': 'No label provided in the request'}), 400
    data = request.json['text']
    model = request.json['model']
    if "2012" in model:
        nlp = spacy.load(os.path.join(MODELS_DIR, "re_model_2012", "model-best"))
    elif "2010" in model:
        nlp = spacy.load(os.path.join(MODELS_DIR, "re_model_2010", "model-best"))
    elif "2014" in model:
        nlp = spacy.load(os.path.join("..","ner_models", "ner_model_2014", "model-best"))
    else:
        nlp = spacy.load(os.path.join(MODELS_DIR, "re_model_2018", "model-best"))
    return get_data(data)

# Is called from the FE when a new threshold was selected. It uses the prodived text,
# to create the visualized text, filtering the relation by the > threshold .
# Returns the visulaized text as in a html
@app.route('/api/threshold', methods=['POST'])
def change_threshold():
    global threshold
    if 'text' not in request.json:
        return jsonify({'error': 'No text provided in the request'}), 400
    if 'threshold' not in request.json:
        return jsonify({'error': 'No label provided in the request'}), 400
    data = request.json['text']
    threshold = float(request.json['threshold'])
    return get_data(data)
    
# Is called from the FE when a new filter was selected. It uses the prodived text,
# to create the visualized text with only the provided label's named entities being colored.
# Returns the visulaized text as in a html
@app.route('/api/filter', methods=['POST'])
def filter_text():
    if 'text' not in request.json:
        return jsonify({'error': 'No text provided in the request'}), 400
    if 'label' not in request.json:
        return jsonify({'error': 'No label provided in the request'}), 400
    data = request.json['text']
    label = request.json['label']
    doc = nlp(data)
    entities = list(doc.ents)
    colors = {}
    options = {}
    if label == "ALL LABELS":
        entity_ids = list(range(len(entities)))
        colors = get_colors(entities)
        options = { "colors": colors}
    else:
        entity_ids = [i for i, ent in enumerate(entities) if ent.label_ == label]
        colors = {label: "#7ecefd"}
        options = {"ents": [label], "colors": colors}
    html = displacy.render(doc, style="ent", options=options)
    return jsonify({'html': html, 'entityIds': entity_ids})

# Is called from the FE whenever a file is uploaded. It extract the text from the provided file and 
# returns the rendered HTML along with unique entity labels and the text.
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    data = ''
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file.filename.endswith('.pdf'):
        # Handle PDF file
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                data += page.extract_text()
    else:
        # Handle XML file
        data = file.read().decode('utf-8')
    return get_data(data)

if __name__ == '__main__':
    app.run(debug=True)
