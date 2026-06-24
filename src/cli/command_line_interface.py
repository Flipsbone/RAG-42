from pathlib import Path
from tqdm import tqdm
from src.indexing.indexation import Indexation
from src.retrieval.retriever import Retriever
from src.model.model_retrivial import (
    UnansweredQuestion,
    RagDataset,
    StudentSearchResults)
from src.model.model_generation import (
    MinimalAnswer,
    StudentSearchResultsAndAnswer
)
from src.exeptions import RetrieverError, GeneraterError


class RagCLI:
    """A Command Line Interface for managing the RAG document index."""
    def index(
            self, target_dir: str = "data/raw/vllm-0.10.1",
            max_chunk_size: int = 2000) -> None:
        """
        Indexes documents found in the target directory.

        Args:
            target_dir: The folder path containing the raw documents.
            max_chunk_size: The maximum character limit for each text chunk.
        """
        if max_chunk_size > 2000:
            raise ValueError(
                f"max_chunk_size : {max_chunk_size} must be < 2000")
        if max_chunk_size < 1000:
            raise ValueError(
                f"max_chunk_size : {max_chunk_size} must be > 1000"
                "in order to have a good semantic")
        path = Path(target_dir)
        indexer = Indexation(path, (max_chunk_size - 1))
        indexer.processed_chunks()

    def search(self, query: str = "", k: int = 5) -> None:
        """
        Search the database to retrieve the most useful snippets.
        With exactly one query.

        Args:
            query: What you want to know.
            k: The maximum result of relevant snippets to retrieve.
        """
        retriever = Retriever()
        retriever.load_index()
        unanswered_query: UnansweredQuestion = UnansweredQuestion(
            question=query,
        )
        search_results = retriever.bulk_search([unanswered_query], k)
        print(search_results.model_dump_json(indent=4))

    def search_dataset(
            self, dataset_path: str = (
                "data/datasets/UnansweredQuestions/my_dataset_public.json"),
            save_directory: str = "data/output/search_results",
            k: int = 5) -> None:
        """
        Process multiple questions from a JSON
        dataset and save the search results.

        Args:
            dataset_path: Path to the input
            JSON dataset (e.g., UnansweredQuestions).
            save_directory: Directory where the output JSON will be saved.
            k: The maximum number of results to retrieve per question.
        """
        retriever = Retriever()
        retriever.load_index()
        dataset_file: Path = Path(dataset_path)
        try:
            with open(dataset_file, "r") as file:
                raw_data: str = file.read()
                dataset_obj: RagDataset = (
                    RagDataset.model_validate_json(raw_data))
        except OSError as e:
            raise RetrieverError(
                f"Dataset at {dataset_path} could not be read."
                "have you lunch index ?") from e

        save_file: Path = Path(save_directory)
        save_file.mkdir(parents=True, exist_ok=True)
        queries: list[UnansweredQuestion] = []

        for _, unanswered_questions in (
                tqdm(dataset_obj, desc="Parsing dataset queries")):
            for unanswered_question in unanswered_questions:
                queries.append(unanswered_question)

        search_results = retriever.bulk_search(queries, k)

        print(f"Executing bulk search for {len(queries)} queries...")
        file_name: str = dataset_file.name
        output_path = save_file / file_name
        with open(output_path, "w") as out_file:
            out_file.write(search_results.model_dump_json(indent=4))
        retriever._save_hash_file(output_path)
        print(f"Dataset search complete. Results saved to {output_path}")

    def answer(self, query: str, k: int = 5) -> None:
        """
        Answer a single question using the indexed knowledge base.

        Args:
            query: The question to answer.
            k: The maximum number of relevant snippets to retrieve.
        """
        retriever = Retriever()
        retriever.load_index()
        unanswered_query = UnansweredQuestion(question=query)
        search_results = retriever.bulk_search([unanswered_query], k)

        mini_search_result = search_results.search_results[0]

        # 2. Generate the answer (Placeholder LLM logic)
        # generator = Generator()
        # answer_text = generator.generate_answer(
        #     question=minimal_search_result.question, 
        #     sources=minimal_search_result.retrieved_sources
        # )

        answer_text = "Placeholder answer until the Generator is implemented."

        minimal_answer = MinimalAnswer(
            question_id=mini_search_result.question_id,
            question_str=mini_search_result.question_str,
            retrieved_sources=mini_search_result.retrieved_sources,
            answer=answer_text
        )

        print(minimal_answer.model_dump_json(indent=4))

    def answer_dataset(
            self,
            student_answer_path: str = (
                "data/output/search_results/my_dataset_public.json"),
            save_directory: str = (
                "data/output/search_results_and_answer")) -> None:
        """
        Process answer from a JSON
        search results and save the search results and answer.

        Args:
            student_answer_path: Path to the input
            JSON output (e.g., search_results).
            save_directory: Directory where the output JSON will be saved.
        """
        answer_file: Path = Path(student_answer_path)
        try:
            with open(answer_file, "r") as file:
                raw_data_answer: str = file.read()
                answer_obj: StudentSearchResults = (
                    StudentSearchResults.model_validate_json(raw_data_answer))
        except OSError as e:
            raise GeneraterError(
                f"Dataset at {student_answer_path} could not be read. "
                "Did you launch search_dataset?") from e

        answered_results: list[MinimalAnswer] = []

        print(f"Loaded {len(answer_obj.search_results)} "
              f"questions from {answer_file.name}")

        for search_result in tqdm(
                answer_obj.search_results, desc="Generating Answers"):

            # Generate the answer (Placeholder fo LLM logic)
            # answer_text = generator.generate_answer(
            #     question=search_result.question_str,
            #     sources=search_result.retrieved_sources
            # )

            answer_text = "Placeholder answer until the Generator is implemented."

            answered_results.append(
                MinimalAnswer(
                    question_id=search_result.question_id,
                    question_str=search_result.question_str,
                    retrieved_sources=search_result.retrieved_sources,
                    answer=answer_text
                )
            )

        final_output = StudentSearchResultsAndAnswer(
            search_results=answered_results,
            k=answer_obj.k
        )

        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)
        output_file = save_path / answer_file.name

        with open(output_file, "w") as out_file:
            out_file.write(final_output.model_dump_json(indent=4))

        print(f"Processed {len(answered_results)} of "
              f"{len(answer_obj.search_results)} questions")
        print(f"Saved student_search_results_and_answer to {output_file}")

    # def evaluate(
    #         self,
    #         student_answer_path: str,
    #         dataset_path: str,
    #         k: int = 10,
    #         max_context_length: int = 2000) -> None:

    #     answer_file: Path = Path(student_answer_path)
    #     try:
    #         with open(answer_file, "r") as file:
    #             raw_data_answer: str = file.read()
    #             answer_obj: RagDataset = (
    #                 RagDataset.model_validate_json(raw_data_answer))
    #     except OSError as e:
    #         raise RetrieverError(
    #             f"Dataset at {student_answer_path} could not be read.") from e

    #     dataset_file: Path = Path(dataset_path)
    #     try:
    #         with open(dataset_file, "r") as file:
    #             raw_data: str = file.read()
    #             dataset_obj: RagDataset = (
    #                 RagDataset.model_validate_json(raw_data))
    #     except OSError as e:
    #         raise RetrieverError(
    #             f"Dataset at {dataset_path} could not be read.") from e

    #     print("Student data is valid: True")
