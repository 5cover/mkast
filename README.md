# AST Generator

Generate an AST data structure from a language-agnostic description expressed in YAML.

[Input schema](https://raw.githubusercontent.com/5cover/ast-gen/refs/heads/main/schemas/nodes.json)

## Usage

`./ast.py < input.yml`

## Features

An AST is expressed as a tree of nodes. There are two kinds of nodes: **class** nodes, having **properties**, are product types, while **union** nodes represent the sum type of other nodes.

### Properties

Properties have a type which is checked to exist.

Types marked as *Do Not Touch* (by prepending it with an equal sign `=`) are not checked and their casing is not altered.

Multiple `?`, `+`, and `*` suffixes can be appended for optionals, non-empty lists and lists respectively.

## Casing

The casing of identifiers is altered to match the conventions of the target language.

Agnostically, snake_case is used and expected as input.
