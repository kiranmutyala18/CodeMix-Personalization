import pytest

from codemix_bench.english import hunspell_available

needs_hunspell = pytest.mark.skipif(not hunspell_available(), reason="hunspell en_US not installed")
