import sys
import torch
from tqdm import tqdm
from peft import PeftModel
from transformers import GenerationConfig, LlamaForCausalLM, LlamaTokenizer, AutoTokenizer

class ReactionExtractor:
    """
    A class for extracting chemical reactions from text using a pre-trained language model.

    Args:
        model_size (str): The size of the language model (e.g., '8b').
        base_model (str, optional): The base model to use. Defaults to "meta-llama/Meta-Llama-3.1-8B".
        load_8bit (bool, optional): Whether to load the model in 8-bit mode. Defaults to False.
        cache_dir (str, optional): Directory for caching model files. Defaults to None.

    Attributes:
        device (str): The device to run the model on ('cuda', 'cpu', or 'mps').
        tokenizer (LlamaTokenizer): Tokenizer for processing text.
        model (PeftModel): Pre-trained language model for reaction extraction.
        excluded_phrases (list): List of phrases to exclude when parsing reactions.

    Methods:
        get_structured_reactions(reaction_string): Parses reactions into structured dictionaries.
        extract(texts, temperature, top_p, top_k, do_sample, max_new_tokens, **kwargs): 
            Extracts reactions from a list of input texts.

    Example:
        extractor = ReactionExtractor(model_size='7b')
        reactions = extractor.extract(['Sample text containing chemical reactions.'])
    """
    def __init__(
        self,
        model_size,
        base_model="meta-llama/Meta-Llama-3.1-8B",
        load_8bit=False,
        cache_dir=None
    ):
        """ 
        Set up model
        """
        if torch.cuda.is_available():
            print('GPU detected, using GPU')
            self.device = "cuda:0"
        elif torch.backends.mps.is_available():
            print('MPS is available, it has been enabled')
            self.device = "mps"
        else:
            print('No GPU detected, falling back to CPU-only')
            self.device = "cpu"

        # Currently only 8b model size is supported
        assert model_size in ['8b']
        lora_path = f'TingfengLuo/reaction-miner-8b-lora'

        # self.tokenizer = LlamaTokenizer.from_pretrained(base_model)
        print('Running TingfengLuo/reaction-miner-8b-lora...')
        self.tokenizer = AutoTokenizer.from_pretrained(base_model, token=True)

        if self.device == "cuda":
            print('Executing on GPU...')
            self.model = LlamaForCausalLM.from_pretrained(
                base_model,
                load_in_8bit=load_8bit,
                torch_dtype=torch.float16,
                # device_map="auto",
                low_cpu_mem_usage=True,
                device_map={"": self.device},
            )
            self.model = PeftModel.from_pretrained(
                self.model,
                lora_path,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
            )
        elif self.device == "mps":
            print('Executing on MPS...')
            self.model = LlamaForCausalLM.from_pretrained(
                base_model,
                device_map={"": self.device},
                low_cpu_mem_usage=True,
                torch_dtype=torch.float16,
            )
            self.model = PeftModel.from_pretrained(
                self.model,
                lora_path,
                device_map={"": self.device},
                low_cpu_mem_usage=True,
                torch_dtype=torch.float16,
            )
        else:
            print('Executing on CPU...')
            self.model = LlamaForCausalLM.from_pretrained(
                base_model,
                device_map={"": self.device},
                low_cpu_mem_usage=True
            )
            self.model = PeftModel.from_pretrained(
                self.model,
                lora_path,
                device_map={"": self.device},
                low_cpu_mem_usage=True,
            )
        # TODO this is important parameter - check how it influences on output
        if not load_8bit:
            print('model half')  # By default use half
            self.model.half()
        
        self.model.eval()
        if torch.__version__ >= "2" and sys.platform != "win32":
            print('Compiling...')
            self.model = torch.compile(self.model)

        self.excluded_phrases = ["not specified", "not mentioned", "not available", "none"]
        print('Initialization of model completed.')

    def get_structured_reactions(self, reaction_string):
        """
        Parses raw reaction strings into structured dictionaries.

        Args:
            reaction_string (str): Raw reaction input_string to be parsed.

        Returns:
            list: List of dictionaries representing structured reactions.
        """
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
            # Condition to add recognized data as reaction, might be adjustable
            if len(reaction_dict) > 1 and 'Product' in reaction_dict:
                reactions_dicts.append(reaction_dict)
        return reactions_dicts

    def extract(
        self,
        texts,
        default_prompt ='You are a helpful assistant in extracting all the chemical reactions from the text provided by the user.',
        temperature=0.1,
        top_p=0.75,
        top_k=40,
        # num_beams=4,
        do_sample=True,
        max_new_tokens=1024,
        **kwargs
    ):
        """
        Extracts chemical reactions from a list of input texts.

        Args:
            texts (list or str): List of input texts or a single input text.
            default_prompt (str): Prompt for model
            temperature (float, optional): Sampling temperature for generation. Defaults to 0.1.
            top_p (float, optional): Top-p nucleus sampling probability. Defaults to 0.75.
            top_k (int, optional): Top-k sampling parameter. Defaults to 40.
            do_sample (bool, optional): Whether to use sampling during generation. Defaults to True.
            max_new_tokens (int, optional): Maximum number of new tokens to generate. Defaults to 1024.
            **kwargs: Additional generation configuration options.

        Returns:
            list: List of dictionaries containing input texts and corresponding extracted reactions.
        """
        system_prompt = f"<|system|>\n{default_prompt}\n\n"
        
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

