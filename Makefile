PYTHON = uv run python3
MAIN = -m src
SRC = src/
INDEX = index --max_chunk_size=2000 --target_dir=data/raw/vllm-0.10.1
SEARCH = search --query="What are the default values for FP8_MIN and FP8_MAX constants in vLLM's triton_flash_attention module?" --k=1
SEARCH_DDOC = search_dataset --dataset_path datasets_public/public/UnansweredQuestions/dataset_docs_public.json --save_directory data/output/search_results --k=5
SEARCH_DCODE = search_dataset --dataset_path datasets_public/public/UnansweredQuestions/dataset_code_public.json --save_directory data/output/search_results --k=5
EVALUATE_DOC = evaluate --student_search_results_path data/output/search_results/dataset_docs_public.json --dataset_path datasets_public/public/AnsweredQuestions/dataset_docs_public.json --k=5 --max_context_length=2000
EVALUATE_CODE = evaluate --student_search_results_path data/output/search_results/dataset_code_public.json --dataset_path datasets_public/public/AnsweredQuestions/dataset_code_public.json --k=5 --max_context_length=2000
ANSWER = answer --query="How to configure OpenAI server" --k=1
ANSWER_DATASET_DOC = answer_dataset --student_search_results_path data/output/search_results/dataset_docs_public.json --save_directory data/output/search_results_and_answer
ANSWER_DATASET_CODE = answer_dataset --student_search_results_path data/output/search_results/dataset_code_public.json --save_directory data/output/search_results_and_answer
EVAL_SCRIPT := ./moulinette_pkg/moulinette-ubuntu 
# RESULTS := data/output/search_results/dataset_docs_public.json
# DATASET := datasets_public/public/AnsweredQuestions/dataset_docs_public.json
RESULTS := data/output/search_results/dataset_code_public.json
DATASET := datasets_public/public/AnsweredQuestions/dataset_code_public.json
K := 5
CYAN  := \033[36m
GREEN := \033[32m
RESET := \033[0m

all: install

uv.lock: pyproject.toml Makefile
	@echo "Installing dependencies using uv..."
	uv sync
	@touch uv.lock

install: uv.lock
	uv sync

run: install
	@echo "$(CYAN)=========================================="
	@echo "🚀 Starting full RAG pipeline"
	@echo "==========================================$(RESET)"
	
	@echo "$(GREEN)>>> Step 1: Indexing$(RESET)"
	$(MAKE) --no-print-directory index
	
	@echo "$(GREEN)>>> Step 2: Searching Dataset$(RESET)"
	$(MAKE) --no-print-directory search_dataset
	
	@echo "$(GREEN)>>> Step 3: Answering Dataset$(RESET)"
	$(MAKE) --no-print-directory answer_dataset
	
	@echo "$(CYAN)=========================================="
	@echo "✨ Pipeline finished successfully!"
	@echo "==========================================$(RESET)"

index: install
	@echo "Running the program with args: $(INDEX)..."
	$(PYTHON) $(MAIN) $(INDEX)

search: install
	@echo "Running the program with function search..."
	$(PYTHON) $(MAIN) $(SEARCH)

search_dataset: install
	@echo "Running the program with function search..."
	$(PYTHON) $(MAIN) $(SEARCH_DCODE)

evaluate: install
	@echo "Running the program with moulinette..."
	$(PYTHON) $(MAIN) $(EVALUATE_DOC)

answer: install
	@echo "Running the program with answer..."
	$(PYTHON) $(MAIN) $(ANSWER)

answer_dataset: install
	@echo "Running the program with answer..."
	$(PYTHON) $(MAIN) $(ANSWER_DATASET_DOC)

moulinette: install
	@echo "Running the program with moulinette..."
	$(EVAL_SCRIPT) list_valid_questions \
		$(RESULTS) \
		$(DATASET) \
		--k $(K) \

debug: install
	@echo "Starting debug mode..."
	$(PYTHON) -m pdb $(MAIN)

lint:
	@echo "Running standard linting..."
	uv run flake8 $(SRC)
	uv run mypy $(SRC) --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@echo "Running strict linting..."
	uv run flake8 $(SRC)
	uv run mypy --strict $(SRC)

test:
	uv run python -m pytest test_pytest/ -v

clean:
	@echo "Cleaning up..."
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf data/processed
	rm -rf data/output

.PHONY: all install run index search search_dataset answer answer_dataset evaluate moulinette debug lint lint-strict test clean