"""Test code in burrito.__init__"""

from biblealignlib import burrito


class TestInit:
    """Test imports and varialbes."""

    def test_init(self) -> None:
        """Test initialization."""
        assert burrito.DATAPATH.parent == burrito.ROOT
