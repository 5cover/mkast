# AST Generator

Generate an AST data structure from a language-agnostic description expressed in YAML.

[Input schema](https://raw.githubusercontent.com/5cover/ast-gen/refs/heads/main/schemas/nodes.json)

[Config schema](https://raw.githubusercontent.com/5cover/ast-gen/refs/heads/main/schemas/config.json)

## Usage

`./ast.py < input.yml`

## Input

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

Configuration optioons:

name|type|default value|description
-|-|-|-
known_types|array of identifier|[]|Types to always consider defined
root|identifier||If defined, adds an outer union node wrapping everything
common_props|map of identifier &rarr; identifier|{}|Common properties present in every product node
target|"csharp" or "agnostic"|(value is required)|Output languages.
namespace|identifier||Namespace or package name
assert|code snippet||Expands to an assertion statmeent. $1 is replaced by the boolean expression to assert
imports|array of identifier|[]|Importations to add to the top of the file
union|snippet|depends on target language|Expands to the declaration of an union node. $1 is replaced by the name of the node.
product|snippet|depends on the target language|Expands to the declaration of an product node. $1 is replaced by the name of the node.
modifiers|map of modifier char &rarr; modifier (see decicated section)|{}|Modifiers are used to hook into the type names and expressions emitted.

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

Types marked as *Do Not Touch* (by pefixing them with an equal sign `=`) are not checked and their casing is not altered.

Multiple `?`, `+`, and `*` suffixes can be appended for optionals, non-empty lists and lists respectively.

### Casing

The casing of identifiers is altered to match the conventions of the target language.

Agnostically, snake_case is used and expected as input.
