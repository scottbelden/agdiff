from dataclasses import dataclass
import hashlib
import os
from math import floor
from pathlib import Path
from typing import Literal

from rich import print
from rich.console import Group
from rich.markup import escape
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.tree import Tree
import typer

_PREVIOUS = "PREVIOUS"
_QUIT = "QUIT"

app = typer.Typer()


@dataclass
class _PathAndHash:
    path: str
    is_dir: bool
    count: int = 0
    sha1_hash: str = ""
    can_traverse: bool = True
    traversed: bool = False

    def __rich__(self):
        if self.is_dir:
            icon = "📁"
        else:
            icon = "📄"

        if self.count:
            formatted_count = f"({self.count}) "
        else:
            formatted_count = ""

        style = ""
        if not self.can_traverse:
            style = "strike"
        elif not self.traversed:
            style = "bold"

        return Text(
            f"{formatted_count}{icon} {self.path} ({self.sha1_hash})", style=style
        )


def _traverse_file(input_path: Path):
    with input_path.open("r") as fp:
        lines = fp.readlines()
    _split_file(str(input_path), lines)


def _traverse_directory(input_path: Path):
    folder_hashes: dict[Path, str] = {}
    root_directory = _PathAndHash(str(input_path), is_dir=True, traversed=True)
    tree = Tree(root_directory)
    all_paths = [(input_path, root_directory)]
    # In Python 3.12 we can use input_path.walk() and get rid of `root_path`
    for root, dirs, files in os.walk(input_path, topdown=False):
        root_path = Path(root)
        sha1 = hashlib.sha1()
        for dir in sorted(dirs):
            sha1.update(folder_hashes[root_path / dir].encode())
            if input_path == root_path:
                sub_directory = _PathAndHash(
                    dir,
                    count=len(all_paths),
                    is_dir=True,
                    sha1_hash=folder_hashes[root_path / dir],
                )
                tree.add(sub_directory)
                all_paths.append((root_path / dir, sub_directory))
        for file in sorted(files):
            file_hash = _get_file_hash(root_path / file)
            if file_hash:
                sha1.update(file_hash.encode())
                if input_path == root_path:
                    sub_file = _PathAndHash(
                        file, count=len(all_paths), is_dir=False, sha1_hash=file_hash
                    )
                    tree.add(sub_file)
                    all_paths.append((root_path / file, sub_file))
            else:
                if input_path == root_path:
                    sub_file = _PathAndHash(
                        file,
                        count=len(all_paths),
                        is_dir=False,
                        sha1_hash="Binary",
                        can_traverse=False,
                    )
                    tree.add(sub_file)
                    all_paths.append((root_path / file, sub_file))

        folder_hash = sha1.hexdigest()
        folder_hashes[root_path] = folder_hash
        root_directory.sha1_hash = folder_hash

    while True:
        print(tree)
        print("")
        print("-----")
        end = len(all_paths) - 1
        answer = Prompt.ask(
            escape(
                f"Which file or directory to step into? [1 - {end}] Or press [p] to go up one directory"
            )
        )

        if answer == "p":
            return

        error_message = f"Must choose a value between 1 and {end}"
        try:
            answer_as_int = int(answer)
        except ValueError:
            raise ValueError(error_message)

        if answer_as_int < 1 or answer_as_int > end:
            raise ValueError(error_message)

        if all_paths[answer_as_int][1].can_traverse:
            _traverse(all_paths[answer_as_int][0])
            all_paths[answer_as_int][1].traversed = True


def _traverse(input_path: Path):
    if input_path.is_file():
        _traverse_file(input_path)
    elif input_path.is_dir():
        _traverse_directory(input_path)
    else:
        raise ValueError("Unsupported path type")


def _split_file(
    filename: str, lines: list[str], start_index: int = 0
) -> Literal["PREVIOUS"] | Literal["QUIT"]:
    if len(lines) == 0:
        print("Empty file")
        print("")
        return _QUIT

    if len(lines) == 1:
        print("Line contents:")
        print(Panel(lines[0]))

        print("-----")
        print(escape("Return to previous chunks [p]"))
        print(escape("Exit file [q]"))
        action = Prompt.ask()

        if action == "p":
            return _PREVIOUS
        elif action == "q":
            return _QUIT
        else:
            raise ValueError("Invalid choice")

    halfway = floor(len(lines) / 2)

    first_half_lines = lines[:halfway]
    first_half_str = "".join(first_half_lines)
    sha1 = hashlib.sha1()
    sha1.update(first_half_str.encode())
    top_hash = sha1.hexdigest()

    second_half_lines = lines[halfway:]
    second_half_str = "".join(second_half_lines)
    sha1 = hashlib.sha1()
    sha1.update(second_half_str.encode())
    bottom_hash = sha1.hexdigest()

    traversed_top = False
    traversed_bottom = False
    while True:
        top_style = "bold"
        bottom_style = "bold"
        if traversed_top:
            top_style = "none"
        if traversed_bottom:
            bottom_style = "none"

        group = Group(
            Panel(
                f"Lines: {1 + start_index} - {halfway + start_index}\n" + top_hash,
                style=top_style,
            ),
            Panel(
                f"Lines: {halfway + 1 + start_index} - {len(lines) + start_index}\n"
                + bottom_hash,
                style=bottom_style,
            ),
        )
        print(Panel(group, title=filename))

        print("-----")
        print(escape("Split top [t]"))
        print(escape("Split bottom [b]"))
        print(escape("Return to previous chunks [p]"))
        print(escape("Exit file [q]"))
        action = Prompt.ask()
        if action == "t":
            return_value = _split_file(
                filename, first_half_lines, start_index=start_index
            )
            traversed_top = True
        elif action == "b":
            return_value = _split_file(
                filename, second_half_lines, start_index=halfway + start_index
            )
            traversed_bottom = True
        elif action == "p":
            return _PREVIOUS
        elif action == "q":
            return _QUIT
        else:
            raise ValueError("Invalid choice")

        if return_value == _QUIT:
            return _QUIT


def _get_file_hash(file_path: Path) -> str | None:
    sha1 = hashlib.sha1()
    with file_path.open("r") as fp:
        try:
            contents = fp.read()
        except UnicodeDecodeError:
            return None

    sha1.update(contents.encode())
    return sha1.hexdigest()


@app.command()
def main(input_path_str: str):
    input_path = Path(input_path_str)
    _traverse(input_path)


if __name__ == "__main__":
    typer.run(main)
