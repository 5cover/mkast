# Todo

- [ ] instead of visiting on the fly, build a datastructure and revisit. this means we'll be able to query the properties and subnodes of a node when generating it, which will allow for:
    - [ ] smarter code generation (semi-colon body)
    - [ ] mermaid class diagram target
    - [ ] csharp: only strictly necessary interfaces in base type list (currently all parents are added)

- [ ] union node properties: currently, we decide to make a product node if it contains properties (which is why we need root in config to wrap everyting in an interface). this means we cannot have interfaces with properties. solution: use '*' for products and '+' for sum types
- [ ] account for the empty modifier in csharp.py (currently it seems to be ignored)

- [ ] Modifier stackability (C# nullable reference types cannot be stacked)

- [x] Multidocument input support
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
