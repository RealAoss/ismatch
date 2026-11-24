"""Compare two full names and explain the result."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from itertools import islice, product

from . import lexicon
from .distance import similarity, skeleton
from .parse import Token, parse_name
from .phonemes import phonemes

__all__ = ["Match", "compare", "score", "is_match", "token_similarity", "keys", "token_keys", "DEFAULT_THRESHOLD"]

DEFAULT_THRESHOLD = 0.85
_DISTINCT_CAP = 0.78       # two spellings known to be different names
_SAME_FLOOR = 0.9          # two spellings resolved to the same known name
_WEAK_PAIR = 0.8           # below this, a paired name part counts against the match
_INITIAL_SIM = 0.85
_INITIAL_WEIGHT = 0.4
_REORDER_FACTOR = 0.92
_EXTRA_PENALTY = 0.2       # a name part present on one side only
_EXTRA_PENALTY_THIN = 0.5  # ... when only one part matched at all
_JOIN_MIN = 0.88
_JOIN_GAIN = 0.08


@dataclass
class Match:
    """Result of :func:`compare`."""

    score: float
    pairs: list = field(default_factory=list)        # (part of a, part of b, similarity)
    unmatched_a: list = field(default_factory=list)
    unmatched_b: list = field(default_factory=list)
    reordered: bool = False
    threshold: float = DEFAULT_THRESHOLD

    @property
    def is_match(self) -> bool:
        return self.score >= self.threshold

    @property
    def level(self) -> str:
        s = self.score
        if s >= 0.93:
            return "strong"
        if s >= 0.85:
            return "probable"
        if s >= 0.70:
            return "possible"
        return "no"

    def __bool__(self) -> bool:
        return self.is_match

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 4),
            "is_match": self.is_match,
            "level": self.level,
            "pairs": [{"a": a, "b": b, "score": round(s, 4)} for a, b, s in self.pairs],
            "unmatched_a": list(self.unmatched_a),
            "unmatched_b": list(self.unmatched_b),
            "reordered": self.reordered,
        }

    def explain(self) -> str:
        lines = [f"score {self.score:.2f}  ({self.level})"]
        for a, b, s in self.pairs:
            lines.append(f"  {a}  ~  {b}   {s:.2f}")
        if self.unmatched_a:
            lines.append("  only in first:  " + ", ".join(self.unmatched_a))
        if self.unmatched_b:
            lines.append("  only in second: " + ", ".join(self.unmatched_b))
        if self.reordered:
            lines.append("  (name parts appear in a different order)")
        return "\n".join(lines)


def _seq(script: str, form: tuple) -> tuple:
    out = []
    for part in form:
        out.extend(phonemes(script, part))
    return tuple(out)


@lru_cache(maxsize=50_000)
def _variants(tok: Token, other_script: str) -> tuple:
    """Phoneme sequences a token may stand for when facing ``other_script``."""
    out = []
    for n, form in enumerate(tok.forms):
        if tok.script != "la" and other_script == "la":
            # Use the vocalised reading when the lexicon knows every part.
            readings = [lexicon.readings_for(p, tok.script) for p in form]
            if all(readings):
                for combo in islice(product(*readings), 4):
                    seq = []
                    for r in combo:
                        seq.extend(lexicon.reading_phonemes(r))
                    out.append((n, tuple(seq)))
                continue
        seq = _seq(tok.script, form)
        if seq:
            out.append((n, seq))
    return tuple(out)


@lru_cache(maxsize=50_000)
def _ids(tok: Token) -> frozenset:
    """Lexicon entries this token is known to stand for."""
    for form in tok.forms:
        part = form[-1]
        if tok.script == "ar":
            ids = lexicon.arabic_ids(part)
        elif tok.script == "la":
            ids = lexicon.latin_ids(part)
        else:
            ids = lexicon.hebrew_ids(part)
        if ids:
            return ids
    return frozenset()


@lru_cache(maxsize=200_000)
def token_similarity(a: Token, b: Token) -> float:
    """Similarity in [0, 1] between two name parts, in any two scripts."""
    if a.kind == "initial" or b.kind == "initial":
        va, vb = _variants(a, b.script), _variants(b, a.script)
        if not va or not vb or not va[0][1] or not vb[0][1]:
            return 0.0
        x, y = va[0][1][0], vb[0][1][0]
        same = x.p == y.p if (x.t == "C" and y.t == "C") else (x.t != "C" and y.t != "C")
        if not same:
            return 0.0
        return 1.0 if a.kind == b.kind else _INITIAL_SIM
    best = 0.0
    both_articled = a.full >= 0 and b.full >= 0
    for na, sa in _variants(a, b.script):
        for nb, sb in _variants(b, a.script):
            if both_articled and na == a.full and nb == b.full:
                continue  # two shared articles would inflate the similarity
            s = similarity(sa, sb)
            if s > best:
                best = s
    if a.compound == b.compound:
        ia, ib = _ids(a), _ids(b)
        if ia and ib:
            if ia.isdisjoint(ib):
                best = min(best, _DISTINCT_CAP)   # known to be different names
            elif ia == ib and len(ia) == 1 and not a.compound:
                best = max(best, _SAME_FLOOR)     # two spellings of one known name
    return best


def _weight(tok: Token) -> float:
    return _INITIAL_WEIGHT if tok.kind == "initial" else 1.0


def _join(a: Token, b: Token) -> Token:
    forms = tuple(x + y for x, y in islice(product(a.forms, b.forms), 4))
    return Token(a.script, forms, a.display + " " + b.display)


def _merge_split_parts(A: list, B: list) -> list:
    """If one part of A is written as two adjacent parts in B, join them.

    Covers Abubakar / Abu Bakr, Salahuddin / Salah al-Din, Benali / Ben Ali.
    """
    B = list(B)
    for t in A:
        if t.kind == "initial":
            continue
        j = 0
        while j < len(B) - 1:
            u, v = B[j], B[j + 1]
            if u.kind == "name" and v.kind == "name" and u.script == v.script:
                merged = _join(u, v)
                s = token_similarity(t, merged)
                if s >= _JOIN_MIN and s > max(token_similarity(t, u), token_similarity(t, v)) + _JOIN_GAIN:
                    B[j:j + 2] = [merged]
                    continue
            j += 1
    return B


def _assign(S, wa, wb, monotonic: bool):
    """Best one-to-one assignment of rows to columns; returns (total, pairs)."""
    n, m = len(S), len(S[0]) if S else 0
    if monotonic:
        D = [[0.0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                D[i][j] = max(D[i - 1][j], D[i][j - 1],
                              D[i - 1][j - 1] + S[i - 1][j - 1] * min(wa[i - 1], wb[j - 1]))
        pairs = []
        i, j = n, m
        while i > 0 and j > 0:
            if D[i][j] == D[i - 1][j]:
                i -= 1
            elif D[i][j] == D[i][j - 1]:
                j -= 1
            else:
                pairs.append((i - 1, j - 1))
                i -= 1
                j -= 1
        return D[n][m], pairs[::-1]
    if m > 12:  # absurdly long name: greedy is good enough
        cells = sorted(((S[i][j] * min(wa[i], wb[j]), i, j) for i in range(n) for j in range(m)), reverse=True)
        used_i, used_j, pairs, total = set(), set(), [], 0.0
        for v, i, j in cells:
            if i not in used_i and j not in used_j and v > 0:
                used_i.add(i)
                used_j.add(j)
                pairs.append((i, j))
                total += v
        return total, sorted(pairs)

    @lru_cache(maxsize=None)
    def best(i: int, mask: int):
        if i == n:
            return 0.0, ()
        top, top_pairs = best(i + 1, mask)  # leave row i unmatched
        for j in range(m):
            if not mask & (1 << j):
                v = S[i][j] * min(wa[i], wb[j])
                if v <= 0:
                    continue
                sub, sub_pairs = best(i + 1, mask | (1 << j))
                if v + sub > top + 1e-12:
                    top, top_pairs = v + sub, ((i, j),) + sub_pairs
        return top, top_pairs

    total, pairs = best(0, 0)
    return total, list(pairs)


def compare(a: str, b: str, threshold: float = DEFAULT_THRESHOLD) -> Match:
    """Compare two full names written in Arabic, Latin or Hebrew script.

    >>> compare("محمد عبد الرحمن", "Mohamed Abdelrahman").is_match
    True
    """
    A, B = list(parse_name(a)), list(parse_name(b))
    if not A or not B:
        return Match(0.0, threshold=threshold)
    B = _merge_split_parts(A, B)
    A = _merge_split_parts(B, A)
    if len(A) > len(B):  # keep the assignment search on the shorter side
        res = _compare_tokens(B, A, threshold)
        res.pairs = [(y, x, s) for x, y, s in res.pairs]
        res.unmatched_a, res.unmatched_b = res.unmatched_b, res.unmatched_a
        return res
    return _compare_tokens(A, B, threshold)


def _compare_tokens(A, B, threshold) -> Match:
    S = [[token_similarity(x, y) for y in B] for x in A]
    wa, wb = [_weight(t) for t in A], [_weight(t) for t in B]
    mono_total, mono_pairs = _assign(S, wa, wb, True)
    free_total, free_pairs = _assign(S, wa, wb, False)
    reordered = free_total > mono_total + 1e-9
    pairs = free_pairs if reordered else mono_pairs

    num = den = 0.0
    used_a, used_b = set(), set()
    strong = 0
    out_pairs = []
    for i, j in pairs:
        w = min(wa[i], wb[j])
        s = S[i][j]
        if s < _WEAK_PAIR and len(pairs) > 1:
            s *= 0.25  # one clearly different part outweighs several equal ones
        num += w * s
        den += w
        used_a.add(i)
        used_b.add(j)
        if S[i][j] >= 0.8 and A[i].kind == "name" and B[j].kind == "name":
            strong += 1
        out_pairs.append((A[i].display, B[j].display, S[i][j]))
    left_a = [i for i in range(len(A)) if i not in used_a]
    left_b = [j for j in range(len(B)) if j not in used_b]
    wa_left = sum(wa[i] for i in left_a)
    wb_left = sum(wb[j] for j in left_b)
    conflict = min(wa_left, wb_left)          # both sides have something the other lacks
    extra = abs(wa_left - wb_left)            # one side simply has more parts
    den += conflict + extra * (_EXTRA_PENALTY if strong >= 2 else _EXTRA_PENALTY_THIN)
    value = num / den if den else 0.0
    if reordered:
        value *= _REORDER_FACTOR
    return Match(
        score=max(0.0, min(1.0, value)),
        pairs=out_pairs,
        unmatched_a=[A[i].display for i in left_a],
        unmatched_b=[B[j].display for j in left_b],
        reordered=reordered,
        threshold=threshold,
    )


def score(a: str, b: str) -> float:
    """Similarity in [0, 1] between two full names."""
    return compare(a, b).score


def is_match(a: str, b: str, threshold: float = DEFAULT_THRESHOLD) -> bool:
    """True if two names plausibly refer to the same person."""
    return compare(a, b, threshold).score >= threshold


def keys(name: str) -> tuple:
    """Script-independent blocking keys, one or more per name part.

    Two spellings of the same name share at least one key in nearly all cases,
    so the keys can be stored in a database column or used to bucket records
    before the (more expensive) pairwise :func:`compare`.

    >>> keys("محمد") == keys("Mohammed") == ("MHMD",)
    True
    """
    out = []
    for group in token_keys(name):
        for k in group:
            if k not in out:
                out.append(k)
    return tuple(out)


def token_keys(name: str) -> tuple:
    """Like :func:`keys`, but grouped: one tuple of keys per name part."""
    out = []
    for tok in parse_name(name):
        if tok.kind == "initial":
            continue
        group = []
        for _, seq in _variants(tok, "la") + _variants(tok, tok.script):
            k = skeleton(seq)
            if k not in group:
                group.append(k)
        if group:
            out.append(tuple(group))
    return tuple(out)
