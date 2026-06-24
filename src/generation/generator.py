from transformers import AutoTokenizer, AutoModelForCausalLM


class Generator:
    def __init__(
            self,
            model_name: str = "Qwen/Qwen3-0.6B",
            max_context_length: int = 2000) -> None:

        self._model_name = model_name
        self.max_token: int = max_context_length
        self.max_new_token: int = 2000
        self.temperature: float = 0.1
        self.tokenizer = AutoTokenizer.from_pretrained(
            self._model_name,
            trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self._model_name,
            device_map="auto",
            trust_remote_code=True
        )
