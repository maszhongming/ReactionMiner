import json
from tqdm import tqdm
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
import math
from helpers.fileIOHelper import outputCleanJsonFile
import time 

device = torch.device(0)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
threshhold_value = 0.12

# import pretrained model
mpnet_tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-mpnet-base-v2")
mpnet_model = AutoModel.from_pretrained("sentence-transformers/all-mpnet-base-v2", output_hidden_states=True).to(device)

# driver function
# clean noise information
def cleanJson(jsonPath, threshold = threshhold_value):
    with open(jsonPath) as fin:
        contents = fin.read()
        # Strip any leading/trailing whitespace
        contents = contents.strip()
        # Parse the JSON data
        data = json.loads(contents)
        content = data["content"]
    cleaned_paragraphs = clean_paragraphs(content, threshold)
    complete_paragraphs = concat_paragraphs(cleaned_paragraphs)
    data["content"] = complete_paragraphs
    outputCleanJsonFile(jsonPath, data)
    return complete_paragraphs

# obtain paragraph embedding
def mpnet_emb(text):
    input_ids = (torch.tensor(mpnet_tokenizer.encode(text.lower(), max_length=512, truncation=True)).unsqueeze(0).to(device))
    input_ids = input_ids[:, :512]
    outputs = mpnet_model(input_ids)
    hidden_states = outputs[2][-1][0]
    emb = torch.mean(hidden_states, dim=0).to(device)
    emb = np.array([float(x) for x in emb])
    magnitude = np.linalg.norm(emb)
    if math.isnan(magnitude):
        emb = np.zeros(len(emb))
    else:
        emb = emb / magnitude
    return emb

# obtain cosine similarity score between anchor paragraphs and given paragraph
def similarity(anchor_paragraphs, paragraph):
    # convert sequence to id
    paragraph_emb = mpnet_emb(paragraph)
    similarity = 0
    for fragment in anchor_paragraphs:
        fragment_emb = mpnet_emb(fragment)
        similarity += np.dot(fragment_emb, paragraph_emb)
    return similarity / len(anchor_paragraphs)

# given a paper, decide anchor paragraph by finding the longest paragraph in the first 1/3 of the paper
def get_longest_string_first_half(paper):
    half_index = len(paper) // 3
    first_half = paper[:half_index]
    longest = ''
    for string in first_half:
        if len(string) > len(longest):
            longest = string
    return longest

# given a paragraph, filter noise information by cosine similarity score
def clean_paragraphs(paragraphs, threshold = threshhold_value):
    cleaned_paragraphs = []
    anchor_paragraph = get_longest_string_first_half(paragraphs)
    anchor_paragraphs = [anchor_paragraph]
    for idx, paragraph in enumerate(paragraphs):
        score = similarity(anchor_paragraphs, paragraph)
        if score > threshold:
            cleaned_paragraphs.append(paragraph)
            if len(anchor_paragraphs) == 5:
                del anchor_paragraphs[0]
                anchor_paragraphs.append(paragraph)        
    return cleaned_paragraphs

# concatenate incomplete paragraphs across two pages
def concat_paragraphs(paragraphs):
    complete_paragraphs = []
    paragraph = ""
    for idx, current_segment in enumerate(paragraphs):
        terminals = [".", "?", "!"]
        if not current_segment:
            continue
        # a complete paragraph
        if (( current_segment[-1] in terminals or idx== len(paragraphs) - 1 or idx==0 ) and paragraph == ""):  
            complete_paragraphs.append(current_segment)
        # middle of a paragraph
        elif (current_segment[-1] not in terminals):  
            paragraph += current_segment
        # end of a paragraph
        elif (current_segment[-1] in terminals):  
            paragraph += current_segment
            complete_paragraphs.append(paragraph)
            paragraph = ""
    return complete_paragraphs

if __name__ == "__main__":
    print("Using device:", DEVICE)

