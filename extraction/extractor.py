import sys
import torch
from tqdm import tqdm
import transformers
from peft import PeftModel
from transformers import GenerationConfig, LlamaForCausalLM, LlamaTokenizer

class ReactionExtractor:
    def __init__(
        self,
        model_size,
        base_model="meta-llama/Llama-2-7b-hf",
        load_8bit=False,
        cache_dir=None
    ):
        """ Set up model """
        if torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        
        try:
            if torch.backends.mps.is_available():
                self.device = "mps"
        except:
            pass

        # Currently only 7b model size is supported
        assert model_size in ['7b']
        lora_path = f"MingZhong/reaction-miner-{model_size}-lora"

        self.tokenizer = LlamaTokenizer.from_pretrained(base_model)
        if self.device == "cuda":
            self.model = LlamaForCausalLM.from_pretrained(
                base_model,
                load_in_8bit=load_8bit,
                torch_dtype=torch.float16,
                device_map="auto",
            )
            self.model = PeftModel.from_pretrained(
                self.model,
                lora_path,
                torch_dtype=torch.float16,
            )
        elif self.device == "mps":
            self.model = LlamaForCausalLM.from_pretrained(
                base_model,
                device_map={"": self.device},
                torch_dtype=torch.float16,
            )
            self.model = PeftModel.from_pretrained(
                self.model,
                lora_path,
                device_map={"": self.device},
                torch_dtype=torch.float16,
            )
        else:
            self.model = LlamaForCausalLM.from_pretrained(
                base_model, device_map={"": self.device}, low_cpu_mem_usage=True
            )
            self.model = PeftModel.from_pretrained(
                self.model,
                lora_path,
                device_map={"": self.device},
            )
        
        if not load_8bit:
            self.model.half()
        
        self.model.eval()
        if torch.__version__ >= "2" and sys.platform != "win32":
            self.model = torch.compile(self.model)

        self.excluded_phrases = ["not specified", "not mentioned", "not available", "none"]

    def get_structured_reactions(self, reaction_string):
        # Parsing each output into a dictionary and filtering out excluded_phrases
        reactions_list = reaction_string.strip().split("\n\n")

        reactions_dicts = []
        for reaction in reactions_list:
            reaction_lines = reaction.split("\n")
            reaction_dict = {}
            for line in reaction_lines:
                if ':' in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if not any(phrase in value.lower() for phrase in self.excluded_phrases):
                        reaction_dict[key] = value
            if len(reaction_dict) > 1 and 'Product' in reaction_dict:
                reactions_dicts.append(reaction_dict)
        return reactions_dicts

    def extract(
        self,
        texts,
        temperature=0.1,
        top_p=0.75,
        top_k=40,
        # num_beams=4,
        do_sample=True,
        max_new_tokens=1024,
        **kwargs
    ):
        system_prompt = "<|system|>\nYou are a helpful assistant in extracting all the chemical reactions from the text provided by the user.\n\n"
        
        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            # num_beams=num_beams,
            do_sample=do_sample,
            **kwargs,
        )

        if isinstance(texts, str):
            texts = [texts]
        
        outputs = []
        for input in tqdm(texts):
            prompt = system_prompt + "<|user|>\n" + input.strip() + "\n\n<|assistant|>\n"
            
            inputs = self.tokenizer(prompt, return_tensors="pt")
            input_ids = inputs["input_ids"].to(self.device)

            with torch.no_grad():
                generation_output = self.model.generate(
                    input_ids=input_ids,
                    generation_config=generation_config,
                    return_dict_in_generate=True,
                    output_scores=True,
                    max_new_tokens=max_new_tokens,
                )
            s = generation_output.sequences[0]
            output = self.tokenizer.decode(s, skip_special_tokens=True)
            output = output.split('<|assistant|>\n')[-1].strip()
            if 'no complete' not in output.lower():
                cur_result = {}
                cur_result['text'] = input.strip()
                cur_result['reactions'] = self.get_structured_reactions(output)
                if len(cur_result['reactions']) > 0:
                    outputs.append(cur_result)
        return outputs

