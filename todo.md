# Todo

- [ ] Pattern domain (handles replacement of $1, $2..., escaping)
- [ ] Type options (abstracts type and modifier separation)
- [ ] Modifier stackability (C# nullable reference types cannot be stacked)

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
