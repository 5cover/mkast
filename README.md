# AST Generator

Generate an AST data structure from a language-agnostic description expressed in YAML.

[Input schema](https://raw.githubusercontent.com/5cover/ast-gen/refs/heads/main/schemas/nodes.json)

[Config schema](https://raw.githubusercontent.com/5cover/ast-gen/refs/heads/main/schemas/config.json)

## Usage

`./ast.py < input.yml`

## Features

An AST is expressed as a tree of nodes. There are two kinds of nodes: **class** nodes, having **properties**, are product types, while **union** nodes represent the sum type of other nodes.

## Input

The input is a YAML file containing one or two documents.

If the input contains two documents, the first document is considered configuration; the second document is considered as the actual input.

## Configuration

Configuration can be specified at four levels.

1. Individual options
2. `-c` option
3. First document of a bi-document input
4. Defaults

Each level takes precedence over the ones below.

### Properties

Properties have a type which is checked to exist.

Types marked as *Do Not Touch* (by prepending it with an equal sign `=`) are not checked and their casing is not altered.

Multiple `?`, `+`, and `*` suffixes can be appended for optionals, non-empty lists and lists respectively.

## Casing

The casing of identifiers is altered to match the conventions of the target language.

Agnostically, snake_case is used and expected as input.
