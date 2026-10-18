#!/usr/bin/env python3
"""Refuse a CHANGELOG.md that repeats the same bullet inside one release section."""
from __future__ import annotations

import argparse
import collections
import os
import re
import sys
import tempfile

MIN_LEN = 25


def duplicates(text: str):
    bad = []
    for section in re.split(r"^##\s+", text, flags=re.M)[1:]:
        title, _, body = section.partition("\n")
        bullets = []
        for line in body.splitlines():
            s = line.strip()
            if s.startswith("- ") or s.startswith("* "):
                if len(s) >= MIN_LEN:
                    bullets.append(s)
        for bullet, n in collections.Counter(bullets).items():
            if n > 1:
                bad.append((title.strip(), bullet, n))
    return bad


def check(path: str) -> int:
    if not os.path.exists(path):
        print("changelog-lint: no %s, skip" % path)
        return 0
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    bad = duplicates(text)
    for title, bullet, n in bad:
        print("FAIL [%s] x%d: %s" % (title, n, bullet))
    print("changelog-lint: %d duplicated bullet(s)" % len(bad))
    return 1 if bad else 0


def selftest() -> int:
    good = "# Changelog\n\n## [Unreleased]\n- Added a first thing that is long enough\n- Added a second thing that is long enough\n"
    bad = "# Changelog\n\n## [Unreleased]\n- Added a first thing that is long enough\n- Added a first thing that is long enough\n"
    with tempfile.TemporaryDirectory() as td:
        g = os.path.join(td, "good.md")
        b = os.path.join(td, "bad.md")
        open(g, "w", encoding="utf-8").write(good)
        open(b, "w", encoding="utf-8").write(bad)
        ok = check(g) == 0 and check(b) == 1
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="CHANGELOG.md")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return check(args.path)


if __name__ == "__main__":
    sys.exit(main())
