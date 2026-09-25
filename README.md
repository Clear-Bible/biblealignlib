# biblealignlib

Biblica's Python code for working with Bible alignment data from
https://github.com/Clear-Bible/Alignments .

This code is ©2024-2026 by [Biblica, Inc](http://biblica.com) and is
licensed under [CC BY SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).


## Installing

This project uses [uv](https://docs.astral.sh/uv/) for dependency and
environment management.

```
uv sync                # install runtime + dev dependencies
uv sync --group docs   # additionally install documentation dependencies
```

Common commands (run inside the project root):

```
uv run pytest          # run the test suite
uv run mypy            # run type checks
uv run mkdocs serve    # preview the docs locally
```

## Installing extra dependencies

### eflomal

`eflomal` is a tool for automated alignment. It is not installed by
default because it requires a custom build.

On macOS, you may need to install additional dependencies before installing:

```
brew install llvm libomp
```

You'll need to override the `CFLAGS` and `LDFLAGS` environment variables before installing `eflomal`:

```
export CFLAGS="-Xpreprocessor -fopenmp -I${HOMEBREW_PREFIX}/opt/libomp/include -Ofast -march=native -Wall --std=gnu99 -Wno-unused-function -g"
export LDFLAGS="-Xpreprocessor -fopenmp -L${HOMEBREW_PREFIX}/opt/libomp/lib -lm -lomp"
uv pip install eflomal
```

