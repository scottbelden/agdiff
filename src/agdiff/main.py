from dataclasses import dataclass
import hashlib
from math import floor
from pathlib import Path

from rich import print
from rich.markup import escape
from rich.panel import Panel
from rich.prompt import Prompt
from rich.tree import Tree
import typer


@dataclass
class _PathAndHash:
    path: str
    sha1_hash: str = ""

    def __rich__(self):
        return f"{self.path} ({self.sha1_hash})"


app = typer.Typer()


def _split_lines(lines: list[str], start_index: int = 0):
    if len(lines) == 1:
        print("Line contents:")
        print(Panel(lines[0]))
        return

    halfway = floor(len(lines) / 2)

    first_half_lines = lines[:halfway]
    first_half_str = "".join(first_half_lines)
    sha1 = hashlib.sha1()
    sha1.update(first_half_str.encode())
    print(Panel(f"Lines: {1 + start_index} - {halfway + start_index}\n" + f"{sha1.hexdigest()}"))

    second_half_lines = lines[halfway:]
    second_half_str = "".join(second_half_lines)
    sha1 = hashlib.sha1()
    sha1.update(second_half_str.encode())
    print(
        Panel(
            f"Lines: {halfway + 1 + start_index} - {len(lines) + start_index}\n"
            + f"{sha1.hexdigest()}"
        )
    )

    print("-----")
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
    if input_path.is_file():
        file_hash = _get_file_hash(input_path)
        print(input_path_str)
        print(file_hash)
        print("")
        print("-----")
        print(escape("Continue [c]"))
        print(escape("Split file [s]"))
        action = Prompt.ask()
        if action == "c":
            typer.Exit()
        elif action == "s":
            with input_path.open("r") as fp:
                lines = fp.readlines()
            _split_lines(lines)
    elif input_path.is_dir():
        folder_hashes: dict[Path, str] = {}
        root_directory = _PathAndHash(str(input_path))
        tree = Tree(root_directory)
        for root, dirs, files in input_path.walk(top_down=False):
            sha1 = hashlib.sha1()
            for dir in sorted(dirs):
                sha1.update(folder_hashes[root / dir].encode())
                if input_path == root:
                    tree.add(_PathAndHash(dir, folder_hashes[root / dir]))
            for file in sorted(files):
                file_hash = _get_file_hash(root / file)
                if file_hash:
                    sha1.update(file_hash.encode())
                    if input_path == root:
                        tree.add(_PathAndHash(file, file_hash))
                else:
                    if input_path == root:
                        tree.add(_PathAndHash(file, "Binary"))

            folder_hash = sha1.hexdigest()
            folder_hashes[root] = folder_hash
            root_directory.sha1_hash = folder_hash
        print(tree)

    else:
        raise ValueError("Unsupported path type")


if __name__ == "__main__":
    typer.run(main)
