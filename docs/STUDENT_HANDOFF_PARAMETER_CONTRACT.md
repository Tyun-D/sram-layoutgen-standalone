# Student Handoff Parameter Contract

Audit timestamp: 2026-08-09T05:02:51Z

Current runnable CLI:

```bash
python -m sram_layoutgen \
  --word-size 16 \
  --num-words 16 \
  --words-per-row 1 \
  --out /path/to/output
```

JSON config is also supported:

```bash
python -m sram_layoutgen --config configs/sram_16x16.json --out outputs/sram_16x16
```

Current direct CLI/config parameters:

| parameter | status | source | notes |
|---|---|---|---|
| `word_size` | CURRENTLY_RUNNABLE | `StandaloneSpec.word_size` | positive integer |
| `num_words` | CURRENTLY_RUNNABLE | `StandaloneSpec.num_words` | positive integer |
| `words_per_row` | CURRENTLY_RUNNABLE with constraints | `StandaloneSpec.words_per_row` | legal values are from `{1,2,4,8,16}` filtered by `num_words % wpr == 0` and `num_words / wpr >= 16` |
| `name` | CURRENTLY_RUNNABLE | CLI/config | optional top/output basename |
| `out` | CURRENTLY_RUNNABLE | CLI/config | output directory |
| `technology` | SUPPORTED_WITH_CONSTRAINTS | hardcoded `load_bundled_freepdk45()` | only bundled FreePDK45 is exposed by current CLI |
| `bank_count` | NOT_SUPPORTED in legacy CLI | not in `StandaloneSpec` | no multi-bank CLI contract in this path |
| OpenYield adapter flags | PARTIAL/internal | `StandaloneSpec.enable_openyield_*` | dataclass supports flags, but CLI does not expose them and full-top OpenYield validation is a separate path |

Current derivation logic from `build_layout`:

- `wpr = spec.resolved_words_per_row()`
- `rows = spec.num_words // wpr`
- `cols = spec.word_size * wpr`
- `addr_bits = max(1, (spec.num_words - 1).bit_length())`
- `row_addr_bits = max(1, (rows - 1).bit_length())`
- `col_addr_bits = max(0, (wpr - 1).bit_length())`

Current legal `words_per_row` behavior:

- Candidate set: `[1, 2, 4, 8, 16]`
- Additional constraints: `num_words % wpr == 0` and `num_words // wpr >= 16`
- If omitted, default is the maximum legal WPR.
- Examples:
  - `num_words=16`: legal WPR is `[1]`
  - `num_words=32`: legal WPR is `[1,2]`
  - `num_words=64`: legal WPR is `[1,2,4]`

Smoke-tested current configurations:

| config | status | derived rows | derived cols | addr bits |
|---|---|---:|---:|---:|
| 16 words x 16 bits, WPR=1 | CURRENTLY_RUNNABLE | 16 | 16 | 4 |
| 32 words x 16 bits, WPR=1 | CURRENTLY_RUNNABLE | 32 | 16 | 5 |
| 32 words x 16 bits, WPR=2 | CURRENTLY_RUNNABLE | 16 | 32 | 5 |

Parameterization result: true for single-bank FreePDK45 legacy macro generation. Multi-bank and technology switching are not current legacy CLI features.
