from typing import Any, cast

from transformers import AutoTokenizer, AutoModelForCausalLM
from src.model.model_retrivial import (
    ChunkSource)
import torch


class Generator:
    def __init__(
            self,
            model_name: str = "Qwen/Qwen3-0.6B",
            max_context_length: int = 2000) -> None:

        self._model_name = model_name
        self.max_token: int = max_context_length
        self.max_new_token: int = 64
        self.temperature: float = 0.1
        self.tokenizer = AutoTokenizer.from_pretrained(
            self._model_name,
            trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            self._model_name,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True
        )
        self.model = cast(Any, model)
        self.model.eval()

    def _stitch_context(self, chunks_source: list[ChunkSource]) -> str:
        context_parts = []

        for source in chunks_source:
            header = f"--- Snippet from {source.file_path} ---"
            context_parts.append(f"{header}{source.text}\n")

        full_context = "\n".join(context_parts)

        tokens = self.tokenizer.encode(full_context)
        if len(tokens) > self.max_token:
            full_context = (
                self.tokenizer.decode(tokens[:self.max_token]))  # type: ignore
        return full_context

    def _build_prompt(self, query: str, context: str) -> str:
        system_instruction = (
            "You are an expert technical assistant."
            "Your task is to answer the user's question "
            "based STRICTLY on the provided context."
            "If the context does not contain the answer, "
            "you must reply exactly with 'Information not found in context'."
            "Do not hallucinate or use external knowledge."
        )
        prompt = (
            f"<|im_start|>system\n{system_instruction}<|im_end|>\n"
            f"<|im_start|>user\nContext:\n{context}\n\nQuestion: "
            f"{query}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        return prompt

    def _parse_response(self, raw_output: str) -> str:
        delimiter = "<|im_start|>assistant\n"
        if delimiter in raw_output:
            answer = raw_output.split(delimiter)[-1]
        else:
            answer = raw_output
        answer = answer.replace("<|im_end|>", "").strip()

        return answer

    def generate_answer(
            self,
            query: str,
            chunks_source: list[ChunkSource]) -> str:

        if not chunks_source:
            return "Information not found in context"

        try:
            context = self._stitch_context(chunks_source)
            prompt = self._build_prompt(query, context)

            inputs = (
                self.tokenizer(
                    prompt, return_tensors="pt").to(self.model.device))
            with torch.inference_mode():
                model = cast(Any, self.model)
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_token,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            generated_tokens = outputs[0][inputs.input_ids.shape[1]:]
            decoded_answer = self.tokenizer.decode(
                generated_tokens, skip_special_tokens=True)
            raw_answer: str
            if isinstance(decoded_answer, str):
                raw_answer = decoded_answer
            else:
                raw_answer = decoded_answer[0]
            return self._parse_response(raw_answer)
        except Exception:
            return "Information not found in context"
