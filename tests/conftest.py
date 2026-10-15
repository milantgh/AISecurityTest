# -*- coding: utf-8 -*-
"""pytest global configuration: add src/ to sys.path.
This allows running tests without installing the package first.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, "..", "src"))
if os.path.isdir(_SRC) and _SRC not in sys.path:
    sys.path.insert(0, _SRC)