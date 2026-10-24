"""Executable entrypoint for `python -m goldseam`."""

from goldseam.cli import app

if __name__ == "__main__":
    app(prog_name="goldseam")
