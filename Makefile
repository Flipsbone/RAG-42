PYTHON = uv run python3
MAIN = -m src
SRC = src/
ARGS = index --max_chunk_size=2000 --target_dir=test-file

all: install

uv.lock: pyproject.toml Makefile
	@echo "Installing dependencies using uv..."
	uv sync
	@touch uv.lock

install: uv.lock
	uv sync

run: install
	@echo "Running the program with args: $(ARGS)..."
	$(PYTHON) $(MAIN) $(ARGS)
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