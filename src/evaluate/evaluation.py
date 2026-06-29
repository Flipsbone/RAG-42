from src.model.model_retrivial import (
    StudentSearchResults,
    RagDataset,
)
from src.exceptions import EvaluatError
from src.model.model_generation import EvalSource


class Evaluator:
    def __init__(self,
                 my_answers: StudentSearchResults,
                 real_answers: RagDataset,
                 k: int,
                 max_context_length: int) -> None:

        self.my_answers: StudentSearchResults = my_answers
        self.real_answers: RagDataset = real_answers
        self.nb_sources: int = k
        self.max_context: int = max_context_length
        self.my_info_recall: dict[str, list[EvalSource]] = {}
        self.real_info_recall: dict[str, list[EvalSource]] = {}

    def check_size_chunk(self) -> None:
        for search_result in self.my_answers.search_results:
            my_chunks = [
                EvalSource(
                    file_path=my_chunk.file_path,
                    first_index=my_chunk.first_character_index,
                    last_index=my_chunk.last_character_index
                )
                for my_chunk in search_result.retrieved_sources
            ]
            self.my_info_recall[search_result.question_id] = my_chunks
            if any(
                (chunk.last_index - chunk.first_index + 1) >
                    self.max_context for chunk in my_chunks):
                raise EvaluatError("Student data is invalid")
        print(f"Student data is valid: {True}")

    def check_questions(self) -> int:
        total_questions = len(self.real_answers.rag_questions)

        total_sourced_questions: int = 0
        for real_question in self.real_answers.rag_questions:
            if hasattr(real_question, 'sources') and real_question.sources:
                total_sourced_questions += 1
                self.real_info_recall[real_question.question_id] = [
                    EvalSource(
                        file_path=real_source.file_path,
                        first_index=real_source.first_character_index,
                        last_index=real_source.last_character_index
                    )
                    for real_source in real_question.sources
                ]

        total_my_sourced_questions = 0
        for my_search_result in self.my_answers.search_results:
            if my_search_result.retrieved_sources:
                total_my_sourced_questions += 1

        print(f"Total number of questions: {total_questions}")
        print(
            "Total number of questions with "
            f"sources: {total_sourced_questions}")
        print(
            "Total number of questions with "
            f"student sources: {total_my_sourced_questions}\n")
        return (total_questions)

    def _overlap_calculator(
            self,
            my_source: EvalSource,
            real_source: EvalSource) -> bool:

        if my_source.file_path != real_source.file_path:
            return False

        common_start: int = max(my_source.first_index, real_source.first_index)
        common_end: int = min(my_source.last_index, real_source.last_index)
        union: int = common_end - common_start + 1
        total_lenght: int = (
            real_source.last_index - real_source.first_index + 1)
        score: float = (union / total_lenght) * 100

        return score >= 5

    @staticmethod
    def print_scores(scores_k: dict[int, float], total_questions: int) -> None:
        print("Evaluation Results")
        print("========================================")
        print(f"Questions evaluated:{total_questions}")
        if 1 in scores_k:
            print(f"Recall@1: {scores_k[1] / total_questions:.3f}")
        if 3 in scores_k:
            print(f"Recall@3: {scores_k[3] / total_questions:.3f}")
        if 5 in scores_k:
            print(f"Recall@5: {scores_k[5] / total_questions:.3f}")
        if 10 in scores_k:
            print(f"Recall@10: {scores_k[10] / total_questions:.3f}")

    def check_recall(self, total_questions: int) -> None:
        k_targets = [1, 3, 5, 10]
        scores_k = {k: 0.0 for k in k_targets if k <= self.nb_sources}
        if total_questions == 0:
            print("No questions to evaluate.")
            return

        for question_id, real_sources in self.real_info_recall.items():
            my_total_sources = self.my_info_recall.get(question_id, [])
            for k in scores_k.keys():
                my_sources_k = my_total_sources[:k]
                source_found = 0

                for awaited_source in real_sources:
                    match = any(
                        self._overlap_calculator(my_source, awaited_source)
                        for my_source in my_sources_k
                    )

                    if match:
                        source_found += 1

                scores_k[k] += (source_found / len(real_sources))
        self.print_scores(scores_k, total_questions)

    def evaluate(self) -> None:
        self.check_size_chunk()
        total_questions: int = self.check_questions()
        self.check_recall(total_questions)
