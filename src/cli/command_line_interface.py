from pathlib import Path
from tqdm import tqdm
from src.indexing.indexation import Indexation
from src.retrieval.retriever import Retriever
from src.generation.generator import Generator
from src.evaluate.evaluation import Evaluator
from src.model.model_retrivial import (
    UnansweredQuestion,
    RagDataset,
    MinimalSearchResults,
    StudentSearchResults)
from src.model.model_generation import (
    MinimalAnswer,
    StudentSearchResultsAndAnswer
)
from src.exceptions import (
    RetrieverError,
    GeneratorError,
    EvaluatError
)


class RagCLI:
    """A Command Line Interface for managing the RAG document index."""
    def index(
            self, target_dir: str = "data/raw/vllm-0.10.1",
            max_chunk_size: int = 2000) -> None:
        """1: Index documents found in the target directory.

        Args:
            target_dir: The folder path containing the raw documents.
            max_chunk_size: The maximum character limit for each text chunk.

        Returns:
            None.
        """
        if max_chunk_size > 2000:
            raise ValueError(
                f"max_chunk_size : {max_chunk_size} must be < 2000")
        if max_chunk_size < 1000:
            raise ValueError(
                f"max_chunk_size : {max_chunk_size} must be > 1000"
                " in order to have a good semantic")
        path = Path(target_dir)
        indexer = Indexation(path, (max_chunk_size - 1))
        indexer.processed_chunks()

    def search(self, query: str = "", k: int = 10) -> None:
        """
        Search the database to retrieve the most useful snippets.
        With exactly one query.

        Args:
            query: The question to search for.
            k: The maximum number of snippets to retrieve.

        Returns:
            None.
        """
        if query == "":
            print("You must write something")
            return 
        retriever = Retriever()
        retriever.load_index()
        unanswered_query: UnansweredQuestion = UnansweredQuestion(
            question=query,
        )
        search_results = retriever.bulk_search([unanswered_query], k)
        print(search_results.model_dump_json(indent=4))

    def search_dataset(
            self, dataset_path: str = (
                "datasets_public/public/"
                "UnansweredQuestions/dataset_docs_public.json"),
            save_directory: str = "data/output/search_results",
            k: int = 10) -> None:
        """2: Process a question dataset and save the search results.

        Args:
            dataset_path: Path to the input JSON dataset.
            save_directory: Directory where the output JSON will be saved.
            k: The maximum number of results to retrieve per question.

        Returns:
            None.
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
        retriever.save_dataset(
            len(queries), dataset_file,
            save_file, search_results)

    def answer(self, query: str = "", k: int = 10) -> None:
        """Answer a single question using the indexed knowledge base.

        Args:
            query: The question to answer.
            k: The maximum number of relevant snippets to retrieve.

        Returns:
            None.
        """
        if query == "":
            print("You must write something")
            return 
        retriever = Retriever()
        retriever.load_index()

        unanswered_query = UnansweredQuestion(question=query)
        search_results: StudentSearchResults = (
            retriever.bulk_search([unanswered_query], k))
        mini_search_result: MinimalSearchResults = (
            search_results.search_results[0])

        generator = Generator()
        answer_text = generator.generate_answer(
            query,
            mini_search_result.retrieved_sources
        )

        minimal_answer = MinimalAnswer(
            question_id=mini_search_result.question_id,
            question_str=mini_search_result.question_str,
            retrieved_sources=mini_search_result.retrieved_sources,
            answer=answer_text
        )

        print(minimal_answer.model_dump_json(indent=4))

    def answer_dataset(
            self,
            student_search_results_path: str = (
                "data/output/search_results/dataset_docs_public.json"),
            save_directory: str = (
                "data/output/search_results_and_answer")) -> None:
        """3: Generate answers from saved search results and persist them.

        Args:
            student_search_results_path: Path to the input search-results JSON.
            save_directory: Directory where the output JSON will be saved.

        Returns:
            None.
        """
        answer_file: Path = Path(student_search_results_path)
        try:
            with open(answer_file, "r") as file:
                raw_data_answer: str = file.read()
                answer_obj: StudentSearchResults = (
                    StudentSearchResults.model_validate_json(raw_data_answer))
        except OSError as e:
            raise GeneratorError(
                f"Dataset at {student_search_results_path} could not be read. "
                "Did you launch search_dataset?") from e

        answers: list[MinimalAnswer] = []

        print(f"Loaded {len(answer_obj.search_results)} "
              f"questions from {answer_file.name}")
        generator = Generator()
        for search_result in tqdm(
                answer_obj.search_results, desc="Generating Answers"):

            answer_text = generator.generate_answer(
                search_result.question_str,
                search_result.retrieved_sources
            )
            answers.append(
                MinimalAnswer(
                    question_id=search_result.question_id,
                    question_str=search_result.question_str,
                    retrieved_sources=search_result.retrieved_sources,
                    answer=answer_text
                )
            )

        answered_results = StudentSearchResultsAndAnswer(
            search_results=answers,
            k=answer_obj.k
        )

        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)

        generator.save_answer(save_path, answer_file, answered_results)

    def evaluate(
            self,
            student_search_results_path: str = (
                "data/output/search_results/dataset_docs_public.json"
            ),
            dataset_path: str = (
                "datasets_public/public/"
                "AnsweredQuestions/dataset_docs_public.json"),
            k: int = 10,
            max_context_length: int = 2000) -> None:
        """4: Evaluate retrieved snippets against the labeled dataset.

        Args:
            student_search_results_path: Path to the student search-results
                JSON.
            dataset_path: Path to the labeled answered-question dataset.
            k: The maximum number of sources considered for each question.
            max_context_length: The maximum allowed context size.

        Returns:
            None.
        """

        if max_context_length < 500:
            raise ValueError(
                f"max_context_lengthz : {max_context_length} must be > 500"
                "in order to have a proper answer")

        answer_file: Path = Path(student_search_results_path)
        try:
            with open(answer_file, "r") as file:
                raw_data_answer: str = file.read()
                answer_obj: StudentSearchResults = (
                    StudentSearchResults.model_validate_json(raw_data_answer))
        except OSError as e:
            raise EvaluatError(
                f"Dataset at {student_search_results_path} could not be read"
            ) from e

        dataset_file: Path = Path(dataset_path)
        try:
            with open(dataset_file, "r") as file:
                raw_data: str = file.read()
                dataset_obj: RagDataset = (
                    RagDataset.model_validate_json(raw_data))
        except OSError as e:
            raise RetrieverError(
                f"Dataset at {dataset_path} could not be read.") from e

        evaluator = Evaluator(
            my_answers=answer_obj,
            real_answers=dataset_obj,
            k=k,
            max_context_length=max_context_length
        )

        evaluator.check_size_chunk()
        total_questions = evaluator.check_questions()
        evaluator.check_recall(total_questions)
