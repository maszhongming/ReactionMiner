export CUDA_VISIBLE_DEVICES=6,7

WORLD_SIZE=2  torchrun --nproc_per_node=2 --master_port=5946 finetune.py \
    --base_model "meta-llama/Meta-Llama-3.1-8B" \
    --num_epochs 10 \
    --cutoff_len 2048 \
    --data_path "train_processed.jsonl" \
    --output_dir "extractor-8b" \
    --lora_target_modules "[q_proj,k_proj,v_proj,o_proj,up_proj,down_proj,gate_proj,embed_tokens,lm_head]" \
    --lora_r 16 \
    --micro_batch_size 16 \
    --batch_size 64 \
    --learning_rate 3e-4 \
    --val_set_size 0 \
    --use_chat_prompt \
    --train_on_inputs False \