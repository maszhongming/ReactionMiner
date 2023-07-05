import json
from tqdm import tqdm
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
import math
from helpers.fileIOHelper import outputCleanJsonFile

device = torch.device(4)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
mpnet_tokenizer = AutoTokenizer.from_pretrained(
    "sentence-transformers/all-mpnet-base-v2"
)
mpnet_model = AutoModel.from_pretrained(
    "sentence-transformers/all-mpnet-base-v2", output_hidden_states=True
).to(device)

def cleanJson(jsonPath, title = '', threshold = 0.2):
    with open(jsonPath) as fin:
        contents = fin.read()
        # Strip any leading/trailing whitespace
        contents = contents.strip()
        # Parse the JSON data
        data = json.loads(contents)
        content = data["content"]
    cleaned_paragraphs = clean_paragraphs(content, title, threshold)
    complete_paragraphs = concat_paragraphs(cleaned_paragraphs)
    data["content"] = complete_paragraphs
    outputCleanJsonFile(jsonPath, data)
    return complete_paragraphs

def mpnet_emb(text):
    input_ids = (
        torch.tensor(
            mpnet_tokenizer.encode(text.lower(), max_length=512, truncation=True)
        )
        .unsqueeze(0)
        .to(device)
    )
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


def similarity(anchor_paragraphs, paragraph):
    # convert sequence to id
    paragraph_emb = mpnet_emb(paragraph)
    
    anchor_emb = []
    similarity = 0
    for fragment in anchor_paragraphs:
        fragment_emb = mpnet_emb(fragment)
        similarity += np.dot(fragment_emb, paragraph_emb)
        
    return similarity / len(anchor_paragraphs)

def get_longest_string_first_half(strings):
    half_index = len(strings) // 3
    # print(half_index)
    
    first_half = strings[:half_index]
    longest = ''
    
    for string in first_half:
        if len(string) > len(longest):
            longest = string
    
    return longest

def clean_paragraphs(paragraphs, title = '', threshold = 0.3):
    
    cleaned_paragraphs = []

    if title != '':
        anchor_paragraph = title
    else:
        anchor_paragraph = get_longest_string_first_half(paragraphs)
    
    anchor_paragraphs = [anchor_paragraph]
    
    # print("Anchor:", anchor_paragraphs)
    
    decay_rate = 1
    
    for idx, paragraph in enumerate(paragraphs):

        score = similarity(anchor_paragraphs, paragraph)
        
        if score > threshold:
            
            # print(idx, score, paragraph)
            # print()
            
            cleaned_paragraphs.append(paragraph)
            
            if len(anchor_paragraphs) == 5:
                del anchor_paragraphs[0]
                anchor_paragraphs.append(paragraph)
            
            curr_paragraph = paragraph
            curr_paragraph_idx = idx
    
    return cleaned_paragraphs


def concat_paragraphs(paragraphs):
    complete_paragraphs = []
    curr_idx = 0
    paragraph = ""

    for idx, current_segment in enumerate(paragraphs):
        terminals = [".", "?", "!"]
        if not current_segment:
            continue
        if (
            current_segment[0].isupper() and current_segment[-1] in terminals
        ) and paragraph != "":  # clean up trash
            paragraph = ""
            complete_paragraphs.append(current_segment)
        elif (
            current_segment[0].isupper() and current_segment[-1] in terminals
            or idx == 0
            or idx == len(paragraphs) - 1
        ):  # Complete a paragraph
            complete_paragraphs.append(current_segment)
        elif (
            current_segment[0].isupper() and current_segment[-1] in terminals
        ):  # Start of a paragraph
            paragraph = current_segment
        elif (
            current_segment[0].isupper() == False
            and current_segment[-1] not in terminals
        ):  # Middle of a paragraph
            paragraph += current_segment
        elif (
            current_segment[0].isupper() and current_segment[-1] in terminals
        ):  # End of a paragraph
            paragraph += current_segment
            complete_paragraphs.append(paragraph)
            paragraph = ""

    return complete_paragraphs

if __name__ == "__main__":
    print("Using device:", DEVICE)

