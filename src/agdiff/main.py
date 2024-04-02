import hashlib
from math import floor
from pathlib import Path

from rich import print
from rich.prompt import Prompt
from rich.markup import escape
import typer


app = typer.Typer()


def _split_lines(lines: list[str], start_index: int = 0):
    if len(lines) == 1:
        print("Line contents:")
        print(lines[0])
        return

    halfway = floor(len(lines) / 2)

    first_half_lines = lines[:halfway]
    first_half_str = "".join(first_half_lines)
    sha1 = hashlib.sha1()
    sha1.update(first_half_str.encode())
    print(f"Lines: {1 + start_index} - {halfway + start_index}")
    print(sha1.hexdigest())
    print("")

    second_half_lines = lines[halfway:]
    second_half_str = "".join(second_half_lines)
    sha1 = hashlib.sha1()
    sha1.update(second_half_str.encode())
    print(f"Lines: {halfway + 1 + start_index} - {len(lines) + start_index}")
    print(sha1.hexdigest())
    print("")

    print("What action should be taken?")
    print(escape("Split top [t]"))
    print(escape("Split bottom [b]"))
    print(escape("Return to previous chunks [r]"))
    action = Prompt.ask()
    if action == "t":
        _split_lines(first_half_lines, start_index=start_index)
    elif action == "b":
        _split_lines(second_half_lines, start_index=halfway + start_index)
    elif action == "r":
        pass
    else:
        raise ValueError("Invalid choice")


def main(input_path_str: str):
    input_path = Path(input_path_str)
    if input_path.is_file():
        sha1 = hashlib.sha1()
        with input_path.open("r") as fp:
            contents = fp.read()

        sha1.update(contents.encode())
        print(input_path_str)
        print(sha1.hexdigest())
        action = Prompt.ask(escape("What action should be taken? Continue [c], Split file [s]"))
        if action == "c":
            typer.Exit()
        elif action == "s":
            with input_path.open("r") as fp:
                lines = fp.readlines()
            _split_lines(lines)
    else:
        raise ValueError("Unsupported path type")


if __name__ == "__main__":
    typer.run(main)
