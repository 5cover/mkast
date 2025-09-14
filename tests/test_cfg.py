from mkast.cfg import Config, Modifier

def test_merge_cfg_simple_fields():
    base = Config(target='python', root='base_root')
    new = Config(target='typescript', root=None)
    merged = base + new
    assert merged.target == 'typescript'
    assert merged.root == 'base_root'

def test_merge_cfg_sets_and_sequences():
    base = Config(known_types={'A', 'B'}, imports=['x', 'y'])
    new = Config(known_types={'B', 'C'}, imports=['z'])
    merged = base + new
    assert set(merged.known_types) == {'A', 'B', 'C'}
    assert list(merged.imports) == ['x', 'y', 'z']

def test_merge_cfg_dicts_and_modifiers():
    base = Config(common_props={'a': '1'}, modifiers={'?': Modifier(type='opt')})
    new = Config(common_props={'b': '2'}, modifiers={'*': Modifier(type='star')})
    merged = base + new
    assert merged.common_props == {'a': '1', 'b': '2'}
    assert set(merged.modifiers.keys()) == {'?', '*'}

def test_merge_cfg_nested_models():
    base = Config(modifiers={'': Modifier(type='base', must='yes')})
    new = Config(modifiers={'': Modifier(type='new', must=None)})
    merged = base + new
    assert merged.modifiers[''].type == 'new'
    assert merged.modifiers[''].must == 'yes'

def test_merge_cfg_none_handling():
    base = Config(root='toor')
    new = Config(root=None)
    merged = base + new
    assert merged.root == 'toor'

def test_merge_cfg_empty_new():
    base = Config(target='python', known_types={'A'})
    new = Config()
    merged = base + new
    assert merged.target == 'python'
    assert set(merged.known_types) == {'A'}