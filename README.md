# biblealignlib

Biblica's code for working with Bible alignment data from
https://github.com/Clear-Bible/Alignments .

Currently private but we should move toward a future where it's
public. 

## Installing extra dependencies

### eflomal
`eflomal` is specified as an extra, so it is not installed with `poetry install`.

On macOS, you may need to install additional dependencies before installing:

```
brew install llvm libomp
```

You'll need to override the `CFLAGS` and `LDFLAGS` environment variables before installing `eflomal`.

```
poetry shell
export CFLAGS="-Xpreprocessor -fopenmp -I${HOMEBREW_PREFIX}/opt/libomp/include -Ofast -march=native -Wall --std=gnu99 -Wno-unused-function -g"
export LDFLAGS="-Xpreprocessor -fopenmp -L${HOMEBREW_PREFIX}/opt/libomp/lib -lm -lomp"
poetry install -E eflomal
```

