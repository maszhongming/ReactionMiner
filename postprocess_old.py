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

def cleanJson(jsonPath):
    with open(jsonPath) as fin:
        contents = fin.read()
        # Strip any leading/trailing whitespace
        contents = contents.strip()
        # Parse the JSON data
        data = json.loads(contents)
        content = data["content"]
    cleaned_paragraphs = clean_paragraphs(content)
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


def similarity(fragment1, fragment2):
    # convert sequence to id
    fragment1_emb = mpnet_emb(fragment1)
    fragment2_emb = mpnet_emb(fragment2)

    cosine_similarity = np.dot(fragment1_emb, fragment2_emb)

    return cosine_similarity


def isFigureDiscription(text):
    text_lower = text.lower()
    tokens = text_lower.split(" ")
    if tokens[0] == "scheme" or tokens[0] == "figure":
        if len(tokens) < 15:
            return True

    return False

def clean_paragraphs(contents):
    cleaned_paragraphs = []
    curr_paragraph = ""
    curr_paragraph_idx = -1

    decay_rate = 0.99

    for idx, paragraph in enumerate(contents):
        if isFigureDiscription(paragraph):
            continue

        distance = idx - curr_paragraph_idx
        score = similarity(curr_paragraph, paragraph) * (decay_rate**distance)

        if score > 0.3 or curr_paragraph_idx == -1:
            cleaned_paragraphs.append(paragraph)
            curr_paragraph = paragraph
            curr_paragraph_idx = idx

    return cleaned_paragraphs


def concat_paragraphs(paragraphs):
    complete_paragraphs = []
    curr_idx = 0
    paragraph = ""

    for idx, current_segment in enumerate(paragraphs):
        terminals = [".", "?", "!"]

        if (
            current_segment[0].isupper() and current_segment[-1] in terminals
        ) and paragraph != "":  # clean up trash
            paragraph = ""
            complete_paragraphs.append(current_segment)
        elif (
            (current_segment[0].isupper() and current_segment[-1] in terminals)
            or idx == 0
            or idx == len(paragraphs) - 1
        ):  # Complete a paragraph
            complete_paragraphs.append(current_segment)
        elif (
            current_segment[0].isupper() and current_segment[-1] not in terminals
        ):  # Start of a paragraph
            paragraph = current_segment
        elif (
            current_segment[0].isupper() == False
            and current_segment[-1] not in terminals
        ):  # Middle of a paragraph
            paragraph += current_segment
        elif (
            current_segment[0].isupper() == False and current_segment[-1] in terminals
        ):  # End of a paragraph
            paragraph += current_segment
            complete_paragraphs.append(paragraph)
            paragraph = ""

    return complete_paragraphs
