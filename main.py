# -*- coding: utf-8 -*-
"""
AISecurityTest quick entry point.
Usage:
    python main.py            # show help
    python main.py list       # same as aisec list
    python main.py validate   # same as aisec validate
After installing the package, the `aisec` command is recommended.
"""
import sys
import os

# Allow running without installation: add src/to sys.path.
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "src")
if os.path.isdir(_SRC) and _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def main():
    from aisecurity.cli.main import main as cli_main
    return cli_main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())