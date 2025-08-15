# Named Entity Recognition and Relation Extraction for Medical Records
This repository includes just the README of my Bachelor Thesis, since my project is used for further research at TUM, therefore the code is private for now.

## Description
This project originated as part of the KAP (Clinical Application Project) and has been significantly extended to form the core of a Bachelor's thesis.
The goal of the KAP was to create a lean and robust NLP pipeline that can accurately perform NER and subsequent analysis on various datasets, even in environments with limited computational resources.
The goal of the Bachelor's Thesis was to optimize existing NER approaches and augment them with a RE component. 
To achieve this, the project will leverage existing NLP and machine learning libraries, specifically spaCy and scikit-learn, to develop a custom pipeline. Further it includes a Optuna script for hyperparameter optimization. This project includes a user interface (UI) to facilitate the use and demonstration of the developed models. 
The i2b2 (Informatics for Integrating Biology & the Bedside) datasets from 2010, 2012, 2014, and 2018 were utilized for model training and evaluation. 


## Getting Started
### Prerequisites
In order to run this project you need **Python** and **Node.js** installed on your local machine.
### Setup
Clone this repository to your desired folder.

### Installation
To install the dependencies listed in the ```requirements.txt``` file you can use an virtual environment.

First, create and activate a virtual environment to isolate your dependencies from the system-wide Python installation.

**On Windows**
~~~
python -m venv venv
venv\Scripts\activate
~~~

**On macOs/Linux**
~~~
python3 -m venv venv
source venv/bin/activate
~~~

Once your virtual environment is active, use ```pip``` to install the dependencies listed in the ```requirements.txt``` file:
~~~
pip install -r requirements.txt
~~~

## Models 
The project provides trained NER and RE models for the utilized i2b2 datasets.

### NER Models:
These models are organized within the `ner_models/` folder, with their names reflecting the i2b2 dataset year they were trained on (e.g., the model in the `ner_model_2012/` folder was trained on the i2b2 dataset from 2012).

To clearly delineate the progressive optimization steps undertaken as part of this Bachelor's thesis, the NER models for the years 2012, 2014, and 2018 are versioned as follows:

`[YEAR]/` (e.g., `ner_model_2012/`): Represents the baseline NER models, which originated from the initial KAP.

`[YEAR].2/` (e.g., `ner_model_2012.2/`): Denotes NER models that have undergone data-centric optimization as the first enhancement step.

`[YEAR].3/` (e.g., `ner_model_2012.3/`): Represents the final, most optimized NER models, further refined through hyperparameter optimization (HPO) using Optuna.

For the 2010 dataset, only one NER model version (`ner_model_2010/`) is provided. This dataset was exclusively incorporated and optimized within the scope of this Bachelor's Thesis, and therefore, this version represents its best and final configuration.

### RE Models:
Pre-trained RE models are located in the `re_models/ ` folder. These models are available for the i2b2 datasets from 2010, 2012, and 2018. These RE models leverage the corresponding optimized NER models to identify semantic relationships between extracted entities.

## Usage
This project utilizes `invoke` for streamlined command execution, providing easy access to various workflows such as data preparation, model training, and evaluation. This allows you to perform complex operations with simple commands.

To view all available commands and their descriptions, run:
~~~
invoke --list
~~~
For detailed information on any specific command, use: 
~~~
invoke --help <command_name>
# Example: invoke --help train-ner
~~~
Below are the examples of key commands:
- **split**: Divide raw i2b2 data (XML, ANN, CON) into train, dev, and test sets.
    ~~~
    invoke split --directory <path_to_data> --file-type <xml|ann|con> [--txt-directory <path_to_txt>] [--rel-directory <path_to_rel>]
    # Example for XML:
    invoke split ./path/to/data xml
    ~~~
- **convert-json**: Transform split data into a JSON format suitable for spaCy.
    ~~~
    invoke create-json --data <path_to_input_data> --output <path_to_output.json> --year <2010|2012|2014|2018>
    # Example:
    invoke create-json ./files/train_data_raw ./files/train.json 2012
    ~~~
- **convert-spacy**: Convert JSON data into spaCy's binary .spacy format for training.
    ~~~
    invoke create-spacy --json-file <path_to_input.json> --output <path_to_output.spacy> --data-type <ner|re>
    ~~~
- **train-ner**: Train a NER model
    ~~~
    invoke train-ner --output <output_model_path> --train <path_to_train.spacy> --dev <path_to_dev.spacy> [--config <path_to_config.cfg>]
    #Example:
    invoke train-ner ./ner_models/my_new_ner ./files/train_ner.spacy ./files/dev_ner.spacy --config ./path/to/config
    ~~~
- **train-re**: Train a RE model
    ~~~
    invoke train-re --output <output_model_path> --train <path_to_train.spacy> --dev <path_to_dev.spacy> --model <pat_to_ner_model> [--config <path_to_config.cfg>]
    ~~~
- **ner**: Create .spacy data and train and evaluate NER model
    ~~~
    invoke ner --train-json <path_to_train_json> --dev-json <path_to_dev_json> --test-json <path_to_test_json> --output <output_re_model_path>
    ~~~
- **ner**: Create .spacy data, train NER model and train and evaluate RE model
    ~~~
    invoke re --train-json <path_to_train_json> --dev-json <path_to_dev_json> --test-json <path_to_test_json> --output <output_re_model_path>
    ~~~
- **evaluate-ner**: Evaluate a trained NER model 
    ~~~
    invoke evaluate-ner <dataset_year> 
    # Example: Evaluate the default best NER model for 2012:
    invoke evaluate-ner 2012

    # Or evaluate a specific model with explicit paths:
    invoke evaluate-ner <path_to_model> <path_to_test.spacy>
    # Example:
    invoke evaluate-ner ./ner_models/2012.3/model-best ./training/test_12.spacy
    ~~~
- **evaluate-re**: Evaluate a trained RE model 
    ~~~
    invoke evaluate-re <dataset_year> [--use-gold-ne] [--print-details]
    # Example: Evaluate the default best RE model for 2018 with gold entities and detailed output:
    invoke evaluate-re 2018 --use-gold-ne --print-details

    # Or evaluate a specific model with explicit paths:
    invoke evaluate-re <path_to_model> <path_to_test.spacy> [--use-gold-ne] [--print-details]
    # Example:
    invoke evaluate-re ./re_models/re_model_2012/model-best ./training/test_12.spacy
    ~~~

## Run UI
To start the UI, open your terminal inside the project and inside the **backend**
folder run:
~~~
python app.py
~~~
to start the backend.
Then inside the **frontend** folder run:
~~~
npm install #if not already run
npm start
~~~ 
to start the frontend. The fronted runs on https://localhost:3000.
### UI Features
- **Uploading text files**: Users can upload PDF, TXT, or XML files. The text is extracted and sent to the backend for analysis using the selected model. The text with the marked entities is then displayed.
- **Model switching**: Users can choose between different NER models that have been specifically trained for various medical datasets (e.g., 2010, 2012, 2014, 2018). Selecting a new model triggers a re-analysis of the text, updating the results accordingly.
- **Filtering entities**: Users can filter the visualized entities by labels to specifically highlight certain entity types and enable a more focused analysis. With the extension of the models to include RE, the following additional features were added in this work:
- **Displaying relations**: By clicking on a marked entity, users can open a sidebar showing all relations originating from the clicked entity.
- **Threshold filter**: Users can filter the relations by threshold probability to specifically highlight certain probability values. The default probability value is 0.05.
  
![UI](ui/ui.png)

## Project Structure 
```bash
.
├── backend/                # Implementation of the backend
├── configs                 # Configs files for NER and RE 
│   ├── ner_config.cfg
│   └── re_config.cfg
├── frontend/                   # Implementation of the frontend
├── ner_files                   # Scripts for NER data preparation and HPO
│   ├── generate_training_data.py   # Old script to create JSON files
│   ├── hp_tuning.py                # Code for HPO
│   ├── json2spacy.py               # Converter for JSON to .spacy for NER
├── ner_models                      # Trained NER models
│   ├── ner_model_2010
│   ├── ner_model_2012
│   ├── ner_model_2012.2
│   ├── ner_model_2012.3
│   ├── ner_model_2014
│   ├── ner_model_2014.2
│   ├── ner_model_2014.3
│   ├── ner_model_2018
│   ├── ner_model_2018.2
│   └── ner_model_2018.3
├── re_models                   # Trained RE models
│   ├── re_model_2010
│   ├── re_model_2012
│   └── re_model_2018
├── README.md
├── rel_files                   # Scripts for RE data preparation and HPO
│   ├── custom_functions.py
│   ├── json2spacy_re.py            # Converter for JSON to .spacy for RE
│   ├── rel_model.py                # Custom Thinc modle 
│   └── rel_pipe.py                 # Custom spaCy pipeline
├── requirements.txt            
├── scripts                     # Utilities scripts
│   ├── generate_labels.py          # Helper functions for XML data extraction
│   ├── parse_2010_i2b2.py          # Converts i2b2 2010 data to JSON file
│   ├── parse_2012_i2b2.py          # Converts i2b2 2012 data to JSON file
│   ├── parse_2014_i2b2.py          # Converts i2b2 2014 data to JSON file
│   ├── parse_2018_i2b2.py          # Converts i2b2 2018 data to JSON file
│   ├── split_data.py               # Splits raw data in train,dev,test folders
│   └── utils.py
├── tasks.py                    # File for python invoke 
├── testing                     # Evaluation and visualization tools
│   ├── evaluate_ner_model.py       # Evaluate NER model 
│   ├── evaluate_re_model.py        # Evaluate RE model 
│   └── visualize_data.py           # Visualizes confusion matrix and classifiction report 
```
