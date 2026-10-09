"""A minimal YAML reader, with no outside library dependency, built only for
this harness's own files.

It supports only what the harness actually uses: block mapping, block
sequence (made of scalars or small nested dicts), a flow list like
`[a, b]`, a scalar with or without quotes, `null`/`true`/`false`, and `#` comments.
This is not a general YAML parser — do not reuse it outside this repo.
"""
import re

_BLOCK_SCALAR_RE = re.compile(r"^[|>][+-]?\d?$")


class UnsupportedYamlError(ValueError):
    """Valid YAML syntax that falls outside the subset minimal_yaml.py
    supports (see the module docstring). This differs from a normal parse
    error: this syntax is CORRECT by the YAML standard, this minimal parser
    just chooses not to handle it — so the reason must be reported clearly
    right here, instead of silently parsing it wrong and surfacing as a
    confusing error in some other field."""


def _reject_block_scalar(value, raw_line):
    if _BLOCK_SCALAR_RE.match(value.strip()):
        raise UnsupportedYamlError(
            f"block scalar YAML ('{value.strip()}') is not supported by minimal_yaml.py "
            f"(line: {raw_line!r}) — use a one-line string in quotes instead of "
            "a multi-line '>'/'|' block."
        )


def _strip_comment(line):
    in_quote = None
    for i, ch in enumerate(line):
        if in_quote:
            if ch == in_quote:
                in_quote = None
        elif ch in ('"', "'"):
            in_quote = ch
        elif ch == "#":
            return line[:i]
    return line


def _parse_scalar(s):
    s = s.strip()
    if s == "" or s == "~" or s.lower() == "null":
        return None
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if inner == "":
            return []
        return [_parse_scalar(part) for part in inner.split(",")]
    if re.match(r"^-?\d+$", s):
        return int(s)
    if re.match(r"^-?\d+\.\d+$", s):
        return float(s)
    return s


def _parse_mapping(lines, idx, indent, result=None):
    if result is None:
        result = {}
    while idx < len(lines) and lines[idx][0] == indent and not lines[idx][1].startswith("- "):
        key, _, val = lines[idx][1].partition(":")
        key = key.strip()
        val = val.strip()
        idx += 1
        if val == "":
            if idx < len(lines) and lines[idx][0] > indent:
                child_indent = lines[idx][0]
                value, idx = _parse_block(lines, idx, child_indent)
                result[key] = value
            else:
                result[key] = None
        else:
            _reject_block_scalar(val, lines[idx - 1][1])
            result[key] = _parse_scalar(val)
    return result, idx


def _parse_sequence(lines, idx, indent):
    result = []
    while idx < len(lines) and lines[idx][0] == indent and lines[idx][1].startswith("- "):
        item = lines[idx][1][2:].strip()
        if item == "":
            idx += 1
            if idx < len(lines) and lines[idx][0] > indent:
                value, idx = _parse_block(lines, idx, lines[idx][0])
            else:
                value = None
            result.append(value)
        elif ":" in item:
            # The first key is on the same line as the dash; the next keys
            # of the same dict are normal mapping lines, indented two more
            # spaces (and can be nested even deeper, for example `when:`/`activate:`).
            key, _, val = item.partition(":")
            initial = {key.strip(): (None if val.strip() == "" else _parse_scalar(val))}
            idx += 1
            mapping, idx = _parse_mapping(lines, idx, indent + 2, initial)
            result.append(mapping)
        else:
            _reject_block_scalar(item, lines[idx][1])
            result.append(_parse_scalar(item))
            idx += 1
    return result, idx


def _parse_block(lines, idx, indent):
    if idx >= len(lines) or lines[idx][0] < indent:
        return None, idx
    if lines[idx][1].startswith("- "):
        return _parse_sequence(lines, idx, indent)
    return _parse_mapping(lines, idx, indent)


def safe_load(text):
    lines = []
    for raw in text.splitlines():
        line = _strip_comment(raw).rstrip()
        if line.strip() == "" or line.strip() == "---":
            continue
        indent = len(line) - len(line.lstrip(" "))
        lines.append((indent, line.strip()))
    if not lines:
        return None
    value, _ = _parse_block(lines, 0, lines[0][0])
    return value
