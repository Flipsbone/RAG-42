PYTHON = uv run python3
MAIN = -m src
SRC = src/
INDEX = index --max_chunk_size=2000 --target_dir=test-file
SEARCH = uv run python3 -m src search --query=What's the default value of trust_remote_code in vLLM's LLM class constructor? --k=1

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
	@echo "Running the program with args: $(SEARCH)..."
	$(PYTHON) $(MAIN) $(SEARCH)

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
	rm -rf data

.PHONY: all install run debug lint lint-strict clean profile