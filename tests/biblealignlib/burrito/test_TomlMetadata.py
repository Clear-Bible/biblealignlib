"""Test TomlMetadata."""

from pathlib import Path

import pytest

from biblealignlib.burrito import TomlMetadata

TOMLTEXT = """
[source]

identifier = "SBLGNT"
copyright = "Copyright 2010 by the Society of Biblical Literature and Logos Bible Software."
license = "CC-BY-4.0"
url = "https://sblgnt.com/"

[source.metadata]
copyright = "Copyright (c) 2023 by Clear Bible, Inc."
license = "CC-BY 4.0"

[target]

identifier = "RV09"
license = "Public domain"
name.eng = "Reina Valera 1909"
url = "https://ebible.org/find/details.php?id=spaRV1909"

[target.metadata]
copyright = "Copyright (c) 2023 by BiblioNexus"
license = "CC-BY 4.0"
tokenization = "LatinWordTokenizer"

[alignment]

identifier = "SBLGNT-RV09-manual"
format = "Scripture Burrito v0.3"
copyright = "Copyright 2024 by BiblioNexus"
license = "CC-BY-4.0"
process = "manual"
scope = "NT"
team = "BiblioNexus"
"""


@pytest.fixture(scope="module")
def tomlpath(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Return the path of a TOML file with all five sections."""
    path = tmp_path_factory.mktemp("toml") / "SBLGNT-RV09-manual.toml"
    path.write_text(TOMLTEXT, encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def tomlmeta(tomlpath: Path) -> TomlMetadata:
    """Return a TomlMetadata instance."""
    return TomlMetadata.from_path(tomlpath)


class TestTomlMetadata:
    """Test TomlMetadata()."""

    def test_source(self, tomlmeta: TomlMetadata) -> None:
        """Test that the source text section is read."""
        assert tomlmeta.source.identifier == "SBLGNT"
        assert tomlmeta.source.license == "CC-BY-4.0"
        assert tomlmeta.source.url == "https://sblgnt.com/"
        assert "Society of Biblical Literature" in tomlmeta.source.copyright

    def test_target(self, tomlmeta: TomlMetadata) -> None:
        """Test that the target text section is read, including localized names."""
        assert tomlmeta.target.identifier == "RV09"
        assert tomlmeta.target.license == "Public domain"
        assert tomlmeta.target.name == {"eng": "Reina Valera 1909"}

    def test_alignment(self, tomlmeta: TomlMetadata) -> None:
        """Test that the alignment section is read."""
        assert tomlmeta.alignment.identifier == "SBLGNT-RV09-manual"
        assert tomlmeta.alignment.team == "BiblioNexus"
        assert tomlmeta.alignment.scope == "NT"
        assert tomlmeta.alignment.process == "manual"

    def test_rights_over_the_text_and_over_its_tokenization_are_distinct(
        self, tomlmeta: TomlMetadata
    ) -> None:
        """Test that a text's rights and its tokenization's rights are kept apart.

        A source text, the tokenization of that text, and the alignment
        may each be held by a different party. Collapsing them loses the
        attribution the licences require.
        """
        assert "Society of Biblical Literature" in tomlmeta.source.copyright
        assert "Clear Bible" in tomlmeta.source.metadata.copyright
        assert "BiblioNexus" in tomlmeta.target.metadata.copyright
        assert "BiblioNexus" in tomlmeta.alignment.copyright

    def test_tokenization_is_recorded(self, tomlmeta: TomlMetadata) -> None:
        """Test that the tokenizer that produced the target ids is read."""
        assert tomlmeta.target.metadata.tokenization == "LatinWordTokenizer"

    def test_absent_sections_are_empty_not_missing(self, tmp_path: Path) -> None:
        """Test that a file with no sections yields empty values rather than raising."""
        path = tmp_path / "empty.toml"
        path.write_text("", encoding="utf-8")
        meta = TomlMetadata.from_path(path)
        assert meta.source.identifier == ""
        assert meta.target.metadata.tokenization == ""
        assert meta.alignment.team == ""

    def test_unparseable_file_raises_naming_the_path(self, tmp_path: Path) -> None:
        """Test that a malformed TOML names the file it could not read.

        Four sidecars in the published corpus carry a duplicated key and
        cannot be parsed, so this path is real rather than theoretical.
        """
        path = tmp_path / "duplicate.toml"
        path.write_text('[source]\nlicense = "a"\nlicense = "b"\n', encoding="utf-8")
        with pytest.raises(ValueError, match="duplicate.toml"):
            TomlMetadata.from_path(path)
