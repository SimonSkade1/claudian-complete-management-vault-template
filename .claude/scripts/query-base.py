#!/usr/bin/env python3
"""
Query an Obsidian Base (.base) file and display results as a formatted table.

Usage:
    python3 query-base.py <base-file-path> [view-name] [--paths]

    <base-file-path>  Path to .base file, relative to vault root
    [view-name]       Name of the view to display. If omitted, lists available views.
    --paths           Print vault-relative file paths only (one per line, view
                      sort order, no table/header) — for scripting.

Examples:
    python3 query-base.py me.base
    python3 query-base.py me.base Do
    python3 query-base.py claude.base Do --paths
"""

import sys
import os
import re
import math
import yaml
from datetime import date, datetime, timedelta
from pathlib import Path

# Vault root = two levels up from this script (.claude/scripts/query-base.py)
VAULT_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# YAML frontmatter reader
# ---------------------------------------------------------------------------

def read_frontmatter(filepath: Path) -> dict:
    """Read YAML frontmatter from a markdown file."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    yaml_text = text[3:end]
    try:
        data = yaml.safe_load(yaml_text)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Property access helpers
# ---------------------------------------------------------------------------

def get_prop(props: dict, name: str, filepath: Path) -> object:
    """Get a property value. Handles file.name and frontmatter properties."""
    if name == "file.name":
        return filepath.stem
    if name == "file.ext":
        return filepath.suffix.lstrip(".")
    return props.get(name)


def is_empty(value) -> bool:
    """Check if a value is empty/missing in the Obsidian sense."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def parse_date(s) -> date | None:
    """Try to parse a YYYY-MM-DD date from a string or datetime.date."""
    if isinstance(s, date):
        return s
    if isinstance(s, datetime):
        return s.date()
    if isinstance(s, str):
        s = s.strip()
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
        if m:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


# ---------------------------------------------------------------------------
# Expression evaluator
#
# General recursive-descent evaluator for the subset of the Obsidian Bases
# expression language used in filters and formulas: literals, property refs,
# file.* properties, formula.* references (lazy, memoized), if(), date math,
# comparisons, &&/||/!, string/list/number methods, regex literals with
# .matches(). Unknown constructs raise CannotEvaluate -> filters include the
# file by default (warning printed once per distinct expression), formulas
# evaluate to "".
#
# Known gaps vs. real Obsidian: file.hasTag() checks frontmatter tags only
# (not body #tags); file.hasLink(), 'this', and link() are unsupported.
# ---------------------------------------------------------------------------

class CannotEvaluate(Exception):
    pass


_WARNED: set = set()


def _warn_once(key: str, msg: str) -> None:
    if key not in _WARNED:
        _WARNED.add(key)
        print(msg, file=sys.stderr)


class _Regex:
    """Wrapper marking a value as a regex literal."""

    def __init__(self, pattern: str):
        self.pattern = pattern


class _FileVal:
    """A file value (e.g. an element of file.backlinks)."""

    def __init__(self, path: Path):
        self.path = path

    def __str__(self):
        return self.path.stem

    def __eq__(self, other):
        return isinstance(other, _FileVal) and self.path == other.path

    def __hash__(self):
        return hash(self.path)


_BACKLINK_INDEX: dict = {}
_BACKLINK_INDEX_BUILT = [False]
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


def _build_backlink_index() -> None:
    """Scan all vault .md files once; map casefolded link targets -> sources."""
    if _BACKLINK_INDEX_BUILT[0]:
        return
    _BACKLINK_INDEX_BUILT[0] = True
    for src in VAULT_ROOT.rglob("*.md"):
        try:
            text = src.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in _WIKILINK_RE.finditer(text):
            target = m.group(1).strip()
            if target.lower().endswith(".md"):
                target = target[:-3]
            _BACKLINK_INDEX.setdefault(target.casefold(), set()).add(src)


def _backlinks_of(fp: Path) -> list:
    _build_backlink_index()
    rel_noext = str(fp.relative_to(VAULT_ROOT))
    if rel_noext.lower().endswith(".md"):
        rel_noext = rel_noext[:-3]
    sources = set()
    sources |= _BACKLINK_INDEX.get(fp.stem.casefold(), set())
    sources |= _BACKLINK_INDEX.get(rel_noext.casefold(), set())
    sources.discard(fp)
    return [_FileVal(p) for p in sorted(sources)]


# --- Scanner ---------------------------------------------------------------

_TWO_CHAR_OPS = ("==", "!=", "<=", ">=", "&&", "||")
_ONE_CHAR_OPS = "(),.!<>+-*/%"


class _Scanner:
    """On-demand tokenizer. `regex_ok` marks positions where a '/' starts a
    regex literal (primary position) rather than division."""

    def __init__(self, s: str):
        self.s = s
        self.i = 0

    def next(self, regex_ok: bool = False) -> tuple:
        s = self.s
        while self.i < len(s) and s[self.i].isspace():
            self.i += 1
        i = self.i
        if i >= len(s):
            return ("eof", None)
        c = s[i]
        if c in "\"'":  # string literal
            j, out = i + 1, []
            while j < len(s) and s[j] != c:
                if s[j] == "\\" and j + 1 < len(s):
                    out.append(s[j + 1])
                    j += 2
                else:
                    out.append(s[j])
                    j += 1
            if j >= len(s):
                raise CannotEvaluate("unterminated string")
            self.i = j + 1
            return ("str", "".join(out))
        if c == "/" and regex_ok:  # regex literal
            j, out = i + 1, []
            while j < len(s) and s[j] != "/":
                if s[j] == "\\" and j + 1 < len(s):
                    out.append(s[j])
                    out.append(s[j + 1])
                    j += 2
                else:
                    out.append(s[j])
                    j += 1
            if j >= len(s):
                raise CannotEvaluate("unterminated regex")
            self.i = j + 1
            return ("regex", "".join(out))
        if c.isdigit():
            m = re.match(r"\d+(\.\d+)?", s[i:])
            self.i = i + m.end()
            text = m.group(0)
            return ("num", float(text) if "." in text else int(text))
        if c.isalpha() or c == "_":
            m = re.match(r"[A-Za-z_]\w*", s[i:])
            self.i = i + m.end()
            return ("ident", m.group(0))
        if s[i:i + 2] in _TWO_CHAR_OPS:
            self.i = i + 2
            return ("op", s[i:i + 2])
        if c in _ONE_CHAR_OPS:
            self.i = i + 1
            return ("op", c)
        raise CannotEvaluate(f"unexpected character {c!r}")

    def peek(self, regex_ok: bool = False) -> tuple:
        save = self.i
        tok = self.next(regex_ok)
        self.i = save
        return tok


# --- Parser (produces AST tuples, cached per expression string) ------------

_AST_CACHE: dict = {}


def _parse(expr: str):
    if expr in _AST_CACHE:
        return _AST_CACHE[expr]
    sc = _Scanner(expr)
    node = _parse_or(sc)
    kind, val = sc.next()
    if kind != "eof":
        raise CannotEvaluate(f"trailing input at {val!r}")
    _AST_CACHE[expr] = node
    return node


def _parse_or(sc):
    node = _parse_and(sc)
    while sc.peek() == ("op", "||"):
        sc.next()
        node = ("or", node, _parse_and(sc))
    return node


def _parse_and(sc):
    node = _parse_cmp(sc)
    while sc.peek() == ("op", "&&"):
        sc.next()
        node = ("and", node, _parse_cmp(sc))
    return node


def _parse_cmp(sc):
    node = _parse_add(sc)
    while sc.peek()[0] == "op" and sc.peek()[1] in ("==", "!=", "<", "<=", ">", ">="):
        _, op = sc.next()
        node = ("binop", op, node, _parse_add(sc))
    return node


def _parse_add(sc):
    node = _parse_mul(sc)
    while sc.peek()[0] == "op" and sc.peek()[1] in ("+", "-"):
        _, op = sc.next()
        node = ("binop", op, node, _parse_mul(sc))
    return node


def _parse_mul(sc):
    node = _parse_unary(sc)
    while sc.peek()[0] == "op" and sc.peek()[1] in ("*", "/", "%"):
        _, op = sc.next()
        node = ("binop", op, node, _parse_unary(sc))
    return node


def _parse_unary(sc):
    if sc.peek() == ("op", "!"):
        sc.next()
        return ("not", _parse_unary(sc))
    if sc.peek() == ("op", "-"):
        sc.next()
        return ("neg", _parse_unary(sc))
    return _parse_postfix(sc)


def _parse_args(sc):
    args = []
    if sc.peek(regex_ok=True) == ("op", ")"):
        sc.next()
        return args
    while True:
        args.append(_parse_or(sc))
        tok = sc.next()
        if tok == ("op", ")"):
            return args
        if tok != ("op", ","):
            raise CannotEvaluate("expected ',' or ')' in argument list")


def _parse_postfix(sc):
    node = _parse_primary(sc)
    while sc.peek() == ("op", "."):
        sc.next()
        kind, name = sc.next()
        if kind != "ident":
            raise CannotEvaluate("expected identifier after '.'")
        if sc.peek() == ("op", "("):
            sc.next()
            node = ("method", node, name, _parse_args(sc))
        else:
            node = ("attr", node, name)
    return node


def _parse_primary(sc):
    kind, val = sc.next(regex_ok=True)
    if kind in ("str", "num"):
        return ("lit", val)
    if kind == "regex":
        return ("regexlit", val)
    if (kind, val) == ("op", "("):
        node = _parse_or(sc)
        if sc.next() != ("op", ")"):
            raise CannotEvaluate("expected ')'")
        return node
    if kind == "ident":
        if val == "true":
            return ("lit", True)
        if val == "false":
            return ("lit", False)
        if val == "null":
            return ("lit", None)
        if sc.peek() == ("op", "("):
            sc.next()
            return ("call", val, _parse_args(sc))
        return ("prop", val)
    raise CannotEvaluate(f"unexpected token {val!r}")


# --- Evaluation ------------------------------------------------------------

class EvalCtx:
    """Per-file evaluation context with lazy, memoized formula values."""

    def __init__(self, props: dict, filepath: Path, formulas: dict):
        self.props = props
        self.filepath = filepath
        self.formulas = formulas or {}
        self.memo: dict = {}
        self.stack: set = set()
        self.value_stack: list = []  # bindings for 'value' inside filter()/map()


def _truthy(val) -> bool:
    if val is False or val is None:
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    if isinstance(val, list) and not val:
        return False
    if isinstance(val, (int, float)) and not isinstance(val, bool) and val == 0:
        return False
    return True


_DURATION_DAYS = {"y": 365, "year": 365, "years": 365, "M": 30, "month": 30,
                  "months": 30, "w": 7, "week": 7, "weeks": 7, "d": 1, "day": 1, "days": 1}
_DURATION_SECS = {"h": 3600, "hour": 3600, "hours": 3600, "m": 60, "minute": 60,
                  "minutes": 60, "s": 1, "second": 1, "seconds": 1}


def _parse_duration(s: str) -> timedelta:
    total, found = timedelta(), False
    for num, unit in re.findall(r"(\d+(?:\.\d+)?)\s*([A-Za-z]+)", s):
        n = float(num)
        if unit in _DURATION_DAYS:
            total += timedelta(days=n * _DURATION_DAYS[unit])
        elif unit in _DURATION_SECS:
            total += timedelta(seconds=n * _DURATION_SECS[unit])
        else:
            raise CannotEvaluate(f"unknown duration unit {unit!r}")
        found = True
    if not found:
        raise CannotEvaluate(f"cannot parse duration {s!r}")
    return total


def _num(v):
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float)):
        return v
    try:
        return float(v)
    except (TypeError, ValueError):
        raise CannotEvaluate(f"not a number: {v!r}")


def _to_str(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _eq(a, b) -> bool:
    if is_empty(a) or is_empty(b):
        return is_empty(a) and is_empty(b)
    if isinstance(a, bool) and isinstance(b, bool):
        return a == b
    if (isinstance(a, (int, float)) and not isinstance(a, bool)
            and isinstance(b, (int, float)) and not isinstance(b, bool)):
        return a == b
    da, db = parse_date(a), parse_date(b)
    if da is not None and db is not None:
        return da == db
    return str(a).strip() == str(b).strip()


def _cmp(op: str, a, b) -> bool:
    if is_empty(a) or is_empty(b):
        return False
    if isinstance(a, (date, datetime)) or isinstance(b, (date, datetime)):
        da, db = parse_date(a), parse_date(b)
        if da is None or db is None:
            raise CannotEvaluate("comparing date with non-date")
        a, b = da, db
    elif not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        try:
            a, b = float(a), float(b)
        except (TypeError, ValueError):
            a, b = str(a), str(b)
    if op == "<":
        return a < b
    if op == "<=":
        return a <= b
    if op == ">":
        return a > b
    return a >= b


def _as_datetime(d) -> datetime:
    return d if isinstance(d, datetime) else datetime(d.year, d.month, d.day)


def _binop(op: str, a, b):
    if op == "==":
        return _eq(a, b)
    if op == "!=":
        return not _eq(a, b)
    if op in ("<", "<=", ">", ">="):
        return _cmp(op, a, b)
    if op == "+":
        if isinstance(a, (date, datetime)) and isinstance(b, (str, timedelta)):
            return a + (b if isinstance(b, timedelta) else _parse_duration(b))
        if isinstance(a, str) or isinstance(b, str):
            return _to_str(a) + _to_str(b)
        if isinstance(a, timedelta) and isinstance(b, timedelta):
            return a + b
        return _num(a) + _num(b)
    if op == "-":
        if isinstance(a, (date, datetime)) and isinstance(b, (date, datetime)):
            return _as_datetime(a) - _as_datetime(b)
        if isinstance(a, (date, datetime)) and isinstance(b, (str, timedelta)):
            return a - (b if isinstance(b, timedelta) else _parse_duration(b))
        return _num(a) - _num(b)
    if op == "*":
        return _num(a) * _num(b)
    if op == "/":
        return _num(a) / _num(b)
    if op == "%":
        return _num(a) % _num(b)
    raise CannotEvaluate(f"operator {op!r} not supported")


_MOMENT_MAP = [("YYYY", "%Y"), ("dddd", "%A"), ("ddd", "%a"), ("MM", "%m"),
               ("DD", "%d"), ("HH", "%H"), ("mm", "%M"), ("ss", "%S")]


def _format_date(d, fmt: str) -> str:
    for k, v in _MOMENT_MAP:
        fmt = fmt.replace(k, v)
    return _as_datetime(d).strftime(fmt)


def _method(recv, name: str, args: list):
    if isinstance(recv, _Regex):
        if name == "matches":
            return re.search(recv.pattern, _to_str(args[0])) is not None
        raise CannotEvaluate(f"regex method .{name}() not supported")
    if isinstance(recv, _FileVal):
        if name == "asFile":
            return recv
        if name == "inFolder":
            folder = str(args[0]).strip("/")
            rel = str(recv.path.relative_to(VAULT_ROOT))
            return rel.startswith(folder + "/") if folder else True
        raise CannotEvaluate(f"file method .{name}() not supported")
    if name == "asFile":
        target = str(recv).strip().strip("[]")  # accept "[[Note]]" link strings too

        if target.lower().endswith(".md"):
            target = target[:-3]
        cand = VAULT_ROOT / (target + ".md")
        if cand.exists():
            return _FileVal(cand)
        matches = [p for p in VAULT_ROOT.rglob(Path(target).name + ".md")]
        return _FileVal(matches[0]) if matches else None
    if name == "isEmpty":
        return is_empty(recv)
    if is_empty(recv):
        if name in ("contains", "containsAny", "matches", "startsWith", "endsWith"):
            return False
        return None
    if name == "contains":
        if isinstance(recv, list):
            return str(args[0]).strip() in [str(v).strip() for v in recv]
        return str(args[0]) in str(recv)
    if name == "containsAny":
        for a in args:
            if _method(recv, "contains", [a]):
                return True
        return False
    if name == "matches":
        pat = args[0].pattern if isinstance(args[0], _Regex) else str(args[0])
        return re.search(pat, str(recv)) is not None
    if name == "startsWith":
        return str(recv).startswith(str(args[0]))
    if name == "endsWith":
        return str(recv).endswith(str(args[0]))
    if name == "toString":
        return _to_str(recv)
    if name == "lower":
        return str(recv).lower()
    if name == "upper":
        return str(recv).upper()
    if name == "round":
        digits = int(args[0]) if args else 0
        r = round(_num(recv), digits)
        return int(r) if digits <= 0 else r
    if name == "floor":
        return math.floor(_num(recv))
    if name == "ceil":
        return math.ceil(_num(recv))
    if name == "abs":
        return abs(_num(recv))
    if name == "toFixed":
        return f"{_num(recv):.{int(args[0]) if args else 0}f}"
    if name == "format":
        d = recv if isinstance(recv, (date, datetime)) else parse_date(recv)
        if d is None:
            raise CannotEvaluate("format() on non-date")
        return _format_date(d, str(args[0]))
    raise CannotEvaluate(f"method .{name}() not supported")


def _attr(recv, name: str):
    if isinstance(recv, _FileVal):
        fp = recv.path
        if name in ("name", "basename"):
            return fp.stem
        if name == "path":
            return str(fp.relative_to(VAULT_ROOT))
        if name == "folder":
            return str(fp.relative_to(VAULT_ROOT).parent)
        if name == "ext":
            return fp.suffix.lstrip(".")
        raise CannotEvaluate(f"file attribute .{name} not supported")
    if isinstance(recv, timedelta):
        table = {"days": 86400, "hours": 3600, "minutes": 60,
                 "seconds": 1, "milliseconds": 0.001}
        if name in table:
            v = recv.total_seconds() / table[name]
            return int(v) if float(v).is_integer() else v
    if isinstance(recv, (date, datetime)):
        if name in ("year", "month", "day"):
            return getattr(recv, name)
        if isinstance(recv, datetime) and name in ("hour", "minute", "second"):
            return getattr(recv, name)
    if isinstance(recv, (list, str)) and name == "length":
        return len(recv)
    if is_empty(recv):
        return None
    raise CannotEvaluate(f"attribute .{name} not supported on {type(recv).__name__}")


def _file_attr(name: str, ctx: "EvalCtx"):
    fp = ctx.filepath
    if name in ("name", "basename"):
        return fp.stem
    if name == "path":
        return str(fp.relative_to(VAULT_ROOT))
    if name == "folder":
        return str(fp.relative_to(VAULT_ROOT).parent)
    if name == "ext":
        return fp.suffix.lstrip(".")
    if name == "size":
        try:
            return fp.stat().st_size
        except OSError:
            return None
    if name in ("ctime", "mtime"):
        try:
            st = fp.stat()
        except OSError:
            return None
        return datetime.fromtimestamp(st.st_ctime if name == "ctime" else st.st_mtime)
    if name == "properties":
        return ctx.props
    if name == "backlinks":
        return _backlinks_of(fp)
    raise CannotEvaluate(f"file.{name} not supported")


def _file_method(name: str, args: list, ctx: "EvalCtx"):
    fp = ctx.filepath
    if name == "inFolder":
        folder = str(args[0]).strip("/")
        rel = str(fp.relative_to(VAULT_ROOT))
        return rel.startswith(folder + "/") if folder else True
    if name == "hasProperty":
        return str(args[0]) in ctx.props
    if name == "hasTag":
        # Frontmatter tags only; body #tags are not scanned.
        tags = ctx.props.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        wanted = str(args[0]).lstrip("#")
        norm = [str(t).lstrip("#") for t in tags]
        return any(t == wanted or t.startswith(wanted + "/") for t in norm)
    raise CannotEvaluate(f"file.{name}() not supported")


def _call(name: str, argnodes: list, ctx: "EvalCtx"):
    if name == "if":
        if not 2 <= len(argnodes) <= 3:
            raise CannotEvaluate("if() takes 2 or 3 arguments")
        if _truthy(_eval(argnodes[0], ctx)):
            return _eval(argnodes[1], ctx)
        return _eval(argnodes[2], ctx) if len(argnodes) == 3 else None
    args = [_eval(a, ctx) for a in argnodes]
    if name == "date":
        v = args[0]
        if isinstance(v, (date, datetime)):
            return v
        if is_empty(v):
            return None
        try:
            return datetime.fromisoformat(str(v).strip())
        except ValueError:
            return parse_date(v)
    if name == "today":
        return date.today()
    if name == "now":
        return datetime.now()
    if name == "duration":
        return _parse_duration(str(args[0]))
    if name == "number":
        return _num(args[0])
    if name == "min":
        return min(_num(a) for a in args)
    if name == "max":
        return max(_num(a) for a in args)
    raise CannotEvaluate(f"function {name}() not supported")


def _formula_value(name: str, ctx: "EvalCtx"):
    if name in ctx.memo:
        return ctx.memo[name]
    if name in ctx.stack:
        raise CannotEvaluate(f"formula cycle at {name!r}")
    expr = ctx.formulas.get(name)
    if expr is None:
        raise CannotEvaluate(f"unknown formula {name!r}")
    ctx.stack.add(name)
    try:
        val = _eval(_parse(str(expr)), ctx)
    except CannotEvaluate as e:
        _warn_once(f"formula:{name}",
                   f"  [warn] Cannot evaluate formula {name!r}: {e} — treating as empty")
        val = ""
    finally:
        ctx.stack.discard(name)
    ctx.memo[name] = val
    return val


def _eval(node, ctx: "EvalCtx"):
    kind = node[0]
    if kind == "lit":
        return node[1]
    if kind == "regexlit":
        return _Regex(node[1])
    if kind == "prop":
        name = node[1]
        if name == "value" and ctx.value_stack:
            return ctx.value_stack[-1]
        if name in ("this", "file", "note", "formula"):
            raise CannotEvaluate(f"bare {name!r} not supported")
        return ctx.props.get(name)
    if kind == "attr":
        recv, name = node[1], node[2]
        if recv == ("prop", "file"):
            return _file_attr(name, ctx)
        if recv == ("prop", "note"):
            return ctx.props.get(name)
        if recv == ("prop", "formula"):
            return _formula_value(name, ctx)
        return _attr(_eval(recv, ctx), name)
    if kind == "method":
        recv, name, argnodes = node[1], node[2], node[3]
        if name in ("filter", "map") and recv != ("prop", "file"):
            # Lazy per-element evaluation with 'value' bound to the element
            lst = _eval(recv, ctx)
            if is_empty(lst):
                return []
            if not isinstance(lst, list):
                lst = [lst]
            out = []
            for el in lst:
                ctx.value_stack.append(el)
                try:
                    r = _eval(argnodes[0], ctx)
                finally:
                    ctx.value_stack.pop()
                if name == "map":
                    out.append(r)
                elif _truthy(r):
                    out.append(el)
            return out
        args = [_eval(a, ctx) for a in argnodes]
        if recv == ("prop", "file"):
            return _file_method(name, args, ctx)
        return _method(_eval(recv, ctx), name, args)
    if kind == "call":
        return _call(node[1], node[2], ctx)
    if kind == "not":
        return not _truthy(_eval(node[1], ctx))
    if kind == "neg":
        return -_num(_eval(node[1], ctx))
    if kind == "and":
        return _truthy(_eval(node[1], ctx)) and _truthy(_eval(node[2], ctx))
    if kind == "or":
        return _truthy(_eval(node[1], ctx)) or _truthy(_eval(node[2], ctx))
    if kind == "binop":
        return _binop(node[1], _eval(node[2], ctx), _eval(node[3], ctx))
    raise CannotEvaluate(f"node kind {kind!r}")


# --- Public API ------------------------------------------------------------

def eval_filter(filt, ctx: EvalCtx) -> bool:
    """Evaluate a filter node (string, or dict with and/or/not keys)."""
    if isinstance(filt, str):
        try:
            return _truthy(_eval(_parse(filt), ctx))
        except CannotEvaluate as e:
            _warn_once(f"filter:{filt}",
                       f"  [warn] Cannot evaluate filter {filt!r} ({e}) — including by default")
            return True
    if isinstance(filt, dict):
        if "and" in filt:
            return all(eval_filter(sub, ctx) for sub in filt["and"])
        if "or" in filt:
            return any(eval_filter(sub, ctx) for sub in filt["or"])
        if "not" in filt:
            return not any(eval_filter(sub, ctx) for sub in filt["not"])
    _warn_once(f"struct:{filt!r}",
               f"  [warn] Unrecognized filter structure: {filt!r} — including by default")
    return True


def compute_formula(name: str, ctx: EvalCtx) -> object:
    """Compute a named formula for the context's file; '' if unevaluable."""
    try:
        return _formula_value(name, ctx)
    except CannotEvaluate:
        return ""


# ---------------------------------------------------------------------------
# Table formatting
# ---------------------------------------------------------------------------

def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format data as an aligned text table."""
    if not rows:
        # Still show headers
        rows = []

    # Compute column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Build format string
    parts = []
    for w in col_widths:
        parts.append(f"{{:<{w}}}")
    fmt = "  ".join(parts)

    lines = []
    lines.append(fmt.format(*headers))
    lines.append(fmt.format(*["─" * w for w in col_widths]))
    for row in rows:
        # Pad row if needed
        while len(row) < len(headers):
            row.append("")
        lines.append(fmt.format(*[str(c) for c in row]))

    return "\n".join(lines)


def format_value(val) -> str:
    """Format a property value for display."""
    if val is None:
        return ""
    if isinstance(val, list):
        items = [str(v).strip() for v in val if v is not None and str(v).strip()]
        return ", ".join(items)
    if isinstance(val, date) and not isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, datetime):
        return val.date().isoformat()
    s = str(val).strip()
    return s


# ---------------------------------------------------------------------------
# Column display name resolution
# ---------------------------------------------------------------------------

def get_display_name(col: str, properties_config: dict) -> str:
    """Resolve a column key to its display name using the properties config."""
    if properties_config:
        # Direct match
        if col in properties_config and "displayName" in properties_config[col]:
            return properties_config[col]["displayName"]
        # Try with note. prefix
        prefixed = f"note.{col}"
        if prefixed in properties_config and "displayName" in properties_config[prefixed]:
            return properties_config[prefixed]["displayName"]
        # Try formula. prefix
        formula_key = f"formula.{col}"
        if formula_key in properties_config and "displayName" in properties_config[formula_key]:
            return properties_config[formula_key]["displayName"]
    # Fallback: title-case the column name
    return col.replace("_", " ").replace(".", " ").title()


# ---------------------------------------------------------------------------
# Sort helpers
# ---------------------------------------------------------------------------

def sort_key(props: dict, filepath: Path, formulas: dict, sort_spec: dict):
    """Return a sort key for a file based on sort specification."""
    prop_name = sort_spec.get("property", "")
    direction = sort_spec.get("direction", "ASC")

    # Get value
    if prop_name.startswith("formula."):
        formula_name = prop_name[len("formula."):]
        val = formulas.get(formula_name, "")
    else:
        val = get_prop(props, prop_name, filepath)

    # Normalize for sorting
    if val is None or (isinstance(val, str) and val.strip() == ""):
        # Put empties at end regardless of direction
        if direction == "ASC":
            return (1, "")
        else:
            return (1, "")
    if isinstance(val, (int, float)):
        sort_val = val
        if direction == "DESC":
            sort_val = -val
        return (0, sort_val)
    if isinstance(val, date):
        ordinal = val.toordinal()
        if direction == "DESC":
            ordinal = -ordinal
        return (0, ordinal)
    # String
    s = str(val).strip().lower()
    return (0, s)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = [a for a in sys.argv[1:] if a != "--paths"]
    paths_mode = "--paths" in sys.argv[1:]

    if not args:
        print(__doc__.strip())
        sys.exit(1)

    base_path = VAULT_ROOT / args[0]
    if not base_path.exists():
        print(f"Error: File not found: {base_path}")
        sys.exit(1)

    # Parse base file
    with open(base_path, encoding="utf-8") as f:
        base = yaml.safe_load(f)

    views = base.get("views", [])
    global_filters = base.get("filters")
    global_formulas = base.get("formulas", {}) or {}
    properties_config = base.get("properties", {}) or {}

    # If no view name given, list views
    if len(args) < 2:
        print(f"Views in {args[0]}:\n")
        for i, v in enumerate(views):
            print(f"  {i + 1}. {v['name']} ({v['type']})")
        print(f"\nUsage: {sys.argv[0]} {args[0]} <view-name>")
        sys.exit(0)

    # Find view by name (case-insensitive prefix match)
    view_name = " ".join(args[1:])
    selected = None
    for v in views:
        if v["name"].lower() == view_name.lower():
            selected = v
            break
    if selected is None:
        # Try prefix match
        for v in views:
            if v["name"].lower().startswith(view_name.lower()):
                selected = v
                break
    if selected is None:
        print(f"Error: No view matching '{view_name}'")
        print("Available views:")
        for v in views:
            print(f"  - {v['name']}")
        sys.exit(1)

    if not paths_mode:
        print(f"View: {selected['name']}\n")

    # Determine which folder to scan from global filters
    scan_folder = None
    if global_filters:
        scan_folder = _extract_folder(global_filters)

    if scan_folder is None:
        # Default to vault root
        scan_folder = ""

    # Scan markdown files
    scan_path = VAULT_ROOT / scan_folder if scan_folder else VAULT_ROOT
    if not scan_path.exists():
        print(f"Error: Scan folder not found: {scan_path}")
        sys.exit(1)

    md_files = sorted(scan_path.rglob("*.md"))

    # Combine filters: global AND view-specific
    combined = {"and": []}
    if global_filters:
        combined["and"].append(global_filters)
    if selected.get("filters"):
        combined["and"].append(selected["filters"])

    # Apply filters
    matching = []
    for fp in md_files:
        props = read_frontmatter(fp)
        ctx = EvalCtx(props, fp, global_formulas)
        if eval_filter(combined, ctx):
            # Compute formulas (filter evaluation already memoized some)
            computed_formulas = {name: compute_formula(name, ctx)
                                 for name in global_formulas}
            matching.append((fp, props, computed_formulas))

    # Get columns from view order
    columns = selected.get("order", ["file.name"])

    # Resolve display names for headers
    headers = []
    for col in columns:
        headers.append(get_display_name(col, properties_config))

    # Build rows
    rows = []
    for fp, props, formulas in matching:
        row = []
        for col in columns:
            if col.startswith("formula."):
                formula_name = col[len("formula."):]
                val = formulas.get(formula_name, "")
            else:
                val = get_prop(props, col, fp)
            row.append(format_value(val))
        rows.append(row)

    # Sort
    sort_specs = selected.get("sort", [])
    if sort_specs:
        # Sort by last sort key first (stable sort, so we apply in reverse order)
        for spec in reversed(sort_specs):
            direction = spec.get("direction", "ASC")
            reverse = (direction == "DESC")

            def make_key(item, spec=spec):
                fp, props, formulas = matching[rows.index(item)]
                return sort_key(props, fp, formulas, spec)

            # Pair rows with matching entries for sorting
            paired = list(zip(rows, matching))
            if reverse:
                # For DESC, we need custom handling since sort_key already negates numeric values
                paired.sort(key=lambda p: sort_key(p[1][1], p[1][0], p[1][2], spec))
            else:
                paired.sort(key=lambda p: sort_key(p[1][1], p[1][0], p[1][2], spec))
            rows = [p[0] for p in paired]
            matching = [p[1] for p in paired]

    # Display
    if paths_mode:
        for fp, _props, _formulas in matching:
            print(fp.relative_to(VAULT_ROOT))
        return

    table = format_table(headers, rows)
    print(table)
    print(f"\n({len(rows)} result{'s' if len(rows) != 1 else ''})")


def _extract_folder(filt) -> str | None:
    """Extract the folder from a file.inFolder filter."""
    if isinstance(filt, str):
        m = re.match(r'^file\.inFolder\("(.+?)"\)$', filt)
        if m:
            return m.group(1)
        return None
    if isinstance(filt, dict):
        for key in ("and", "or", "not"):
            if key in filt:
                for sub in filt[key]:
                    result = _extract_folder(sub)
                    if result is not None:
                        return result
    return None


if __name__ == "__main__":
    main()
