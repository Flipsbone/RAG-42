PYTHON = uv run python3
MAIN = -m src
SRC = src/
INDEX = index --max_chunk_size=2000 --target_dir=data/raw/vllm-0.10.1
SEARCH = search --query="What are the default values for FP8_MIN and FP8_MAX constants in vLLM's triton_flash_attention module?" --k=2
SEARCH_D = search_dataset --dataset_path datasets_public/public/UnansweredQuestions/dataset_docs_public.json --save_directory data/output/search_results --k=1
# SEARCH_D = search_dataset --dataset_path datasets_public/public/UnansweredQuestions/dataset_code_public.json --save_directory data/output/search_results --k=1
EVALUATE = evaluate --student_answer_path data/output/search_results/dataset_docs_public.json --dataset_path data/datasets/AnsweredQuestions/dataset_docs_public.json --k=1 --max_context_length=2000
EVAL_SCRIPT := ./moulinette_pkg/moulinette-ubuntu 
RESULTS := data/output/search_results/dataset_docs_public.json
DATASET := datasets_public/public/AnsweredQuestions/dataset_docs_public.json
# RESULTS := data/output/search_results/dataset_code_public.json
# DATASET := datasets_public/public/AnsweredQuestions/dataset_code_public.json
K := 1
THRESHOLD := 0.80

all: install

uv.lock: pyproject.toml Makefile
	@echo "Installing dependencies using uv..."
	uv sync
	@touch uv.lock

install: uv.lock
	uv sync

run: install
	@echo "Running the program with args: $(INDEX)..."
	$(PYTHON) $(MAIN) $(INDEX)

search: install
	@echo "Running the program with function search..."
	$(PYTHON) $(MAIN) $(SEARCH)

search_dataset: install
	@echo "Running the program with function search..."
	$(PYTHON) $(MAIN) $(SEARCH_D)

evaluate: install
	@echo "Running the program with moulinette..."
	$(PYTHON) -m moulinette $(EVALUATE)

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
	uv run python -m pytest tests/ -v

clean:
	@echo "Cleaning up..."
	rm -rf .mypy_cache \
	       .pytest_cache \

	find . -type d -name "__pycache__" -exec rm -rf {} +

.PHONY: all install run search search_dataset evaluate debug lint lint-strict test clean