# mkast

[![PyPI version](https://badge.fury.io/py/mkast.svg)](https://badge.fury.io/py/mkast)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mkast)
[![License: Unlicense](https://img.shields.io/badge/License-Unlicense-yellow.svg)](https://opensource.org/license/Unlicense)
![Tests](/mkast/actions/workflows/tests.yml/badge.svg)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

## What is it?

**mkast** is a CLI tool that generates an AST data structure from a language-agnostic description expressed in YAML.

## Usage

Latest schema URLs:

[Input schema](https://raw.githubusercontent.com/5cover/mkast/refs/heads/main/src/mkast/schemas/nodes.json)

[Config schema](https://raw.githubusercontent.com/5cover/mkast/refs/heads/main/src/mkast/schemas/config.json)

The schemas are also shipped in the package and can be imported from there

### Installing

The easiest way is to install **mkast** is from PyPI using pip:

```sh
pip install mkast
```

### Running

`./ast.py < input.yml`

First, import the library.

```python
import mkast
```

#### Input

The input is a YAML file containing one or two documents.

If the input contains two documents, the first document is considered configuration; the second document is considered as the actual input.

An AST is expressed as a tree of nodes. There are two kinds of nodes: **product** nodes, having **properties**, are product types, while **union** nodes represent the sum type of other nodes.

## Configuration

Configuration can be specified at four levels.

1. Individual options
2. First document of a bi-document input
3. `-c` option
4. Defaults

Each level takes precedence over the ones below.

Configuration options:

name|type|default value|description
-|-|-|-
known_types|array of identifier|[]|Types to always consider defined
root|identifier||If defined, adds an outer union node wrapping everything
common_props|map of identifier &rarr; identifier|{}|Common properties present in every product node
target|"csharp" or "agnostic"|(value is required)|Output languages.
namespace|identifier||Namespace or package name
assert|code snippet||Expands to an assertion statement. $1 is replaced by the boolean expression to assert
imports|array of identifier|[]|Importations to add to the top of the file
union|snippet|depends on target language|Expands to the declaration of an union node. $1 is replaced by the name of the node.
product|snippet|depends on the target language|Expands to the declaration of an product node. $1 is replaced by the name of the node.
modifiers|map of modifier char &rarr; modifier (see dedicated section)|{}|Modifiers are used to hook into the type names and expressions emitted.

Modifiers:

name|char|description
-|-|-
one|(empty)|Implicit. Used to wrap every type or apply an invariant everywhere.
optional|?|Optional element
one or more|+|Non-empty list of elements
zero or more|*|List of elements

Modifier code snippets (all optional):

name|expands to|arguments
-|-|-
type|The type name|$1 is replaced by the payload type.
must|A boolean expression that validates the value. Used in combination with assertions.|$1 is replaced by the name of the variable to check.
none_when|A boolean expression that indicates when it is invalid to unwrap the value.|$1 is replaced by name of the variable to check.
unwrap|An expression that yields the payload value. Or, if there are multiple payload values (such as for lists), a boolean expression that is true when all the values satisfy $2.| $1 is replaced by the name of the variable to unwrap. $2, if present, is replaced by the payload validation boolean expression (based on $1).

## Features

### Properties

Properties have a type which is checked to exist.

Types marked as *Do Not Touch* (by prefixing them with an equal sign `=`) are not checked and their casing is not altered.

Multiple `?`, `+`, and `*` suffixes can be appended for optionals, non-empty lists and lists respectively.

### Casing

The casing of identifiers is altered to match the conventions of the target language.

In the agnostic language, snake_case is used and expected as input.

## TODO

- [ ] merge complex configs values from different sources
  - [ ] imports
  - [ ] modifiers

- [ ] instead of visiting on the fly, build a data structure and revisit. this means we'll be able to query the properties and subnodes of a node when generating it, which will allow for:
  - [ ] smarter code generation (semi-colon body)
  - [ ] mermaid class diagram target
  - [ ] csharp: only strictly necessary interfaces in base type list (currently all parents are added)

- [ ] union node properties: currently, we decide to make a product node if it contains properties (which is why we need root in config to wrap everything in an interface). this means we cannot have interfaces with properties. solution: use '*' for products and '+' for sum types
- [ ] account for the empty modifier in csharp.py (currently it seems to be ignored)

- [ ] Modifier stack-ability (C# nullable reference types cannot be stacked)

- [x] Multi-document input support
- [x] Optional root

- [x] Customize target (current config attr is not read)
- [ ] Target-specific options
- [x] Configure modifiers (config is read (untested), but not used)

- [x] read from config file so options can be persisted on a per-project basis
- [x] C# target:
  - [x] Custom namespace
  - [x] Custom common properties
  - [x] Custom root type
- [x] Known type option
- [x] Use argparse
