"""Command line interface:  ``ismatch compare | key | search | dedupe``."""

from __future__ import annotations

import argparse
import csv
import json
import sys

from . import __version__
from .index import NameIndex, dedupe
from .match import DEFAULT_THRESHOLD, compare, keys


def _read_names(path: str, column):
    """Read names from a text file (one per line) or a CSV column."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        if column is None and not path.lower().endswith((".csv", ".tsv")):
            return [line.strip() for line in fh if line.strip()]
        dialect = "excel-tab" if path.lower().endswith(".tsv") else "excel"
        rows = list(csv.reader(fh, dialect))
    if not rows:
        return []
    header = rows[0]
    if column is None:
        col = 0
    elif column.isdigit():
        col = int(column)
    elif column in header:
        col = header.index(column)
    else:
        raise SystemExit(f"ismatch: column {column!r} not found; header is {header}")
    body = rows[1:] if (column is not None and not column.isdigit()) else rows
    return [r[col].strip() for r in body if len(r) > col and r[col].strip()]


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    p = argparse.ArgumentParser(prog="ismatch", description="Match Arabic names across spellings and scripts.")
    p.add_argument("--version", action="version", version=f"ismatch {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compare", help="compare two names")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--json", action="store_true")
    c.add_argument("-t", "--threshold", type=float, default=DEFAULT_THRESHOLD)

    k = sub.add_parser("key", help="print the script-independent blocking keys of a name")
    k.add_argument("name")

    s = sub.add_parser("search", help="find a name in a file of names")
    s.add_argument("file")
    s.add_argument("query")
    s.add_argument("-c", "--column", help="CSV column name or 0-based number")
    s.add_argument("-n", "--limit", type=int, default=10)
    s.add_argument("-m", "--min-score", type=float, default=0.7)
    s.add_argument("--json", action="store_true")

    d = sub.add_parser("dedupe", help="group names in a file that refer to the same person")
    d.add_argument("file")
    d.add_argument("-c", "--column", help="CSV column name or 0-based number")
    d.add_argument("-t", "--threshold", type=float, default=DEFAULT_THRESHOLD)
    d.add_argument("--json", action="store_true")

    args = p.parse_args(argv)

    if args.cmd == "compare":
        m = compare(args.a, args.b, args.threshold)
        print(json.dumps(m.to_dict(), ensure_ascii=False, indent=2) if args.json else m.explain())
        return 0 if m.is_match else 1

    if args.cmd == "key":
        print(" ".join(keys(args.name)))
        return 0

    names = _read_names(args.file, args.column)
    if args.cmd == "search":
        hits = NameIndex(names).search(args.query, args.limit, args.min_score)
        if args.json:
            print(json.dumps([{"name": n, "score": round(sc, 4)} for n, sc in hits], ensure_ascii=False, indent=2))
        else:
            for n, sc in hits:
                print(f"{sc:.2f}  {n}")
        return 0 if hits else 1

    clusters = dedupe(names, args.threshold)
    if args.json:
        print(json.dumps([[names[i] for i in g] for g in clusters], ensure_ascii=False, indent=2))
    else:
        for n, g in enumerate(clusters, 1):
            print(f"# group {n}")
            for i in g:
                print(f"  {names[i]}")
        print(f"{len(clusters)} group(s) of likely duplicates among {len(names)} names", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
