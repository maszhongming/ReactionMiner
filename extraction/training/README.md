# Model Training for Reaction Extractor

### Local Setup

Install dependencies

```bash
pip install -r requirements.txt
```

### Data Preparation
Please download the data from [this link](https://drive.google.com/file/d/1uCwMJ3Ico6xyifa5UQj5tHYSTKN7c6ZA/view?usp=sharing) and unzip it to the current folder.

### Training (`finetune.py`)

We train Llama-2 and LoRA based models for the reaction extractor with the following usage:

```bash
export CUDA_VISIBLE_DEVICES=0,1
# export TRANSFORMERS_CACHE=/path/to/cache

WORLD_SIZE=2  torchrun --nproc_per_node=2 --master_port=12345 finetune.py \
    --base_model "meta-llama/Llama-2-7b-hf" \
    --num_epochs 10 \
    --cutoff_len 2048 \
    --data_path "chem_data/train_processed.jsonl" \
    --output_dir "extractor-7b" \
    --lora_target_modules "[q_proj,k_proj,v_proj,o_proj,up_proj,down_proj,gate_proj,embed_tokens,lm_head]" \
    --lora_r 16 \
    --micro_batch_size 16 \
    --batch_size 64 \
    --learning_rate 3e-4 \
    --val_set_size 0 \
    --use_chat_prompt \
    --train_on_inputs False \
```
