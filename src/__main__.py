import fire
import sys
from src.cli.command_line_interface import RagCLI
import src.exceptions as error


def main() -> int:
    try:
        fire.Fire(RagCLI)
    except error.IndexationError as e:
        for log in e.failed_logs:
            print(
                f"Indexation Error: Ignored {log['file']}: "
                f"{log['error']}", file=sys.stderr)
        sys.exit(1)
    except error.RetrieverError as e:
        print(f"Retriever Error: {e}", file=sys.stderr)
        sys.exit(1)
    except error.GeneratorError as e:
        print(f"Generator Error: {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"Permission Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"File not found Error: File '{e}' not found.", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)
    return 0


if __name__ == '__main__':
    main()
