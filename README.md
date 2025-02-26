# 🧪 ReactionMiner
**Official Repository for the EMNLP 2023 Demo Paper**  
[Reaction Miner: An Integrated System for Chemical Reaction Extraction from Textual Data](https://aclanthology.org/2023.emnlp-demo.36/)

## 🛠️ Environment and Installation
For using the PDF-to-Text module in Reaction Miner, ensure Maven and Java 1.8 are installed.

To get started, simply run
```
pip install git+https://github.com/maszhongming/ReactionMiner
```

Or install the necessary packages step-by-step:
```
git clone https://github.com/maszhongming/ReactionMiner
cd ReactionMiner
pip install . 
python -m spacy download en_core_web_sm
```

## 📖 How to Use Reaction Miner
Given a PDF file, please refer to [example.py](./example.py) to run our entire system. It can be broken down into the following three steps:

### Step 1: PDF-to-Text Conversion
This step transforms a PDF file into text, saving a json file:

```python
from ReactionMiner.pdf2text.generalParser import parseFile

pdf_path = "copper_acetate.pdf"  # PDF file given by the user
result = parseFile(pdf_path)
full_text = result['fullText']  # Text without paragraph information
paragraphs = result['contents']  # Text with paragraph boundaries
```

The converted text is saved in `pdf2text/results`.

### Step 2: Text Segmentation
Identifies paragraphs about chemical reactions and segments them:

```python
from ReactionMiner.segmentation.segmentor import TopicSegmentor

segmentor = TopicSegmentor()
seg_texts = segmentor.segment(paragraphs)
```

### Step 3: Reaction Extraction
Extracts structured chemical reactions from each segment:

```python
from ReactionMiner.extraction.extractor import ReactionExtractor

extractor = ReactionExtractor('7b')
reactions = extractor.extract(seg_texts)
```

## 🤖 Model Training
We fine-tune Llama-2-7B with LoRA, a technique for efficient fine-tuning, on our collected training set for our reaction extractor.
Explore the training details in [extraction/training](ReactionMiner/extraction/training).

## 📚 Citation
If you find Reaction Miner helpful, please kindly cite our paper:
```
@inproceedings{zhong2023reaction,
  title={Reaction Miner: An Integrated System for Chemical Reaction Extraction from Textual Data},
  author={Zhong, Ming and Ouyang, Siru and Jiao, Yizhu and Kargupta, Priyanka and Luo, Leo and Shen, Yanzhen and Zhou, Bobby and Zhong, Xianrui and Liu, Xuan and Li, Hongxiang and others},
  booktitle={Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing: System Demonstrations},
  pages={389--402},
  year={2023}
}
```
