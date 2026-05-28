'''CLI for standalone SRAM layout generation.'''

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .standalone import StandaloneSpec, write_standalone


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="optional JSON config with word_size, num_words, words_per_row, out, and name")
    parser.add_argument("--word-size", type=int)
    parser.add_argument("--num-words", type=int)
    parser.add_argument("--words-per-row", type=int, default=None)
    parser.add_argument("--name")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    config = _load_config(args.config) if args.config else {}
    word_size = _pick(args.word_size, config, "word_size")
    num_words = _pick(args.num_words, config, "num_words")
    words_per_row = _pick(args.words_per_row, config, "words_per_row")
    out = _pick(args.out, config, "out")
    name = _pick(args.name, config, "name")

    missing = [key for key, value in {"word_size": word_size, "num_words": num_words, "out": out}.items() if value is None]
    if missing:
        parser.error("missing required option(s): " + ", ".join(missing))
    try:
        spec = StandaloneSpec(
            word_size=int(word_size),
            num_words=int(num_words),
            words_per_row=int(words_per_row) if words_per_row is not None else None,
            name=str(name) if name else None,
        )
    except ValueError as exc:
        parser.error(str(exc))
    metrics = write_standalone(spec, Path(out))
    print(json.dumps(metrics, indent=2))
    return 0


def _load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _pick(value: object, config: dict, key: str) -> object:
    return value if value is not None else config.get(key)


if __name__ == "__main__":
    raise SystemExit(main())
