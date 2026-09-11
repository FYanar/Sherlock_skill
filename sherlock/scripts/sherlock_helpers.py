#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlock shared helpers v1.0 (Faz D4 M2 — idiom tekilleştirme).
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tekrar eden 1-2 satırlık idiomlar buradadır:
- read_text / write_text (utf-8, errors=replace)
- utc_stamp() → %Y%m%d_%H%M%S
- sha12(text) → hashlib.sha256(...).hexdigest()[:12]

Kullanım (scripts/ içinden, çalıştırma yönünden bağımsız):
    try:
        from sherlock_helpers import read_text, write_text, utc_stamp, sha12
    except ImportError:
        from scripts.sherlock_helpers import read_text, write_text, utc_stamp, sha12
"""

import datetime
import hashlib
import os


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_text(path: str, text: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def utc_stamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
