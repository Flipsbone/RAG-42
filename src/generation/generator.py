import ollama
from pathlib import Path
from src.utils.security import save_hash_file
from src.model.model_indexing import (
    ChunkSource)
from src.exceptions import GeneratorError
from src.model.model_generation import (
    StudentSearchResultsAndAnswer)


class Generator:
    """Generate questions and answers using an Ollama chat model."""

    def __init__(
            self,
            model_name: str = "qwen3:0.6b",
            max_context_length: int = 2000) -> None:
        """Initialize the model client and generation settings.

        Args:
            model_name: The Ollama model to use for generation.
            max_context_length: The maximum context length allowed in prompts.
        """

        self._model_name = model_name
        self.max_char_length: int = max_context_length
        self.temperature: float = 0.1
        self.client: ollama.Client = ollama.Client(
            host='http://127.0.0.1:11434'
        )

    @staticmethod
    def save_answer(
            save_path: Path,
            answer_file: Path,
            answered_results: StudentSearchResultsAndAnswer) -> None:
        """Persist generated answers and save a companion hash file.

        Args:
            save_path: Directory where the answer file should be written.
            answer_file: The source filename used for the output name.
            answered_results: The answers to serialize.

        Returns:
            None.

        Raises:
            GeneratorError: If the answer file cannot be written.
        """

        output_path = save_path / answer_file.name

        try:
            with open(output_path, "w") as output_file:
                output_file.write(answered_results.model_dump_json(indent=4))

            print(f"Processed {len(answered_results.search_results)} of "
                  f"{len(answered_results.search_results)} questions")
            print(f"Saved student_search_results_and_answer to {output_file}")
            save_hash_file(output_path)
        except OSError as e:
            raise GeneratorError(
                f"Dataset at {output_file} could not save.") from e

    def _stitch_context(self, chunks_source: list[ChunkSource]) -> str:
        """Join retrieved chunks into a single prompt context string.

        Args:
            chunks_source: The retrieved chunks to stitch together.

        Returns:
            The formatted prompt context.
        """
        context_parts: list[str] = []
        for source in chunks_source:
            header = f"--- Snippet from {source.file_path} ---"
            context_parts.append(f"{header}\n{source.text}\n")

        full_context = "\n".join(context_parts)
        if len(full_context) > self.max_char_length:
            full_context = full_context[:self.max_char_length:]

        return full_context

    @staticmethod
    def _build_prompt() -> str:
        system_instruction = (
            "Answer the question using ONLY the provided Context. "
            "If the answer is not in the Context,"
            "say 'Information not found in context'."
        )
        return system_instruction

    @staticmethod
    def _build_prompt_question() -> str:
        system_instruction = (
            "Generate 3-5 technical synonyms for the query. "
            "Output ONLY space-separated keywords. "
            "No formatting, lists, or conversational text."
        )
        return system_instruction

    def generate_question(self, query: str) -> str:
        """Expand a query into related technical synonyms.

        Args:
            query: The original user query.

        Returns:
            A space-separated synonym expansion.

        Raises:
            GeneratorError: If the model request fails.
        """
        prompt = self._build_prompt_question()
        messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": query},
            ]
        try:
            response = self.client.chat(
                model=self._model_name,
                messages=messages,
                think=False,
                options={
                    "temperature": self.temperature,
                    "num_threads": 8,
                    },
            )
            answer = str(response["message"]["content"].strip())

            return answer
        except Exception as e:
            raise GeneratorError(f"{e} \nDo ollama serve inside terminal ")

    def generate_answer(
            self,
            query: str,
            chunks_source: list[ChunkSource]) -> str:
        """Generate an answer from the query and retrieved context.

        Args:
            query: The question to answer.
            chunks_source: Retrieved context chunks to ground the answer.

        Returns:
            The generated answer, or a fallback message when no context is
            available.

        Raises:
            GeneratorError: If the model request fails.
        """

        if not chunks_source:
            return "Information not found in context"
        try:
            context = self._stitch_context(chunks_source)
            prompt = self._build_prompt()

            user_content = (
                f"Context:\n{context}\n\n"
                f"Question: {query}"
            )

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content},
            ]

            response = self.client.chat(
                model=self._model_name,
                messages=messages,
                think=False,
                options={
                    "temperature": self.temperature,
                    "num_threads": 4,
                    },
            )
            answer = str(response["message"]["content"].strip())

            return answer
        except Exception as e:
            raise GeneratorError(f"{e} \nDo ollama serve inside terminal ")
