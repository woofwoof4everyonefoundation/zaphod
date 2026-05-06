# zaphod.py

A small toy script for experimenting with simple text-pattern encodings.

This repository is for learning and demonstration only. It scans text supplied by the user and applies a few simple, auditable pattern checks such as sentence length, acrostics, punctuation rhythm, word-length parity, and capitalization anomalies.

It does not fetch, crawl, monitor, scrape, or connect to any external service.

## Status

Experimental toy. Expect false positives.

This is not cryptography. It is not suitable for secrecy, authentication, evasion, or operational use.

## Intended use

Appropriate uses include:

- learning basic steganography-adjacent concepts
- testing how formatting changes affect simple text patterns
- puzzle construction
- demonstrating false positives in pattern detection
- local experiments on text you already have permission to inspect

Do not use this project for:

- evading moderation or platform rules
- bypassing organizational controls
- hiding prohibited content
- data exfiltration
- covert coordination
- scanning third-party sites or large public corpora

## Commands

Encode a short message using the sentence-length toy scheme:

```bash
python zaphod.py encode SOS
```

Decode with one specific lens:

```bash
python zaphod.py decode sentence_morse sample.txt
```

Analyze sentence and paragraph lengths:

```bash
python zaphod.py analyze sample.txt
```

Scan user-provided text with several local lenses:

```bash
python zaphod.py scan sample.txt
```

Show evidence for reported candidates:

```bash
python zaphod.py scan sample.txt -v
```

## Important limitations

- False positives are common.
- Any output should be treated as a candidate pattern, not proof of intent.
- Small text samples are especially noisy.
- Editing, translation, summarization, reformatting, or copy/paste can destroy patterns.
- The generated encodings are low bandwidth and fragile.
- The script provides no confidentiality or integrity.

## Design boundaries

This project intentionally avoids network features. It should remain a local, user-supplied-text tool.

Non-goals:

- no scraping
- no crawling
- no monitoring
- no platform bypass features
- no claims of reliable hidden-message detection
- no homemade cryptography

## Repository contents

- `zaphod.py` - the toy scanner/encoder script
- `samples/` - small local examples
- `tests/` - minimal sanity tests
- `DISCLAIMER.md` - scope and responsible-use notes

## License

MIT. See `LICENSE`.
