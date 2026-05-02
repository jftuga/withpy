# withpy

Batteries-included Swiss-army CLI using only the Python 3.14+ standard library.
No pip, no venv, no third-party dependencies -- just Python.

`withpy` is the Python sibling of [mtool](https://github.com/jftuga/mtool)
(Go, 91 stdlib packages) and
[swiftswiss](https://github.com/jftuga/swiftswiss) (Swift, 23 frameworks).

**Stdlib modules used: 91** | **Subcommands: 51**

## Subcommands

| Command    | Description | Key stdlib modules |
|------------|-------------|---------------------|
| `archive`  | Create/extract/list tar and zip archives | `tarfile`, `zipfile` |
| `bench`    | HTTP load testing with concurrency and stats | `urllib.request`, `concurrent.futures`, `statistics` |
| `calc`     | Safe expression evaluator (no eval) | `ast`, `operator`, `math`, `statistics`, `decimal`, `fractions` |
| `calendar` | Calendars, weekday math, Easter dates | `calendar`, `datetime` |
| `color`    | Color space conversions (RGB/HSL/HSV/HEX) | `colorsys` |
| `compress` | Compress/decompress (gzip, zlib, bz2, lzma) | `gzip`, `zlib`, `bz2`, `lzma` |
| `config`   | Read/write/query INI config files | `configparser` |
| `csv`      | CSV/JSON conversion, filter, select columns | `csv`, `json`, `io` |
| `db`       | SQLite queries on .db or CSV-as-table | `sqlite3`, `csv` |
| `decode`   | Decode data (base64, hex, URL, HTML, ...) | `base64`, `binascii`, `urllib.parse`, `html` |
| `deps`     | Topological sort of dependency graphs | `graphlib`, `json` |
| `diff`     | Compare two files (unified/context/HTML) | `difflib` |
| `dirdiff`  | Recursive directory comparison | `filecmp`, `pathlib` |
| `encode`   | Encode data (base64, hex, URL, HTML, ...) | `base64`, `binascii`, `urllib.parse`, `html` |
| `fetch`    | HTTP client with headers, timing, cookies | `urllib.request`, `http.cookiejar` |
| `find`     | Find files by glob, size, mtime, type | `fnmatch`, `pathlib`, `stat` |
| `generate` | Generate UUIDs, tokens, and passwords | `secrets`, `uuid`, `string` |
| `glob`     | Expand glob patterns and list matches | `glob` |
| `hash`     | Compute file hashes (MD5, SHA, CRC32, ...) | `hashlib`, `hmac`, `zlib` |
| `hexdump`  | Hex + ASCII dump of binary data | (builtins) |
| `info`     | System information (OS, CPU, network, disk) | `platform`, `socket`, `shutil`, `uuid` |
| `inspect`  | TLS certificate inspection and DNS lookup | `ssl`, `socket`, `datetime` |
| `ipaddr`   | IP/CIDR math (contains, overlap, split) | `ipaddress` |
| `iter`     | Combinatoric operations (permutations, product) | `itertools`, `functools` |
| `json`     | JSON pretty-print, compact, validate, query | `json` |
| `jwt`      | Decode JWT tokens (no verification) | `base64`, `json`, `datetime` |
| `keyword`  | Check/list Python keywords | `keyword` |
| `log`      | Tail, filter, grep log files | `re`, `json` |
| `mail`     | Parse .eml files (headers, body, attachments) | `email.parser`, `email.policy` |
| `net`      | TCP port check, scan, echo, wait-for-port | `socket`, `selectors`, `concurrent.futures` |
| `netrc`    | Parse/query .netrc files | `netrc` |
| `pickle`   | Inspect/disassemble pickle files safely | `pickle`, `pickletools` |
| `plist`    | Read/write/convert Apple plist files | `plistlib`, `json` |
| `profile`  | Profile a Python script and show stats | `cProfile`, `pstats`, `linecache` |
| `pydis`    | Disassemble Python source to bytecode | `dis`, `traceback` |
| `random`   | Shuffle, sample, dice, weighted choice | `random` |
| `repr`     | Format JSON data as Python repr/pprint | `pprint`, `copy` |
| `sched`    | Schedule one-shot or recurring commands | `sched`, `subprocess`, `threading` |
| `serve`    | HTTP/HTTPS static file server | `http.server`, `ssl`, `socketserver`, `dataclasses` |
| `shlex`    | Split/quote shell commands safely | `shlex` |
| `sort`     | Sort lines (alpha, numeric, length, top-N) | `heapq`, `bisect` |
| `struct`   | Pack/unpack binary data with format strings | `struct` |
| `template` | Render string.Template from JSON data | `string`, `json` |
| `time`     | Time utilities: now, epoch conversions, calendars | `datetime`, `time`, `zoneinfo` |
| `tokenize` | Tokenize Python source files | `tokenize`, `token` |
| `toml`     | Parse TOML and output as JSON | `tomllib`, `json` |
| `transform`| Text transformations (regex, case, wrap, dedent) | `re`, `collections`, `unicodedata`, `textwrap` |
| `unicode`  | Unicode character lookup, normalization, stats | `unicodedata` |
| `url`      | Parse, build, encode/decode URLs | `urllib.parse` |
| `wave`     | WAV audio file metadata and duration | `wave`, `array` |
| `zipapp`   | Create/inspect Python ZIP application archives | `zipapp`, `zipfile` |

## Installation

### From source (amalgamated single-file)

```sh
git clone https://github.com/jftuga/withpy.git
cd withpy
make install        # installs to /usr/local/bin
# or
make user-install   # installs to ~/bin
```

### Via pip (editable)

```sh
pip install -e .
```

### Direct use (no install)

```sh
python -m withpy <command> [args]
```

## Examples

```sh
# Hash a file
withpy hash myfile.txt

# Compress with lzma
withpy compress --format lzma data.bin --output data.bin.xz

# Decode JWT
withpy jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.sig

# Pretty-print JSON
cat data.json | withpy json --mode pretty --sort-keys

# IP network info
withpy ipaddr --mode info 192.168.1.0/24

# Safe calculator
withpy calc "sqrt(2) * pi"

# Find large files
withpy find /var/log --name "*.log" --size +10M

# Dependency sort
echo '{"app": ["db", "cache"], "db": [], "cache": []}' | withpy deps --mode sort

# Convert CSV to JSON
withpy csv --mode tojson data.csv

# Profile a script
withpy profile myscript.py --sort tottime

# HTTP fetch with timing
withpy fetch --timing https://example.com

# Generate passwords
withpy generate --mode password --length 24 --charset alphanum --count 5

# Color conversion
withpy color --from hex --to hsl "#FF6600"
```

## Build

```sh
make build       # Compile-check source
make test        # Run pytest suite (371 tests)
make amalgamate  # Build dist/withpy single-file artifact
make dist        # Create tar.xz archive
make clean       # Remove build artifacts
make help        # Show all targets
```

## Design

- Zero third-party runtime dependencies
- One subcommand per file under `withpy/commands/`
- Thin argparse dispatcher in `cli.py`
- Amalgamated single-file artifact via `build.py`
- Python 3.14+, fully type-annotated
- See [CLAUDE.md](CLAUDE.md) for contributor guidelines

## License

MIT
