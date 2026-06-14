import pytest
from src.indexing.chunking import PythonChunker
print("L'import fonctionne parfaitement !")


@pytest.fixture
def chunker():
    """Provides a fresh instance of the chunker for each test."""
    return PythonChunker()


def test_standard_case(chunker):
    """
    Test a standard file with multiple small functions.
    The chunker should pack them together into a single chunk
    since the total size is under the 2000 limit.
    """
    code = (
        "def quick_math(a, b):\n"
        "    return a + b\n\n"
        "def say_hello(name):\n"
        "    print(f'Hello {name}')\n\n"
        "# Just a trailing comment\n"
    )

    max_size = 2000
    chunks = chunker.chunk(code, "standard_test.py", max_size)

    # Assertions
    assert len(chunks) == 1
    assert chunks[0].text == code
    assert chunks[0].first_character_index == 0
    assert chunks[0].last_character_index == len(code)


def test_superior_to_limit_line_by_line(chunker):
    """
    Test a single function that is > 2000 characters.
    Because it is a single AST node, the chunker must fall back to
    line-by-line splitting to preserve semantic meaning (breaking at newlines).
    """
    # Generate a massive function programmatically (~2500 characters)
    lines = ["def massive_function():\n"]
    # 70 lines of 35 characters = ~2450 characters
    lines.extend(["    # This is a comment to add bulk\n" for _ in range(70)])
    lines.append("    return True\n")

    code = "".join(lines)
    max_size = 2000

    chunks = chunker.chunk(code, "line_by_line_test.py", max_size)

    # Assertions
    assert len(chunks) >= 2

    # Verify strict limit and semantic line breaks
    for chunk in chunks:
        assert len(chunk.text) <= max_size
        # The chunk should end with a newline,
        # proving it didn't cut a word in half
        assert chunk.text.endswith("\n")


def test_much_superior_hard_split(chunker):
    """
    Test a worst-case scenario: A single line of code
    that is 3000 characters long.
    The chunker cannot break on a newline, so it
    must force a hard character cut
    exactly at the max limit to prevent crashing the indexer.
    """
    # Create a string assignment where the line is 3000 'A's
    long_string = "A" * 3000
    code = f"massive_variable = '{long_string}'\n"

    max_size = 2000
    chunks = chunker.chunk(code, "hard_split_test.py", max_size)

    # Assertions
    assert len(chunks) == 2

    # The first chunk should be exactly 2000 characters (forced cut)
    assert len(chunks[0].text) == 2000

    # The second chunk contains the remaining ~1000 characters
    assert len(chunks[1].text) <= max_size

    # Verify the indices line up perfectly so no characters are lost
    assert chunks[0].last_character_index == chunks[1].first_character_index
