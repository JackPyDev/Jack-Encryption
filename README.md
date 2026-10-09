<div align="center">

# 🔐 JACK

### Just Another Code Keeper

**Python Source Code Protection & Obfuscation**

`JACK / @vcxah / v3.0`

[![PyPI](https://img.shields.io/pypi/v/jaack?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/jaack/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey?style=for-the-badge)](#-platform-support)

**Turn Python source code into an obfuscated native payload with a lightweight Python loader.**

[Installation](#-installation) · [Usage](#-usage) · [How It Works](#-how-it-works) · [Known Issues](#-known-issues)

</div>

---

## 📖 About JACK

**JACK (Just Another Code Keeper)** is a Python source code protection and obfuscation tool designed to make direct source-code inspection more difficult.

JACK transforms a plain `.py` file through a multi-stage build pipeline involving **AST transformation, Cython transpilation, C++ compilation, code diversification, and payload packing**. The resulting native payload is embedded in a Python loader that uses the separate `jaack` package at runtime.

JACK is intended for developers who want an additional layer of protection for their Python applications and proprietary code.

### ✨ Highlights

- **Native compilation:** Translates Python code through Cython and C++ into a native shared library.
- **Multi-layer obfuscation:** Combines dummy code, opaque predicates, and instruction substitution.
- **Packed payload:** Applies XOR transformation, zlib compression, and Base64 encoding.
- **Lightweight loader:** Uses the `jaack` package to decode and load the protected payload.
- **Optimized compilation:** Uses aggressive compiler optimization and symbol visibility flags.
- **Animated CLI:** Features the NOCTRA banner, animated visual effects, and a typing-style subtitle.

> **Important:** JACK increases the difficulty of inspecting protected code; it does not guarantee confidentiality or make reverse engineering impossible.

---

## 🚀 Features

| Feature | Description |
|---|---|
| AST transformation | Wraps the `__main__` execution block in a `run_protected()` function. |
| Cython transpilation | Converts the transformed Python source into C/C++-compatible native code. |
| Dummy code injection | Adds 400 dummy functions and 100 fake data arrays. |
| Opaque predicates | Injects 4–8 opaque predicate instances per function using 10 types. |
| Instruction substitution | Applies 3–6 instruction substitutions per function using 10 styles. |
| Native compilation | Builds a shared native module with optimization and symbol-hiding flags. |
| Payload packing | Applies XOR transformation, zlib compression at level 9, and Base64 encoding. |
| In-memory loading | The `jaack` loader is designed to decode and load the native module in memory. |
| Terminal interface | Provides an animated CLI with the NOCTRA banner and visual effects. |
| Multiple platforms | Supports Linux, Windows, and macOS, subject to compatible compiler toolchains. |

---

## 🛠️ Installation

### Prerequisites

Before using JACK, ensure that you have:

- **Python 3.8 or newer**
- **pip**
- **Cython**
- A compatible C++ compiler
- The JACK source repository if you want to run the complete build tool

### Option 1: Install the loader package

Install `jaack` from PyPI:

```bash
pip install jaack
