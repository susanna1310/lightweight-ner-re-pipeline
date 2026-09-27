import xml.etree.ElementTree as ET

#------HELPER FUNCTIONS FOR XML DATA FILES----#

def get_root(file):
    """
    Parses XML file into element tree and returns an ElementTree instance.
    
    Args:
        file : source file containing xml data
    """
    with open(file, "r") as f:
        tree = ET.parse(file)
        root = tree.getroot()
        f.close()
    return (root)

def get_text(file):
    """
    Return the text between <TEXT/>.

    Args:
        file: path to the xml file
    """
    root = get_root(file)
    text_element = root.find('TEXT')
    cdata_content = text_element.text
    return (cdata_content)

def is_relation_tag(tag):
    root = ET.fromstring(tag)
    return (
        'fromID' in root.attrib and
        'toID' in root.attrib and 
        'fromText' in root.attrib and
        'toText' in root.attrib and
        'type' in root.attrib and
        root.attrib['type'].strip() != '' and
        not root.attrib.get('id', '').upper().startswith('SECTIME')
    )

def contains_correct_attributes(tag, dataset):
    """
    Checks if the it has start, end, text and type valeu and is either a EVENT or TIMEX3 tag.
    
    Args:
        tag: tag to check
    """
    root = ET.fromstring(tag)
    return ('start' in root.attrib and 
            'end' in root.attrib and 
            'text' in root.attrib and
            ('type' in root.attrib or 'TYPE' in root.attrib) 
             and ((dataset == "2012" and ('EVENT' in tag or 'TIMEX3' in tag)) or dataset == "2014")
            )

def get_relation_tag_attributes(tag):
    root = ET.fromstring(tag)
    from_ID = ""
    to_ID = ""
    type = ""
    if 'fromID' in root.attrib:
        from_ID = root.attrib['fromID']
    if 'toID' in root.attrib:
        to_ID = root.attrib['toID']
    if 'type' in root.attrib:
        type = root.attrib['type']
    return from_ID, to_ID, type

def get_attributes(tag):
    """
    Return the start offset, end offset, the test at the offset, and the type of the text. 
    
    Args:
        data : tag </> which includes a named entity example
    """
    root = ET.fromstring(tag)
    start = -1
    end = -1
    text = ""
    tag_id = ""
    if 'id' in root.attrib:
        tag_id = root.attrib['id']
    if 'start' in root.attrib:
        start = int(root.attrib['start'])
    if 'end' in root.attrib:
        end = int(root.attrib['end'])
    if 'text' in root.attrib:
        text = root.attrib['text']
    if 'type' in root.attrib:
        event_type = root.attrib['type']
    elif 'TYPE' in root.attrib:
        event_type = root.attrib['TYPE']
    return tag_id, start, end, text, event_type


def get_start(tag):
    """
    Returns the start offset of the text inside the tag.
    Args:
        data : tag </> 
    """
    root = ET.fromstring(tag)
    start = -1
    if 'start' in root.attrib:
            start = int(root.attrib['start'])
    return start

def get_relation_tags(file):
    root = get_root(file)
    tags_elements = root.findall('.//TAGS/*')
    tags = [ET.tostring(element).decode('utf-8').replace('\n', '') for element in tags_elements]
    
    filtered_tags = filter(is_relation_tag, tags)
    filtered_tags_list = list(filtered_tags)
    return(filtered_tags_list)

def get_tags(file, dataset):
    """
    Return a list of <TAGS/>.
    Args:
        file : path to the xml file
    """
    root = get_root(file)
    tags_elements = root.findall('.//TAGS/*')
    tags = [ET.tostring(element).decode('utf-8').replace('\n', '') for element in tags_elements]
    
    filtered_tags = filter(lambda tag: contains_correct_attributes(tag, dataset), tags)
    filtered_tags_list = list(filtered_tags)
    
    sorted_tags = sorted(filtered_tags_list, key=get_start)
    return (sorted_tags)

def check_text_at_offset(data, start, end, expected_text):
    """
    Returns a true or false, depending if the text at the given offset is equal to the  expected_text.
    
    Args: 
        data : text to look for the expected_text in
        start : start of the offset
        end : end of the offset
        expected_text : text which is expected at the given offset
    """
    actual_text = data[start:end]
    return actual_text == expected_text
 
def get_data(data, file, dataset):
    """
    Checks if the tags are correct and returns a tuple of the correct entities and tags.
    
    Args: 
        data : text including the expected text of the tags
        tags : list of tags including start offset, end offset, text and type 
    """
    tags = get_tags(file, dataset)
    labels = []
    entities = []
    filteredTags = []
    for tag in tags:
        _, start, end, text, type = get_attributes(tag)
        if (type != "" and text != "" and start != -1 and end != -1):
            if (check_text_at_offset(data, start, end, text)):
                entities.append((text, type))
                labels.append(type)
                filteredTags.append(tag)
    return (filteredTags, labels, entities)


