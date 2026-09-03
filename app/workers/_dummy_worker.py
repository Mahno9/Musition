"""Test double: exercises the worker protocol without a GPU. Used by test_app.py."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common


def load():
    time.sleep(0.2)


def generate(p):
    common.set_progress(1, 2)
    with open(p["out_path"], "wb") as f:
        f.write(b"RIFF----WAVEfake")
    return [p["out_path"]], {"seed": 42}


if __name__ == "__main__":
    common.serve(load, generate)
