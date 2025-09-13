# tests/test_cli.py
import io
import argparse as ap
import pathlib
from typing import Any
import pydantic
import pytest
from mkast import cfg
import mkast.cli as cli


class FakeConfig(cfg.FileConfig):
    # Minimal stand-in for your real Config for unit tests

    # For resolve_config merge tracking
    origin: str | None = None
    seen: list[str] = pydantic.Field(default_factory=list)

    # Capture what config_from_args fed into model_validate
    last_input: dict | None = None

    @classmethod
    def model_validate(cls, obj: Any,         *,
                       strict: bool | None = None,
                       from_attributes: bool | None = None,
                       context: Any | None = None,
                       by_alias: bool | None = None,
                       by_name: bool | None = None):
        # Record exactly what the helper tried to validate
        cls.last_input = dict(obj)
        # Only keep fields this fake model knows about
        fields = {k: v for k, v in obj.items() if k in cls.model_fields}
        return cls(**fields)


def test_prop_ok_basic():
    assert cli.prop("name:type") == ("name", "type")


def test_prop_ok_colon_in_type():
    # Only the first ':' splits
    assert cli.prop("foo:map<string:int>") == ("foo", "map<string:int>")


def test_prop_error_missing_separator():
    with pytest.raises(ap.ArgumentTypeError):
        cli.prop("notValid")


def test_config_from_args_filters_none_and_calls_model_validate(monkeypatch):
    # Patch Config to our FakeConfig
    monkeypatch.setattr(cli, "Config", FakeConfig)

    # Namespace with some None that should be filtered out,
    # plus keys with dashes that your real model likely handles via aliases.
    ns = ap.Namespace(
        target="c",
        **{"known-types": {"X"}, "common-props": [("k", "v")], "ignore_me": None}
    )

    cfg = cli.config_from_args(ns)
    assert isinstance(cfg, FakeConfig)
    # None-valued key should not be passed through
    assert FakeConfig.last_input is not None and "ignore_me" not in FakeConfig.last_input
    # The keys are passed as-is (including dashed names)
    assert FakeConfig.last_input.get("known-types") == {"X"}
    assert FakeConfig.last_input.get("common-props") == [("k", "v")]
    assert cfg.target == "c"


def test_resolve_config_relative_chain(monkeypatch, tmp_path):
    # Layout:
    # tmp/a/config.yaml  -> extends: sub/b.yaml
    # tmp/a/sub/b.yaml   -> extends: ../c.yaml
    # tmp/a/c.yaml       -> extends: null
    a_dir = tmp_path / "a"
    sub_dir = a_dir / "sub"
    sub_dir.mkdir(parents=True)
    file_a = a_dir / "config.yaml"
    file_b = sub_dir / "b.yaml"
    file_c = a_dir / "c.yaml"
    for f in (file_a, file_b, file_c):
        f.write_text("# stub\n", encoding="utf-8")

    extends_map = {
        str(file_a.resolve()): "sub/b.yaml",
        str(file_b.resolve()): "../c.yaml",
        str(file_c.resolve()): None,
    }

    def fake_load_cfg_file(path: pathlib.Path):
        path = pathlib.Path(path).resolve()
        return FakeConfig(extends=extends_map[str(path)], origin=str(path))

    def fake_merge_cfg(cfg: FakeConfig, cfgF: FakeConfig) -> FakeConfig:
        # Accumulate the origin of each loaded config into `seen`
        return FakeConfig(
            seen=[*cfg.seen, cfgF.origin] if cfgF.origin else [*cfg.seen],
            # carry over last extends just to keep loop logic happy
            extends=cfgF.extends,
        )

    monkeypatch.setattr(cli, "Config", FakeConfig)
    monkeypatch.setattr(cli, "load_cfg_file", fake_load_cfg_file)
    monkeypatch.setattr(cli, "merge_cfg", fake_merge_cfg)

    start_cfg = FakeConfig()
    out = cli.resolve_config(start_cfg, file_a.resolve())
    assert isinstance(out, FakeConfig)

    assert out.seen == [str(file_a.resolve()), str(file_b.resolve()), str(file_c.resolve())]


def test_resolve_config_cycle_breaks(monkeypatch, tmp_path):
    # A -> B -> A (cycle)
    a_dir = tmp_path / "a"
    a_dir.mkdir(parents=True)
    file_a = a_dir / "config.yaml"
    file_b = a_dir / "b.yaml"
    for f in (file_a, file_b):
        f.write_text("# stub\n", encoding="utf-8")

    extends_map = {
        str(file_a.resolve()): "b.yaml",
        str(file_b.resolve()): "config.yaml",  # cycle
    }

    def fake_load_cfg_file(path: pathlib.Path):
        path = pathlib.Path(path).resolve()
        return FakeConfig(extends=extends_map[str(path)], origin=str(path))

    def fake_merge_cfg(cfg: FakeConfig, cfgF: FakeConfig) -> FakeConfig:
        return FakeConfig(
            seen=[*cfg.seen, cfgF.origin] if cfgF.origin else [*cfg.seen],
            extends=cfgF.extends,
        )

    monkeypatch.setattr(cli, "Config", FakeConfig)
    monkeypatch.setattr(cli, "load_cfg_file", fake_load_cfg_file)
    monkeypatch.setattr(cli, "merge_cfg", fake_merge_cfg)

    out = cli.resolve_config(FakeConfig(), file_a.resolve())
    # Should process A then B, then stop due to visited set
    assert isinstance(out, FakeConfig)
    assert out.seen == [str(file_a.resolve()), str(file_b.resolve())]


def test_load_input_single_document(monkeypatch):
    # Patch Config to our FakeConfig so model_validate exists
    monkeypatch.setattr(cli, "Config", FakeConfig)

    data = io.StringIO("root: null\n")
    cfg_from_input, ast = cli.load_input(data)
    assert cfg_from_input is None
    assert ast == {"root": None}


def test_load_input_two_documents(monkeypatch):
    monkeypatch.setattr(cli, "Config", FakeConfig)

    yaml_text = """\
target: c
---
Root:
  child: null
"""
    cfg_from_input, ast = cli.load_input(io.StringIO(yaml_text))
    assert isinstance(cfg_from_input, FakeConfig)
    assert cfg_from_input.target == "c"
    assert ast == {"Root": {"child": None}}


def test_load_input_zero_documents_raises():
    with pytest.raises(ValueError) as ei:
        cli.load_input(io.StringIO(""))
    # Be explicit about the message to catch regressions
    assert "expected 1 or 2 documents, not 0" in str(ei.value)


def test_load_input_three_documents_raises():
    text = """\
---
{}
---
{}
---
{}
"""
    with pytest.raises(ValueError) as ei:
        cli.load_input(io.StringIO(text))
    assert "expected 1 or 2 documents, not 3" in str(ei.value)


def test_load_input_invalid_ast_raises_validation_error(monkeypatch):
    monkeypatch.setattr(cli, "Config", FakeConfig)
    # Second doc is invalid for AstUnionNodeModel (list instead of mapping)
    text = """\
target: c
---
- not
- a
- mapping
"""
    with pytest.raises(pydantic.ValidationError):
        cli.load_input(io.StringIO(text))
