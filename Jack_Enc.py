import ast
import base64
import os
import random
import shutil
import string
import subprocess
import sys
import tempfile
import zlib
import time
import math
from pathlib import Path
from datetime import datetime

import pyfiglet
from rich.console import Console
from rich.text import Text

MODULE_NAME = "jack_payload"
XOR_KEY = b"\x5a\x3c\x91\xe7\x2b\x44\xf8\x1d\x62\xa9\x07\x8e\xf1\x53\xbb\x20"

console = Console()

TEXT = "NOCTRA"
SUBTITLE = "JACK  /  @vcxah  /  v3.0"

PALETTES = [
    ["#C8A2E8", "#B57EDC", "#DDA0DD", "#E8C8E8", "#F5E6F5", "#E8D0F0", "#B57EDC", "#9B59B6", "#DDA0DD"],
    ["#7EC8E3", "#5BA8D4", "#A0D8E8", "#C8E8F5", "#E0F5FF", "#B0D8E8", "#5BA8D4", "#3498DB", "#A0D8E8"],
    ["#E87EB5", "#D45BA8", "#E8A0C8", "#F5C8E0", "#FFE0F0", "#E8B0D0", "#D45BA8", "#C71585", "#F5C8E0"],
    ["#E8C87E", "#D4A85B", "#E8D8A0", "#F5E8C8", "#FFF5E0", "#E8D8B0", "#D4A85B", "#DAA520", "#F5E8C8"],
    ["#7EE8A2", "#5BD48A", "#A0E8B8", "#C8F5D8", "#E0FFE8", "#B0E8C8", "#5BD48A", "#3CB371", "#C8F5D8"],
    ["#E87E7E", "#D45B5B", "#E8A0A0", "#F5C8C8", "#FFE0E0", "#E8B0B0", "#D45B5B", "#DC143C", "#F5C8C8"],
    ["#7E9EE8", "#5B7ED4", "#A0B8E8", "#C8D8F5", "#E0E8FF", "#B0C8E8", "#5B7ED4", "#4169E1", "#C8D8F5"],
    ["#E8A87E", "#D4865B", "#E8C0A0", "#F5D8C8", "#FFE8E0", "#E8C8B0", "#D4865B", "#FF8C00", "#F5D8C8"],
]

RAINBOW = [
    "#FF0000", "#FF4500", "#FFA500", "#FFD700", "#FFFF00",
    "#ADFF2F", "#00FF00", "#00FA9A", "#00FFFF", "#00BFFF",
    "#0000FF", "#4B0082", "#8A2BE2", "#DA70D6", "#FF1493",
    "#FF0000",
]

PALETTE_SWITCH_FRAMES = 120
PALETTE_BLEND_FRAMES = 20

SUBTITLE_COLOR_START = "#8A2BE2"
SUBTITLE_COLOR_END   = "#DA70D6"

STAR_CHARS = ["✦", "✧", "⋆", "✩"]
STAR_COLORS = [
    "#FFFFFF", "#E0E0FF", "#FFFFAA",
    "#FFD700", "#AAD4FF", "#DDAAFF",
    "#BA55D3", "#DDA0DD",
]

SPARKLE_CHARS = ["✦", "✧", "⋆", "✩", "*", "•"]

EFFECT_MODES = ["rainbow_flow", "palette_wave", "shimmer_blast", "pulse_burst"]

SUBTYPE_TYPE_SPEED = 2
SUBTYPE_HOLD_FRAMES = 150
SUBTYPE_DELETE_SPEED = 3
SUBTYPE_PAUSE_FRAMES = 20

PROMPT_TEXT = "Press ENTER to continue  ▸"


def _rnd_alpha(rng, n):
    return "".join(rng.choice(string.ascii_lowercase) for _ in range(n))


def _rnd_hex(rng, n):
    return "".join(rng.choice("0123456789abcdef") for _ in range(n))


def _rnd_ident(rng):
    prefixes = [
        "get", "set", "process", "handle", "load", "save", "read", "write",
        "parse", "build", "make", "check", "verify", "validate", "compute",
        "encode", "decode", "hash", "sign", "init", "alloc", "copy", "find",
        "search", "match", "filter", "transform", "convert", "extract",
        "merge", "split", "join", "scan", "update", "apply", "run", "exec",
        "start", "stop", "open", "close", "push", "pull", "send", "recv",
        "encrypt", "decrypt", "sign_", "verify_", "digest", "cipher",
        "compress", "expand", "serialize", "parse_", "unpack", "pack",
        "encode_", "decode_", "build_", "make_", "check_", "init_",
    ]
    suffixes = ["data", "buf", "block", "chunk", "stream", "input", "output",
                "state", "ctx", "item", "list", "node", "tree", "map", "table",
                "cache", "pool", "queue", "stack", "vec", "arr", "ptr", "obj",
                "info", "meta", "config", "session", "token", "key", "secret",
                "header", "body", "packet", "frame", "slot", "entry"]
    return rng.choice(prefixes) + "_" + rng.choice(suffixes) + "_" + _rnd_hex(rng, 4)


OPAQUE_PATTERNS = [
    lambda rng, v: f"(({v} * ({v} + 1)) % 2 == 0)",
    lambda rng, v: f"((({v} ^ 0x{rng.randint(1,0xFFFFFFFF):08x}ULL) * 0x{rng.randint(1,0xFFFFFFFF):08x}ULL) != 0x{rng.randint(1,0xFFFFFFFF):08x}ULL)",
    lambda rng, v: f"(({v} | 0x{rng.randint(1,0xFFFFFFFF):08x}ULL) >= {v})",
    lambda rng, v: f"(({v} & 0x{rng.randint(1,0xFFFFFFFF):08x}ULL) <= {v})",
    lambda rng, v: f"(({v} * 2 / 2) == {v})",
    lambda rng, v: f"(({v} + 0x{rng.randint(1,0xFFFFFFFF):08x}ULL) != 0x{rng.randint(1,0xFFFFFFFF):08x}ULL)",
    lambda rng, v: f"((({v} << 3) >> 3) == {v})",
    lambda rng, v: f"((({v} ^ {v}) == 0))",
    lambda rng, v: f"(({v} - {v}) == 0)",
    lambda rng, v: f"((({v} + 1) * ({v} + 1)) >= ({v} * {v}))",
]


def _opaque_cond(rng, var):
    pat = rng.choice(OPAQUE_PATTERNS)
    return pat(rng, var)


def _ins_sub(rng, var, const):
    style = rng.randint(0, 9)
    if style == 0:
        return f"({var} - (-0x{const:04x}))"
    elif style == 1:
        return f"(({var} << 1) - {var} + 0x{const:04x})"
    elif style == 2:
        k1 = rng.randint(1, 0xFFFF)
        return f"(({var} ^ 0x{k1:04x}) + 0x{const:04x} ^ 0x{k1:04x})"
    elif style == 3:
        k1 = rng.randint(1, 0xFF)
        return f"({var} + 0x{const:04x} + 0x{k1:02x} - 0x{k1:02x})"
    elif style == 4:
        return f"(({var} * 2) / 2 + 0x{const:04x})"
    elif style == 5:
        return f"((({var} >> 1) << 1) + ({var} & 1) + 0x{const:04x})"
    elif style == 6:
        k1 = rng.randint(1, 0xFFFF)
        return f"(({var} ^ 0x{k1:04x}) ^ 0x{k1:04x} + 0x{const:04x})"
    elif style == 7:
        return f"({var} + ({var} >> 32) + 0x{const:04x})"
    elif style == 8:
        k1 = rng.randint(1, 0xFFFF)
        return f"(({var} | 0x{k1:04x}) & 0x{0xFFFF ^ k1:04x} | ({var} & 0x{k1:04x}) + 0x{const:04x})"
    else:
        return f"(({var} + 0x{const:04x}) ^ 0x0)"


def generate_dummy(num_funcs=400, num_arrays=100):
    rng = random.Random()
    L = []
    L.append("#include <cstdint>")
    L.append("#include <cstring>")
    L.append("#include <cstdio>")
    L.append("#include <cstdlib>")
    L.append("")
    L.append("namespace _internal {")
    L.append("")

    L.append("static const std::uint32_t _tbl_a[16] = {")
    L.append("    " + ", ".join(f"0x{rng.randint(0,0xFFFFFFFF):08x}U" for _ in range(16)) + ",")
    L.append("};")
    L.append("")
    L.append("static const std::uint64_t _tbl_b[8] = {")
    L.append("    " + ", ".join(f"0x{rng.randint(0,0xFFFFFFFFFFFFFFFF):016x}ULL" for _ in range(8)) + ",")
    L.append("};")
    L.append("")
    L.append("static const std::uint8_t _tbl_c[64] = {")
    L.append("    " + ", ".join(f"0x{rng.randint(0,0xFF):02x}" for _ in range(64)) + ",")
    L.append("};")
    L.append("")

    calls = []

    for i in range(num_funcs):
        nm = _rnd_ident(rng) + "_" + str(i)
        style = i % 12
        opaque_count = rng.randint(4, 8)
        insub_count = rng.randint(3, 6)

        if style == 0:
            L.append(f"__attribute__((noinline, used)) static std::uint64_t {nm}(const std::uint8_t* data, std::size_t len) {{")
            L.append(f"    std::uint64_t h = 0x{rng.randint(0,0xFFFFFFFFFFFFFFFF):016x}ULL;")
            L.append("    for (std::size_t i = 0; i < len; ++i) {")
            L.append("        h ^= (std::uint64_t)data[i];")
            L.append(f"        h = (h << {rng.randint(3,15)}) - h;")
            L.append(f"        h *= 0x{rng.randint(1,0xFFFFFFFFFFFFFFFF):016x}ULL;")
            L.append(f"        h ^= h >> {rng.randint(13, 47)};")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "h")
                L.append(f"        if ({cond}) {{ h ^= 0x{rng.randint(1,0xFFFFFFFF):08x}ULL; }} else {{ h += 0x{rng.randint(1,0xFFFFFFFF):08x}ULL; }}")
            for _ in range(insub_count):
                c = rng.randint(1, 0xFFF)
                L.append(f"        h = {_ins_sub(rng, 'h', c)};")
            L.append("    }")
            L.append("    return h;")
            L.append("}")
            arg_src = f'"{_rnd_alpha(rng, rng.randint(8, 32))}"'
            arg_len = rng.randint(8, 32)
            calls.append((nm, "hash", arg_src, arg_len))

        elif style == 1:
            L.append(f"__attribute__((noinline, used)) static int {nm}(std::uint8_t* buf, std::size_t len, std::uint8_t key) {{")
            L.append("    for (std::size_t i = 0; i < len; ++i) {")
            L.append("        buf[i] = (std::uint8_t)((buf[i] ^ key) + _tbl_c[i & 63]);")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "buf[i]")
                L.append(f"        if ({cond}) {{ buf[i] ^= 0x{rng.randint(1,0xFF):02x}; }} else {{ buf[i] += 0x{rng.randint(1,0xFF):02x}; }}")
            L.append("    }")
            L.append("    return (int)len;")
            L.append("}")
            calls.append((nm, "xor", None, rng.randint(8, 32)))

        elif style == 2:
            L.append(f"__attribute__((noinline, used)) static std::uint32_t {nm}(std::uint32_t x, std::uint32_t y) {{")
            L.append(f"    x = (x << {rng.randint(5, 15)}) | (x >> {rng.randint(17, 27)});")
            L.append(f"    y = (y << {rng.randint(3, 13)}) | (y >> {rng.randint(19, 29)});")
            L.append(f"    x = x + y - y;")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "x")
                L.append(f"    if ({cond}) {{ x ^= 0x{rng.randint(1,0xFFFFFFFF):08x}U; }}")
            for _ in range(insub_count):
                c = rng.randint(1, 0xFFF)
                L.append(f"    x = (std::uint32_t){_ins_sub(rng, 'x', c)};")
            L.append(f"    return (x ^ y) * 0x{rng.randint(1,0xFFFFFFFF):08x}U + _tbl_a[x & 15];")
            L.append("}")
            calls.append((nm, "u32", None, 0))

        elif style == 3:
            L.append(f"__attribute__((noinline, used)) static int {nm}(const char* s) {{")
            L.append("    int h = 0;")
            L.append("    while (*s) {")
            L.append(f"        h = h * {rng.randint(31, 131)} + (unsigned char)*s;")
            L.append("        ++s;")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "h")
                L.append(f"        if ({cond}) {{ h ^= 0x{rng.randint(1,0xFFFF):04x}; }}")
            L.append("    }")
            L.append("    return h;")
            L.append("}")
            arg_src = f'"{_rnd_alpha(rng, rng.randint(8, 32))}"'
            calls.append((nm, "str", arg_src, 0))

        elif style == 4:
            L.append(f"__attribute__((noinline, used)) static void {nm}(std::uint64_t* st, int rounds) {{")
            L.append("    for (int r = 0; r < rounds; ++r) {")
            L.append("        st[0] ^= st[1] + _tbl_b[r & 7];")
            L.append(f"        st[1] = (st[1] << {rng.randint(7, 23)}) | (st[1] >> {rng.randint(41, 57)});")
            L.append("        st[1] += st[0];")
            L.append(f"        st[0] = (st[0] * 0x{rng.randint(1,0xFFFFFFFFFFFFFFFF):016x}ULL) ^ st[1];")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "st[0]")
                L.append(f"        if ({cond}) {{ st[1] ^= 0x{rng.randint(1,0xFFFFFFFF):08x}ULL; }}")
            for _ in range(insub_count):
                c = rng.randint(1, 0xFFF)
                L.append(f"        st[0] = {_ins_sub(rng, 'st[0]', c)};")
            L.append("    }")
            L.append("}")
            calls.append((nm, "state", None, rng.randint(3, 8)))

        elif style == 5:
            L.append(f"__attribute__((noinline, used)) static int {nm}(std::uint32_t* arr, int n) {{")
            L.append("    for (int i = 1; i < n; ++i) {")
            L.append("        arr[i] = (arr[i] ^ arr[i-1]) + _tbl_a[i & 15];")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "arr[i]")
                L.append(f"        if ({cond}) {{ arr[i] += 0x{rng.randint(1,0xFFFF):04x}U; }}")
            L.append("    }")
            L.append("    return n;")
            L.append("}")
            calls.append((nm, "arr", None, rng.randint(4, 8)))

        elif style == 6:
            L.append(f"__attribute__((noinline, used)) static std::uint64_t {nm}(std::uint64_t x) {{")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "x")
                L.append(f"    if ({cond}) {{")
                L.append(f"        x = x ^ 0x{rng.randint(1,0xFFFFFFFF):08x}ULL;")
                L.append("    } else {")
                L.append(f"        x = x + 0x{rng.randint(1,0xFFFFFFFF):08x}ULL;")
                L.append("    }")
            for _ in range(insub_count):
                c = rng.randint(1, 0xFFF)
                L.append(f"    x = {_ins_sub(rng, 'x', c)};")
            L.append(f"    x = (x << {rng.randint(3,11)}) - x;")
            L.append("    return x;")
            L.append("}")
            calls.append((nm, "u64", None, 0))

        elif style == 7:
            L.append(f"__attribute__((noinline, used)) static std::uint64_t {nm}(std::uint64_t x, std::uint64_t y) {{")
            L.append(f"    std::uint64_t r = 0;")
            L.append(f"    for (int i = 0; i < {rng.randint(4,12)}; ++i) {{")
            L.append(f"        x = (x ^ y) + _tbl_b[i & 7];")
            L.append(f"        y = (y << {rng.randint(3,17)}) | (y >> {rng.randint(47,61)});")
            L.append("        r ^= x ^ y;")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "r")
                L.append(f"        if ({cond}) {{ r ^= 0x{rng.randint(1,0xFFFFFFFF):08x}ULL; }}")
            L.append("    }")
            L.append("    return r;")
            L.append("}")
            calls.append((nm, "u64x2", None, 0))

        elif style == 8:
            L.append(f"__attribute__((noinline, used)) static std::uint64_t {nm}(const std::uint8_t* d, std::size_t n, std::uint64_t seed) {{")
            L.append(f"    std::uint64_t h = seed ^ 0x{rng.randint(1,0xFFFFFFFFFFFFFFFF):016x}ULL;")
            L.append("    for (std::size_t i = 0; i < n; ++i) {")
            L.append("        h += (std::uint64_t)d[i] * _tbl_b[i & 7];")
            L.append(f"        h = (h ^ (h >> {rng.randint(13, 41)})) * 0x{rng.randint(1,0xFFFFFFFFFFFFFFFF):016x}ULL;")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "h")
                L.append(f"        if ({cond}) {{ h ^= 0x{rng.randint(1,0xFFFFFFFF):08x}ULL; }}")
            for _ in range(insub_count):
                c = rng.randint(1, 0xFFF)
                L.append(f"        h = {_ins_sub(rng, 'h', c)};")
            L.append("    }")
            L.append("    return h;")
            L.append("}")
            arg_src = f'"{_rnd_alpha(rng, rng.randint(8, 32))}"'
            arg_len = rng.randint(8, 32)
            calls.append((nm, "hashseed", arg_src, arg_len))

        elif style == 9:
            L.append(f"__attribute__((noinline, used)) static std::uint64_t {nm}(std::uint64_t x) {{")
            L.append(f"    std::uint64_t acc = 0;")
            L.append(f"    for (int i = 0; i < {rng.randint(6,16)}; ++i) {{")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "x")
                L.append(f"        if ({cond}) {{")
                L.append(f"            acc ^= (x << {rng.randint(3,13)}) - x;")
                L.append(f"        }} else {{")
                L.append(f"            acc ^= x + _tbl_b[i & 7];")
                L.append(f"        }}")
            for _ in range(insub_count):
                c = rng.randint(1, 0xFFF)
                L.append(f"        x = {_ins_sub(rng, 'x', c)};")
            L.append(f"        x = (x ^ acc) * 0x{rng.randint(1,0xFFFFFFFFFFFFFFFF):016x}ULL;")
            L.append("    }")
            L.append("    return acc;")
            L.append("}")
            calls.append((nm, "u64loop", None, 0))

        elif style == 10:
            L.append(f"__attribute__((noinline, used)) static std::uint64_t {nm}(std::uint64_t x) {{")
            L.append(f"    std::uint64_t a = x;")
            L.append(f"    std::uint64_t b = x >> 32;")
            L.append(f"    for (int i = 0; i < {rng.randint(5,12)}; ++i) {{")
            L.append(f"        a = a + b - b;")
            L.append(f"        b = (b << {rng.randint(3,11)}) - b;")
            L.append(f"        a ^= b * 0x{rng.randint(1,0xFFFFFFFF):08x}ULL;")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "a")
                L.append(f"        if ({cond}) {{ a ^= 0x{rng.randint(1,0xFFFFFFFF):08x}ULL; }}")
            L.append("    }")
            L.append("    return a ^ b;")
            L.append("}")
            calls.append((nm, "u64sub", None, 0))

        else:
            L.append(f"__attribute__((noinline, used)) static std::uint64_t {nm}(const std::uint8_t* d, std::size_t n) {{")
            L.append(f"    std::uint64_t h = 0x{rng.randint(1,0xFFFFFFFFFFFFFFFF):016x}ULL;")
            L.append(f"    for (std::size_t i = 0; i < n; ++i) {{")
            for _ in range(opaque_count):
                cond = _opaque_cond(rng, "h")
                L.append(f"        if ({cond}) {{")
                L.append(f"            h = h * 0x{rng.randint(1,0xFFFFFFFFFFFFFFFF):016x}ULL + d[i];")
                L.append(f"        }} else {{")
                L.append(f"            h ^= d[i] * 0x{rng.randint(1,0xFFFFFFFF):08x}ULL;")
                L.append(f"        }}")
            for _ in range(insub_count):
                c = rng.randint(1, 0xFFF)
                L.append(f"        h = {_ins_sub(rng, 'h', c)};")
            L.append(f"        h = (h ^ (h >> {rng.randint(13, 41)}));")
            L.append("    }")
            L.append("    return h;")
            L.append("}")
            arg_src = f'"{_rnd_alpha(rng, rng.randint(8, 32))}"'
            arg_len = rng.randint(8, 32)
            calls.append((nm, "hash2", arg_src, arg_len))

        L.append("")

    for i in range(num_arrays):
        sz = 2048
        data = bytes(rng.randint(0, 255) for _ in range(sz))
        nm = f"_d_{_rnd_alpha(rng, 4)}_{i}"
        L.append(f'__attribute__((used, section(".rodata"))) static const std::uint8_t {nm}[{sz}] = {{')
        for j in range(0, sz, 16):
            chunk = data[j:j + 16]
            L.append("    " + ", ".join(f"0x{b:02x}" for b in chunk) + ",")
        L.append("};")
        L.append("")

    L.append("}  // namespace _internal")
    L.append("")

    L.append("__attribute__((constructor)) static void _init_internal() {")
    L.append("    volatile std::uint64_t acc = 0x1234567890ABCDEFULL;")
    L.append("    std::uint8_t buf[256];")
    L.append("    std::memset(buf, 0, sizeof(buf));")

    for nm, kind, arg, val in calls:
        if kind == "hash":
            L.append(f"    acc ^= _internal::{nm}((const std::uint8_t*){arg}, {val});")
        elif kind == "xor":
            L.append(f"    acc ^= (std::uint64_t)_internal::{nm}(buf, {val}, (std::uint8_t)acc);")
        elif kind == "u32":
            L.append(f"    acc ^= (std::uint64_t)_internal::{nm}((std::uint32_t)acc, (std::uint32_t)(acc >> 32));")
        elif kind == "str":
            L.append(f"    acc ^= (std::uint64_t)_internal::{nm}({arg});")
        elif kind == "state":
            L.append(f"    {{ std::uint64_t st[2] = {{acc, 0xDEADBEEFCAFEBABEULL}}; _internal::{nm}(st, {val}); acc ^= st[0] ^ st[1]; }}")
        elif kind == "arr":
            L.append(f"    {{ std::uint32_t arr[16] = {{0}}; arr[0] = (std::uint32_t)acc; _internal::{nm}(arr, {val}); acc ^= arr[0] ^ arr[1]; }}")
        elif kind == "u64":
            L.append(f"    acc ^= _internal::{nm}(acc);")
        elif kind == "u64x2":
            L.append(f"    acc ^= _internal::{nm}(acc, acc >> 32);")
        elif kind == "hashseed":
            L.append(f"    acc ^= _internal::{nm}((const std::uint8_t*){arg}, {val}, acc);")
        elif kind == "u64loop":
            L.append(f"    acc ^= _internal::{nm}(acc);")
        elif kind == "u64sub":
            L.append(f"    acc ^= _internal::{nm}(acc);")
        elif kind == "hash2":
            L.append(f"    acc ^= _internal::{nm}((const std::uint8_t*){arg}, {val});")

    L.append("    (void)acc;")
    L.append("    (void)buf;")
    L.append("}")
    L.append("")

    return "\n".join(L)


def find_compiler():
    for name in ("clang", "gcc", "cc", "c++"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError("no compiler")


def python_library_candidates():
    import sysconfig
    result = []
    cfg = sysconfig.get_config_vars()
    libdir = cfg.get("LIBDIR")
    instsoname = cfg.get("INSTSONAME")
    ldversion = cfg.get("LDVERSION") or cfg.get("VERSION") or f"{sys.version_info.major}.{sys.version_info.minor}"
    if libdir:
        result.append(os.path.join(libdir, f"libpython{ldversion}.so"))
        if instsoname:
            result.append(os.path.join(libdir, instsoname))
    prefixes = [sys.prefix, sys.base_prefix, os.path.dirname(sys.executable), os.path.dirname(os.path.dirname(sys.executable))]
    names = [f"libpython{ldversion}.so", f"libpython{sys.version_info.major}.{sys.version_info.minor}.so", "libpython.so"]
    for prefix in prefixes:
        if not prefix:
            continue
        for root in (prefix, os.path.join(prefix, "lib"), os.path.join(prefix, "lib64"), os.path.join(prefix, "libs")):
            for name in names:
                result.append(os.path.join(root, name))
    seen = set()
    output = []
    for item in result:
        item = os.path.abspath(item)
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


def find_python_library():
    for path in python_library_candidates():
        if os.path.isfile(path):
            return path
    return None


def compile_cython(source):
    import sysconfig
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pyx = td / f"{MODULE_NAME}.pyx"
        cfile = td / f"{MODULE_NAME}.cpp"
        header = (
            "# cython: language_level=3\n"
            "# cython: boundscheck=False\n"
            "# cython: wraparound=False\n"
            "# cython: initializedcheck=False\n"
            "# cython: cdivision=True\n"
        )
        pyx.write_text(header + source, encoding="utf-8")
        cython = shutil.which("cython") or shutil.which("cython3")
        if not cython:
            raise RuntimeError("cython not found")
        r = subprocess.run(
            [cython, "-3", "--cplus", "--fast-fail", "-o", str(cfile), str(pyx)],
            cwd=td, capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr or r.stdout)
        if not cfile.exists():
            raise RuntimeError("no cpp generated")

        cpp_text = cfile.read_text(encoding="utf-8", errors="ignore")
        bloat = generate_dummy()
        idx = cpp_text.find("#include")
        if idx >= 0:
            eol = cpp_text.find("\n", idx)
            cpp_text = cpp_text[:eol + 1] + "\n" + bloat + "\n" + cpp_text[eol + 1:]
        else:
            cpp_text = bloat + "\n" + cpp_text
        cfile.write_text(cpp_text, encoding="utf-8")

        ext = ".pyd" if sys.platform == "win32" else ".so"
        so = td / f"{MODULE_NAME}{ext}"

        include = []
        inc = sysconfig.get_path("include")
        pinc = sysconfig.get_path("platinclude")
        if inc:
            include.append(f"-I{inc}")
        if pinc and pinc != inc:
            include.append(f"-I{pinc}")

        compiler = find_compiler()
        python_lib = find_python_library()

        base = [
            compiler, "-O3", "-fPIC", "-shared", "-std=c++17",
            "-fvisibility=hidden", "-fvisibility-inlines-hidden",
            "-fno-ident", "-fno-asynchronous-unwind-tables",
            "-fno-unwind-tables", "-fno-stack-protector",
            "-fomit-frame-pointer", "-fdata-sections",
            "-ffunction-sections", "-fno-exceptions",
            "-fno-rtti", "-w",
            *include,
            "-Wl,--gc-sections", "-Wl,-s", "-Wl,-E",
            "-o", str(so), str(cfile),
        ]

        attempts = []
        if python_lib:
            attempts.append(base + ["-Wl,--no-as-needed", python_lib])
        attempts.append(base)

        last_error = ""
        for cmd in attempts:
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0 and so.exists():
                strip = shutil.which("strip")
                if strip:
                    subprocess.run([strip, "-s", str(so)], capture_output=True)
                return so.read_bytes()
            last_error = r.stderr or r.stdout or "compile failed"
        raise RuntimeError(last_error)


def wrap_entry(source):
    tree = ast.parse(source)
    new_body = []
    run_body = None
    for node in tree.body:
        if (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "__name__"
            and len(node.test.ops) == 1
            and isinstance(node.test.ops[0], ast.Eq)
            and len(node.test.comparators) == 1
            and isinstance(node.test.comparators[0], ast.Constant)
            and node.test.comparators[0].value == "__main__"
        ):
            run_body = node.body
        else:
            new_body.append(node)
    if run_body is None:
        run_body = [ast.Pass()]
    run_fn = ast.FunctionDef(
        name="run_protected",
        args=ast.arguments(
            posonlyargs=[], args=[], vararg=None, kwonlyargs=[],
            kw_defaults=[], kwarg=None, defaults=[]
        ),
        body=run_body,
        decorator_list=[],
        returns=None,
        type_comment=None,
    )
    new_body.append(run_fn)
    tree.body = new_body
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def encode_payload(binary):
    data = bytes(binary)
    xored = bytes(data[i] ^ XOR_KEY[i % 16] for i in range(len(data)))
    comp = zlib.compress(xored, 9)
    b64 = base64.b64encode(comp).decode("ascii")
    return b64


def build_loader(b64_string, output):
    loader = (
        "import jaack\n"
        f"D = {b64_string!r}\n"
        "Jack()\n"
    )
    Path(output).write_text(loader, encoding="utf-8")


def get_terminal_size():
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


def cursor_home():
    sys.stdout.write("\033[H")


def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    r, g, b = [max(0, min(255, int(c))) for c in rgb]
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def get_current_palette(frame):
    idx = (frame // PALETTE_SWITCH_FRAMES) % len(PALETTES)
    next_idx = (idx + 1) % len(PALETTES)
    t_in_cycle = frame % PALETTE_SWITCH_FRAMES
    blend_start = PALETTE_SWITCH_FRAMES - PALETTE_BLEND_FRAMES
    if t_in_cycle < blend_start:
        blend = 0.0
    else:
        blend = (t_in_cycle - blend_start) / PALETTE_BLEND_FRAMES
    blend = blend * blend * (3 - 2 * blend)
    current = PALETTES[idx]
    nxt = PALETTES[next_idx]
    blended = []
    for c1, c2 in zip(current, nxt):
        r1, g1, b1 = hex_to_rgb(c1)
        r2, g2, b2 = hex_to_rgb(c2)
        blended.append(rgb_to_hex(lerp((r1, g1, b1), (r2, g2, b2), blend)))
    return blended


def get_gradient_color(pos, palette):
    n = len(palette) - 1
    scaled = pos * n
    i = int(scaled)
    t = scaled - i
    if i >= n:
        i = n - 1
        t = 1.0
    c1 = hex_to_rgb(palette[i])
    c2 = hex_to_rgb(palette[i + 1])
    return rgb_to_hex(lerp(c1, c2, t))


def get_rainbow_color(pos):
    n = len(RAINBOW) - 1
    scaled = pos * n
    i = int(scaled) % n
    t = scaled - int(scaled)
    c1 = hex_to_rgb(RAINBOW[i])
    c2 = hex_to_rgb(RAINBOW[i + 1])
    return rgb_to_hex(lerp(c1, c2, t))


def brighten(hex_color, factor=1.6):
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex((r * factor, g * factor, b * factor))


FONT_CANDIDATES = ["banner3-D", "epic", "big", "block", "standard"]


def build_best_fit_art(text, target_width, target_height):
    best = None
    for font in FONT_CANDIDATES:
        try:
            art = pyfiglet.figlet_format(text, font=font)
            lines = [l for l in art.split("\n") if l.strip()]
            if not lines:
                continue
            w = max(len(l) for l in lines)
            h = len(lines)
            if w <= target_width - 2 and h <= target_height - 10:
                return lines, font, w, h
            if best is None or w < best[2]:
                best = (lines, font, w, h)
        except Exception:
            continue
    if best:
        return best
    art = pyfiglet.figlet_format(text, font="standard")
    lines = [l for l in art.split("\n") if l.strip()]
    return lines, "standard", max(len(l) for l in lines), len(lines)


def get_fade_factor(frame, total_frames):
    p = frame / max(1, total_frames - 1)
    if p < 0.15:
        return p / 0.15
    elif p > 0.85:
        return (1.0 - p) / 0.15
    return 1.0


def glow_pulse(frame, speed=0.08, min_g=0.95, max_g=1.35):
    t = (math.sin(frame * speed) + 1) / 2
    return min_g + (max_g - min_g) * t


def get_effect_mode(frame):
    return EFFECT_MODES[(frame // 63) % len(EFFECT_MODES)]


def get_sweep_direction(frame):
    return 1 if (frame // 80) % 2 == 0 else -1


def fast_sweep_band(col_idx, max_width, frame, speed=0.12):
    direction = get_sweep_direction(frame)
    sweep_raw = (frame * speed) % 1.6
    if direction < 0:
        sweep_pos = 1.6 - sweep_raw
    else:
        sweep_pos = sweep_raw
    pos = col_idx / max_width
    dist = (pos - sweep_pos) * direction
    head_band = 0.14
    tail_len = 0.40
    multiplier = 1.0
    if abs(dist) < head_band:
        multiplier = 1.0 + (1.0 - abs(dist) / head_band) * 2.2
    elif -tail_len < dist < 0:
        tail_t = 1.0 - (abs(dist) / tail_len)
        multiplier = 1.0 + tail_t * 0.9
    return multiplier


def color_flow_left_right(col_idx, max_width, frame, speed=0.03):
    base = col_idx / max_width
    shift = (frame * speed) % 1.0
    return (base + shift) % 1.0


def pulse_burst(col_idx, max_width, frame, speed=0.14):
    center = max_width / 2
    dist = abs(col_idx - center) / max(1, center)
    t = (math.sin(frame * speed - dist * 3.5) + 1) / 2
    return 0.7 + t * 0.9


def letter_breathing(row_idx, col_idx, frame):
    seed = (row_idx * 73 + col_idx * 131) % 1000
    speed = 0.12 + (seed % 5) * 0.03
    phase = (seed % 17) / 17.0 * math.pi * 2
    t = (math.sin(frame * speed + phase) + 1) / 2
    return 0.75 + t * 0.85


def horizontal_slow_wave(col_idx, max_width, frame):
    pos = col_idx / max_width
    wave = math.sin(frame * 0.035 + pos * math.pi * 2.0)
    return int(round(wave * 3))


def intro_letter_alpha(col_idx, max_width, frame, reveal_frames=40):
    if frame >= reveal_frames:
        return 1.0
    center = max_width / 2
    dist = abs(col_idx - center) / max(1, center)
    appear_frame = dist * (reveal_frames * 0.85)
    p = (frame - appear_frame) / (reveal_frames * 0.15)
    return max(0.0, min(1.0, p))


class Star:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.char = random.choice(STAR_CHARS)
        self.color = random.choice(STAR_COLORS)
        self.blink_speed = random.uniform(0.15, 0.35)
        self.phase = random.uniform(0, math.pi * 2)
        self.min_bright = random.uniform(0.15, 0.30)
        self.max_bright = random.uniform(1.0, 1.4)

    def get_brightness(self, frame):
        val = (math.sin(frame * self.blink_speed + self.phase) + 1) / 2
        return self.min_bright + val * (self.max_bright - self.min_bright)

    def get_render(self, frame):
        brightness = self.get_brightness(frame)
        color = brighten(self.color, brightness)
        return (self.char, f"bold {color}")


class Sparkle:
    def __init__(self, x, y, palette_color):
        self.x = x
        self.y = y
        self.char = random.choice(SPARKLE_CHARS)
        self.color = palette_color
        self.life = random.randint(10, 20)
        self.age = 0

    def update(self):
        self.age += 1
        return self.age < self.life

    def get_render(self):
        t = self.age / self.life
        if t < 0.25:
            factor = t / 0.25
        elif t > 0.75:
            factor = (1.0 - t) / 0.25
        else:
            factor = 1.0
        color = brighten(self.color, 1.3 + factor * 1.2)
        return (self.char, f"bold {color}")


class StarField:
    def __init__(self, text_x, text_y, text_w, text_h, term_w, term_h,
                 star_count=30):
        self.stars = []
        x1, y1 = text_x, text_y
        x2, y2 = text_x + text_w, text_y + text_h
        pad_x, pad_y = 6, 6
        zones = []
        if y1 - pad_y > 0:
            zones.append((0, max(0, y1 - pad_y), term_w, y1))
        if y2 + pad_y < term_h:
            zones.append((0, y2 + 1, term_w, min(term_h, y2 + pad_y)))
        if x1 - pad_x > 0:
            zones.append((0, max(0, y1 - 2), max(1, x1 - 2), min(term_h, y2 + 2)))
        if x2 + pad_x < term_w:
            zones.append((x2 + 2, max(0, y1 - 2), term_w, min(term_h, y2 + 2)))
        zones.append((max(0, x1 - 2), max(0, y1 - 1), min(term_w, x2 + 2), min(term_h, y2 + 1)))
        if not zones:
            zones.append((0, 0, term_w, term_h))
        occupied = set()
        attempts = 0
        while len(self.stars) < star_count and attempts < 2000:
            attempts += 1
            zone = random.choice(zones)
            zx1, zy1, zx2, zy2 = zone
            if zx2 <= zx1 or zy2 <= zy1:
                continue
            x = random.randint(zx1, zx2 - 1)
            y = random.randint(zy1, zy2 - 1)
            if (x, y) in occupied:
                continue
            occupied.add((x, y))
            self.stars.append(Star(x, y))

    def get_render_map(self, frame):
        return {(s.x, s.y): s.get_render(frame) for s in self.stars}


class SparkleManager:
    def __init__(self):
        self.sparkles = []
        self.spawn_cooldown = 0

    def update(self, art_lines, text_start_x, text_start_y, max_width,
               palette, frame):
        self.sparkles = [s for s in self.sparkles if s.update()]
        self.spawn_cooldown -= 1
        if self.spawn_cooldown <= 0 and art_lines:
            self.spawn_cooldown = 1
            for _ in range(3):
                row_idx = random.randint(0, len(art_lines) - 1)
                line = art_lines[row_idx]
                if not line.strip():
                    continue
                letter_cols = [i for i, c in enumerate(line) if c != " "]
                if not letter_cols:
                    continue
                col_idx = random.choice(letter_cols)
                dx = random.choice([-2, -1, 1, 2, 2])
                dy = random.choice([-1, 0, 1])
                if dy == 0 and abs(dx) < 2:
                    continue
                sx = text_start_x + col_idx + dx
                sy = text_start_y + row_idx + dy
                if sx < 0 or sy < 0:
                    continue
                color = get_gradient_color(random.random(), palette)
                self.sparkles.append(Sparkle(sx, sy, color))

    def get_render_map(self):
        result = {}
        for s in self.sparkles:
            result[(s.x, s.y)] = s.get_render()
        return result


class RandomEventManager:
    def __init__(self):
        self.events = []
        self.cooldown = 50
        self.recent = []

    def update(self, frame, term_w, term_h, art_lines,
               text_start_x, text_start_y):
        alive = []
        for ev in self.events:
            ev["age"] += 1
            if ev["age"] <= ev["duration"]:
                alive.append(ev)
            else:
                self.recent.append(ev["type"])
                self.recent = self.recent[-3:]
        self.events = alive

        self.cooldown -= 1
        if self.cooldown <= 0:
            self._spawn_event(term_w, term_h, art_lines,
                              text_start_x, text_start_y, frame)
            self.cooldown = random.randint(45, 60)

    def _spawn_event(self, term_w, term_h, art_lines,
                     text_start_x, text_start_y, frame):
        choices = ["shooting_star", "letter_flash", "pulse_ring", "full_flash"]
        choices = [c for c in choices if c not in self.recent[-1:]] or choices
        ev_type = random.choice(choices)

        if ev_type == "shooting_star":
            start_x = random.randint(0, max(1, term_w // 3))
            start_y = random.randint(0, max(1, term_h // 4))
            self.events.append({
                "type": "shooting_star",
                "age": 0,
                "duration": 30,
                "start_x": start_x,
                "start_y": start_y,
                "color": random.choice(["#FFFFFF", "#FFFFAA", "#AAD4FF", "#FFD700"]),
                "char": random.choice(["✦", "✧", "★", "☄"]),
            })

        elif ev_type == "letter_flash":
            if not art_lines:
                return
            positions = []
            attempts = 0
            while len(positions) < 6 and attempts < 40:
                attempts += 1
                r = random.randint(0, len(art_lines) - 1)
                line = art_lines[r]
                letter_cols = [i for i, c in enumerate(line) if c != " "]
                if not letter_cols:
                    continue
                c = random.choice(letter_cols)
                positions.append((c, r))
            self.events.append({
                "type": "letter_flash",
                "age": 0,
                "duration": 14,
                "positions": positions,
            })

        elif ev_type == "pulse_ring":
            self.events.append({
                "type": "pulse_ring",
                "age": 0,
                "duration": 35,
            })

        elif ev_type == "full_flash":
            self.events.append({
                "type": "full_flash",
                "age": 0,
                "duration": 8,
            })

    def get_text_modifier(self, col_idx, row_idx, max_width, art_lines):
        mult = 1.0
        for ev in self.events:
            t = ev["age"] / max(1, ev["duration"])
            if ev["type"] == "letter_flash":
                if (col_idx, row_idx) in ev["positions"]:
                    if t < 0.5:
                        mult *= (2.5 - t * 2.0)
                    else:
                        mult *= (1.5 - (t - 0.5) * 1.0)
            elif ev["type"] == "pulse_ring":
                center = max_width / 2
                dist = abs(col_idx - center) / max(1, center)
                ring_pos = t * 1.2
                ring_width = 0.15
                d = abs(dist - ring_pos)
                if d < ring_width:
                    mult *= (1.0 + (1.0 - d / ring_width) * 1.8)
            elif ev["type"] == "full_flash":
                if t < 0.5:
                    mult *= (1.0 + t * 2.0 * 2)
                else:
                    mult *= (3.0 - (t - 0.5) * 2 * 2)
        return mult

    def get_overlay_cells(self, term_w, term_h):
        cells = []
        for ev in self.events:
            t = ev["age"] / max(1, ev["duration"])
            if ev["type"] == "shooting_star":
                sx = ev["start_x"] + int(t * term_w * 0.7)
                sy = ev["start_y"] + int(t * term_h * 0.7)
                ch = ev["char"]
                color = ev["color"]
                brightness = 1.6 if t < 0.7 else 1.6 * (1.0 - (t - 0.7) / 0.3)
                if 0 <= sx < term_w and 0 <= sy < term_h:
                    cells.append((sx, sy, ch, f"bold {brighten(color, brightness)}"))
                for i in range(1, 5):
                    tx = sx - i
                    ty = sy - i
                    if 0 <= tx < term_w and 0 <= ty < term_h:
                        tail_b = brightness * (1.0 - i / 5)
                        tail_color = brighten(color, tail_b)
                        tail_char = random.choice(["·", "∙", "•", "*"])
                        cells.append((tx, ty, tail_char, f"bold {tail_color}"))
        return cells


class TypingSubtitle:
    def __init__(self, text):
        self.text = text
        self.visible = 0
        self.state = "typing"
        self.hold_counter = 0
        self.pause_counter = 0

    def update(self):
        if self.state == "typing":
            self.visible += SUBTYPE_TYPE_SPEED
            if self.visible >= len(self.text):
                self.visible = len(self.text)
                self.state = "holding"
                self.hold_counter = 0
        elif self.state == "holding":
            self.hold_counter += 1
            if self.hold_counter >= SUBTYPE_HOLD_FRAMES:
                self.state = "deleting"
        elif self.state == "deleting":
            self.visible -= SUBTYPE_DELETE_SPEED
            if self.visible <= 0:
                self.visible = 0
                self.state = "pausing"
                self.pause_counter = 0
        elif self.state == "pausing":
            self.pause_counter += 1
            if self.pause_counter >= SUBTYPE_PAUSE_FRAMES:
                self.state = "typing"

    def get_visible_text(self):
        return self.text[:int(self.visible)]


def get_clock_string():
    now = datetime.now()
    return now.strftime("%H:%M:%S")


def draw_clock(grid, term_w, palette):
    clock = get_clock_string()
    x_start = term_w - len(clock) - 2
    if x_start < 0:
        return
    color = get_gradient_color(0.5, palette)
    for i, ch in enumerate(clock):
        x = x_start + i
        if 0 <= x < term_w and grid[0]:
            grid[0][x] = (ch, f"bold {color}")


def compute_char_color(col_idx, row_idx, max_width, frame, palette, mode):
    pos = col_idx / max_width
    if mode == "rainbow_flow":
        flow_pos = color_flow_left_right(col_idx, max_width, frame, speed=0.05)
        color = get_rainbow_color(flow_pos)
        band = fast_sweep_band(col_idx, max_width, frame, speed=0.12)
        return brighten(color, band)
    elif mode == "palette_wave":
        flow_pos = color_flow_left_right(col_idx, max_width, frame, speed=0.04)
        flow_pos += math.sin(frame * 0.18 + row_idx * 0.5) * 0.09
        flow_pos = flow_pos % 1.0
        color = get_gradient_color(flow_pos, palette)
        band = fast_sweep_band(col_idx, max_width, frame, speed=0.12)
        return brighten(color, band)
    elif mode == "shimmer_blast":
        flow_pos = color_flow_left_right(col_idx, max_width, frame, speed=0.03)
        color = get_gradient_color(flow_pos, palette)
        band = fast_sweep_band(col_idx, max_width, frame, speed=0.16)
        return brighten(color, band * 1.2)
    elif mode == "pulse_burst":
        flow_pos = color_flow_left_right(col_idx, max_width, frame, speed=0.035)
        color = get_gradient_color(flow_pos, palette)
        pulse = pulse_burst(col_idx, max_width, frame, speed=0.14)
        return brighten(color, pulse)
    flow_pos = color_flow_left_right(col_idx, max_width, frame, speed=0.04)
    return get_gradient_color(flow_pos, palette)


def render_frame(art_lines, frame, total_frames, star_field, sparkle_mgr,
                 event_mgr, typing_sub, top_pad=1, art_offset_x=0,
                 reveal_frames=40, show_prompt=False, prompt_frame=0):
    cursor_home()

    term_w, term_h = get_terminal_size()
    extra = 5
    grid_h = max(term_h, len(art_lines) + top_pad + extra + 4)
    grid_w = term_w

    grid = [[(" ", "") for _ in range(grid_w)] for _ in range(grid_h)]

    star_map = star_field.get_render_map(frame)
    for (x, y), (ch, style) in star_map.items():
        if 0 <= x < grid_w and 0 <= y < grid_h:
            grid[y][x] = (ch, style)

    max_width = max(len(l) for l in art_lines) if art_lines else 1
    cycle_frame = frame % total_frames
    fade = get_fade_factor(cycle_frame, total_frames)
    glow = glow_pulse(frame, speed=0.08) * fade

    palette = get_current_palette(frame)
    mode = get_effect_mode(frame)

    text_start_y = top_pad
    text_start_x = art_offset_x

    in_intro = frame < reveal_frames

    event_mgr.update(frame, term_w, term_h, art_lines, text_start_x, text_start_y)

    for row_idx, line in enumerate(art_lines):
        y = text_start_y + row_idx
        if y >= grid_h:
            break
        for col_idx, ch in enumerate(line):
            if ch == " ":
                continue
            wave_dx = horizontal_slow_wave(col_idx, max_width, frame)
            x = text_start_x + col_idx + wave_dx
            if x >= grid_w or x < 0:
                continue

            if in_intro:
                alpha = intro_letter_alpha(col_idx, max_width, frame, reveal_frames)
                if alpha <= 0:
                    continue
                intro_mult = alpha
            else:
                intro_mult = 1.0

            color = compute_char_color(col_idx, row_idx, max_width, frame, palette, mode)

            if not in_intro:
                breath = letter_breathing(row_idx, col_idx, frame)
            else:
                breath = 1.0

            ev_mult = event_mgr.get_text_modifier(col_idx, row_idx, max_width, art_lines)

            color = brighten(color, glow * intro_mult * breath * ev_mult)
            grid[y][x] = (ch, f"bold {color}")

    for (x, y, ch, style) in event_mgr.get_overlay_cells(term_w, term_h):
        if 0 <= x < grid_w and 0 <= y < grid_h:
            grid[y][x] = (ch, style)

    sparkle_mgr.update(art_lines, text_start_x, text_start_y, max_width, palette, frame)
    sparkle_map = sparkle_mgr.get_render_map()
    for (x, y), (ch, style) in sparkle_map.items():
        if 0 <= x < grid_w and 0 <= y < grid_h:
            if grid[y][x][0] == " ":
                grid[y][x] = (ch, style)

    sub_y = text_start_y + len(art_lines) + 1
    sub_text = typing_sub.get_visible_text()
    sub_len_full = len(SUBTITLE)
    sub_x = max(0, (term_w - sub_len_full) // 2)

    for i, ch in enumerate(sub_text):
        if ch == " ":
            continue
        x = sub_x + i
        if x >= grid_w or sub_y >= grid_h:
            break
        color = compute_char_color(i, 0, sub_len_full, frame, palette, mode)
        t = i / max(1, sub_len_full - 1)
        base = lerp(hex_to_rgb(SUBTITLE_COLOR_START),
                    hex_to_rgb(SUBTITLE_COLOR_END), t)
        c_rgb = hex_to_rgb(color)
        mixed = rgb_to_hex(lerp(c_rgb, base, 0.25))
        grid[sub_y][x] = (ch, f"bold {mixed}")

    if typing_sub.state in ("typing", "holding", "deleting"):
        cursor_x = sub_x + len(sub_text)
        if cursor_x < grid_w and sub_y < grid_h:
            if (frame // 6) % 2 == 0:
                cursor_color = get_gradient_color(0.5, palette)
                grid[sub_y][cursor_x] = ("▊", f"bold {cursor_color}")

    if len(sub_text) >= sub_len_full - 1:
        underline_y = sub_y + 1
        if underline_y < grid_h:
            for i in range(sub_len_full + 6):
                x = sub_x - 3 + i
                if x < 0 or x >= grid_w:
                    continue
                t = i / max(1, (sub_len_full + 6) - 1)
                edge_fade = max(0.15, 1.0 - abs(t - 0.5) * 2)
                color = compute_char_color(i, 1, sub_len_full + 6, frame, palette, mode)
                r, g, b = hex_to_rgb(color)
                faded = rgb_to_hex((r * edge_fade, g * edge_fade, b * edge_fade))
                grid[underline_y][x] = ("─", faded)

    if show_prompt:
        prompt_y = sub_y + 3
        if prompt_y < grid_h:
            prompt_x = max(0, (term_w - len(PROMPT_TEXT)) // 2)
            pulse = (math.sin(prompt_frame * 0.15) + 1) / 2
            for i, ch in enumerate(PROMPT_TEXT):
                x = prompt_x + i
                if x >= grid_w:
                    break
                if ch == " ":
                    continue
                t = i / max(1, len(PROMPT_TEXT) - 1)
                base_color = get_gradient_color(t, palette)
                bright = brighten(base_color, 1.0 + pulse * 1.2)
                grid[prompt_y][x] = (ch, f"bold {bright}")

    draw_clock(grid, term_w, palette)

    output = []
    for y in range(grid_h):
        line = Text()
        for x in range(grid_w):
            ch, style = grid[y][x]
            line.append(ch, style=style if style else None)
        output.append(line)

    console.print(*output, sep="\n", end="")
    sys.stdout.flush()


def build_star_field(art_w, art_h, top_pad, art_offset_x,
                     term_w, term_h, star_count=30):
    return StarField(
        text_x=art_offset_x, text_y=top_pad,
        text_w=art_w, text_h=art_h,
        term_w=term_w, term_h=term_h, star_count=star_count,
    )


def play_intro(art_lines, star_field, sparkle_mgr, event_mgr, typing_sub,
               top_pad, art_offset_x, reveal_frames=40, fps=25):
    for frame in range(reveal_frames):
        render_frame(
            art_lines, frame, reveal_frames + 1,
            star_field, sparkle_mgr, event_mgr, typing_sub,
            top_pad, art_offset_x, reveal_frames=reveal_frames,
        )
        time.sleep(1 / fps)


def play_until_enter(art_lines, star_field, sparkle_mgr, event_mgr,
                     typing_sub, top_pad, art_offset_x, fps=25):
    import threading
    stop_flag = {"stop": False}

    def wait_for_enter():
        try:
            sys.stdin.readline()
        except Exception:
            pass
        stop_flag["stop"] = True

    t = threading.Thread(target=wait_for_enter, daemon=True)
    t.start()

    frame = 40
    while not stop_flag["stop"]:
        render_frame(
            art_lines, frame, 100000,
            star_field, sparkle_mgr, event_mgr, typing_sub,
            top_pad, art_offset_x, reveal_frames=40,
            show_prompt=True, prompt_frame=frame,
        )
        typing_sub.update()
        frame += 1
        time.sleep(1 / fps)


def list_py_files(directory="."):
    try:
        files = [f for f in os.listdir(directory)
                 if f.endswith(".py") and os.path.isfile(os.path.join(directory, f))]
        files.sort()
        return files
    except Exception:
        return []


def simple_file_menu():
    files = list_py_files(".")
    if not files:
        print("No .py files found in current directory.")
        return None

    print()
    print("=" * 50)
    print("  JACK ENCRYPTOR - SELECT FILE")
    print("=" * 50)
    for i, f in enumerate(files, 1):
        print(f"  [{i}] {f}")
    print("  [q] Quit")
    print("=" * 50)

    while True:
        try:
            choice = input("Select file number: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if choice.lower() == "q":
            return None
        try:
            n = int(choice)
            if 1 <= n <= len(files):
                return files[n - 1]
        except ValueError:
            pass
        print("Invalid choice, try again.")


def run_forever_and_build(fps=25, star_count=30):
    term_w, term_h = get_terminal_size()
    art_lines, font_used, art_w, art_h = build_best_fit_art(TEXT, term_w, term_h)
    top_pad = 1
    art_offset_x = max(0, (term_w - art_w) // 2)

    star_field = build_star_field(art_w, art_h, top_pad, art_offset_x,
                                  term_w, term_h, star_count=star_count)
    sparkle_mgr = SparkleManager()
    event_mgr = RandomEventManager()
    typing_sub = TypingSubtitle(SUBTITLE)

    os.system("cls" if os.name == "nt" else "clear")
    hide_cursor()

    try:
        play_intro(art_lines, star_field, sparkle_mgr, event_mgr, typing_sub,
                   top_pad, art_offset_x, reveal_frames=40, fps=fps)
        play_until_enter(art_lines, star_field, sparkle_mgr, event_mgr,
                         typing_sub, top_pad, art_offset_x, fps=fps)
    except KeyboardInterrupt:
        show_cursor()
        return

    show_cursor()
    os.system("cls" if os.name == "nt" else "clear")

    selected_file = simple_file_menu()

    if not selected_file:
        print("No file selected. Exiting.")
        return

    print(f"\nSelected: {selected_file}\n")

    try:
        source = Path(selected_file).read_text(encoding="utf-8")
        compile(source, str(selected_file), "exec")
        obf_source = wrap_entry(source)
        print(f"[1] wrap_entry ({len(source)} -> {len(obf_source)} bytes)")
        native = compile_cython(obf_source)
        native_kb = len(native) / 1024
        print(f"[2] Cython + dummy + opaque + insub -> {native_kb:.0f} KB .so")
        b64_string = encode_payload(native)
        b64_kb = len(b64_string) / 1024
        print(f"[3] XOR + zlib(9) + base64 -> {b64_kb:.0f} KB D")
        output = "protected.py"
        build_loader(b64_string, output)
        print()
        print("JACK CYTHON BUILD")
        print("Source       :", selected_file)
        print(f"Native size  : {native_kb:.1f} KB")
        print(f"D size       : {b64_kb:.1f} KB")
        print(f"Final size   : {Path(output).stat().st_size / 1024:.1f} KB")
        print("Backend      : Cython + C++ + gcc")
        print("Module       :", MODULE_NAME)
        print("Obfuscation  : none")
        print("Dummy        : 400 funcs + 100 arrays")
        print("Opaque       : 4-8 per function")
        print("InsSub       : 3-6 per function")
        print("Beacon       : removed")
        print("D format     : single string")
        print("zlib level   : 9")
        print("Runtime      : jaack._core Jack()")
        print("Output       :", output)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    run_forever_and_build(fps=25, star_count=30)