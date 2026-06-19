from pathlib import Path
from tqdm import tqdm
from src.indexing.indexation import Indexation
from src.retrieval.retriever import Retriever
from src.model.model_retrivial import UnansweredQuestion, RagDataset
from src.exeptions import DatasetError

class RagCLI:
    """A Command Line Interface for managing the RAG document index."""
    def index(
            self, target_dir: str = "vllm-0.10.1",
            max_chunk_size: int = 2000) -> None:
        """
        Indexes documents found in the target directory.

        Args:
            target_dir: The folder path containing the raw documents.
            max_chunk_size: The maximum character limit for each text chunk.
        """
        path = Path(target_dir)
        indexer = Indexation(path, max_chunk_size)
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
    
    def search_dataset(self, dataset_path: str, save_directory: str, k: int = 10) -> None:
        """
        Process multiple questions from a JSON dataset and save the search results.

        Args:
            dataset_path: Path to the input JSON dataset (e.g., UnansweredQuestions).
            save_directory: Directory where the output JSON will be saved.
            k: The maximum number of results to retrieve per question.
        """
        retriever = Retriever()
        retriever.load_index()
        dataset_file: Path = Path(dataset_path)
        try:
            with open(dataset_file, "r") as file:
                raw_data: str = file.read()
                dataset_obj: RagDataset = RagDataset.model_validate_json(raw_data)
        except OSError as e:
            raise DatasetError(f"Dataset at {dataset_path} could not be read.") from e
        save_file: Path = Path(save_directory)
        save_file.mkdir(parents=True, exist_ok=True)
        
        queries: list[UnansweredQuestion] = []
        for _, unanswered_questions in tqdm(dataset_obj, desc="Parsing dataset queries"):
            for unanswered_question in unanswered_questions:
                queries.append(unanswered_question)
        search_results = retriever.bulk_search(queries, k)
        print(f"Executing bulk search for {len(queries)} queries...")
        search_results = retriever.bulk_search(queries, k)
        output_path = save_file / "dataset_docs_public.json"
        with open(output_path, "w") as out_file:
            out_file.write(search_results.model_dump_json(indent=4))
        print(f"Dataset search complete. Results saved to {output_path}")


    def evaluate(self, student_answer_path: str, dataset_path: str, k: int = 10, max_context_length: int = 2000) -> None:
        
        answer_file: Path = Path(student_answer_path)
        try:
            with open(answer_file, "r") as file:
                raw_data_answer: str = file.read()
                answer_obj: RagDataset = RagDataset.model_validate_json(raw_data_answer)
        except OSError as e:
            raise DatasetError(f"Dataset at {student_answer_path} could not be read.") from e
    
        dataset_file: Path = Path(dataset_path)
        try:
            with open(dataset_file, "r") as file:
                raw_data: str = file.read()
                dataset_obj: RagDataset = RagDataset.model_validate_json(raw_data)
        except OSError as e:
            raise DatasetError(f"Dataset at {dataset_path} could not be read.") from e
        
        print("Student data is valid: True")