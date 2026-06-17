import fire
import sys
from src.cli.command_line_interface import RagCLI


def main() -> int:
    try:
        fire.Fire(RagCLI)
    except PermissionError as e:
        print(f"Permission Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: File '{e}' not found.", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    main()
