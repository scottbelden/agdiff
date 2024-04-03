# import hashlib
# from io import StringIO
# from pathlib import Path

# from rich import print as rprint
# from typer.testing import CliRunner

# from agdiff.main import app

# runner = CliRunner()


# def test_app(tmp_path: Path):
#     test_file = tmp_path / "test_file"
#     file_contents = """line1\nline2"""

#     sha1 = hashlib.sha1()
#     sha1.update(file_contents.encode())
#     file_hash = sha1.hexdigest()

#     test_file.write_text(file_contents)
#     result = runner.invoke(app, str(test_file))

#     expected_output_io = StringIO()
#     rprint(test_file, file=expected_output_io)
#     rprint(file_hash, file=expected_output_io)
#     assert result.stdout.startswith(expected_output_io.getvalue())
