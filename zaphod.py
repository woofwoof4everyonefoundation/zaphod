#!/usr/bin/env python3
"""
zaphod.py

Local toy script for experimenting with simple text-pattern encodings.
It scans user-supplied text only. It does not fetch, crawl, monitor, or connect
anywhere. Results are noisy candidates, not evidence of intent.
"""

from __future__ import annotations

import argparse
import re
import string
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


MORSE_TO_CHAR = {
    ".": "E", "-": "T",
    "..": "I", ".-": "A", "-.": "N", "--": "M",
    "...": "S", "..-": "U", ".-.": "R", ".--": "W",
    "-..": "D", "-.-": "K", "--.": "G", "---": "O",
    "....": "H", "...-": "V", "..-.": "F", ".-..": "L",
    ".--.": "P", ".---": "J", "-...": "B", "-..-": "X",
    "-.-.": "C", "-.--": "Y", "--..": "Z", "--.-": "Q",
    ".....": "5", "....-": "4", "...--": "3", "..---": "2",
    ".----": "1", "-....": "6", "--...": "7", "---..": "8",
    "----.": "9", "-----": "0",
}
CHAR_TO_MORSE = {v: k for k, v in MORSE_TO_CHAR.items()}


@dataclass
class Hit:
    decoder: str
    block_index: int
    decoded: str
    score: float
    evidence: list[str]


def read_input(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def split_blocks(text: str) -> list[str]:
    return [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.findall(r"[^.!?]+[.!?]", text, flags=re.MULTILINE) if s.strip()]


def words_in(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?", text)


def count_words(text: str) -> int:
    return len(words_in(text))


def score_decoded_text(decoded: str) -> float:
    if not decoded:
        return 0.0
    known = 1.0 - (decoded.count("?") / len(decoded))
    printable = sum(1 for c in decoded if c in string.printable and c not in "\x0b\x0c") / len(decoded)
    alpha = sum(1 for c in decoded if c.isalpha() or c.isspace()) / len(decoded)
    length_bonus = min(len(decoded) / 8.0, 1.0)
    return (known * 0.45) + (printable * 0.20) + (alpha * 0.20) + (length_bonus * 0.15)


def looks_interesting(decoded: str, min_len: int, min_score: float) -> bool:
    return len(decoded.replace("?", "")) >= min_len and score_decoded_text(decoded) >= min_score


def sentence_class(sentence: str, short_max: int, long_min: int) -> str:
    n = count_words(sentence)
    if n <= short_max:
        return "."
    if n >= long_min:
        return "-"
    return "|"


def decode_sentence_morse(text: str, short_max: int = 4, long_min: int = 10, verbose: bool = False) -> tuple[str, list[str]]:
    morse = ""
    decoded: list[str] = []
    evidence: list[str] = []
    for i, sentence in enumerate(split_sentences(text), start=1):
        wc = count_words(sentence)
        symbol = sentence_class(sentence, short_max, long_min)
        if symbol == "|":
            if morse:
                char = MORSE_TO_CHAR.get(morse, "?")
                decoded.append(char)
                evidence.append(f"[{i:03d}] {wc:2d} words -> break | {morse}={char} | {sentence}")
                morse = ""
            elif verbose:
                evidence.append(f"[{i:03d}] {wc:2d} words -> break | {sentence}")
        else:
            morse += symbol
            evidence.append(f"[{i:03d}] {wc:2d} words -> {symbol} | {sentence}")
    if morse:
        char = MORSE_TO_CHAR.get(morse, "?")
        decoded.append(char)
        evidence.append(f"[end] morse={morse} -> {char}")
    return "".join(decoded), evidence


def decode_paragraph_morse(text: str, para_short_max: int = 12, para_long_min: int = 40, verbose: bool = False) -> tuple[str, list[str]]:
    morse = ""
    decoded: list[str] = []
    evidence: list[str] = []
    for i, para in enumerate(split_blocks(text), start=1):
        wc = count_words(para)
        if wc <= para_short_max:
            morse += "."
            evidence.append(f"[para {i:03d}] {wc:3d} words -> .")
        elif wc >= para_long_min:
            morse += "-"
            evidence.append(f"[para {i:03d}] {wc:3d} words -> -")
        else:
            if morse:
                char = MORSE_TO_CHAR.get(morse, "?")
                decoded.append(char)
                evidence.append(f"[para {i:03d}] {wc:3d} words -> break | {morse}={char}")
                morse = ""
            elif verbose:
                evidence.append(f"[para {i:03d}] {wc:3d} words -> break")
    if morse:
        char = MORSE_TO_CHAR.get(morse, "?")
        decoded.append(char)
        evidence.append(f"[end] morse={morse} -> {char}")
    return "".join(decoded), evidence


def decode_first_acrostic(text: str, verbose: bool = False) -> tuple[str, list[str]]:
    out: list[str] = []
    evidence: list[str] = []
    for i, sentence in enumerate(split_sentences(text), start=1):
        words = words_in(sentence)
        if words:
            ch = words[0][0].upper()
            out.append(ch)
            evidence.append(f"[{i:03d}] {ch} <- {sentence}")
    return "".join(out), evidence


def decode_last_acrostic(text: str, verbose: bool = False) -> tuple[str, list[str]]:
    out: list[str] = []
    evidence: list[str] = []
    for i, sentence in enumerate(split_sentences(text), start=1):
        words = words_in(sentence)
        if not words:
            continue
        letters = re.findall(r"[A-Za-z]", words[-1])
        if letters:
            ch = letters[-1].upper()
            out.append(ch)
            evidence.append(f"[{i:03d}] {ch} <- {sentence}")
    return "".join(out), evidence


def decode_punct_morse(text: str, verbose: bool = False) -> tuple[str, list[str]]:
    decoded: list[str] = []
    evidence: list[str] = []
    morse = ""
    for i, ch in enumerate(text):
        if ch == ",":
            morse += "."
            evidence.append(f"[{i:03d}] comma -> .")
        elif ch in ";:—–-":
            morse += "-"
            evidence.append(f"[{i:03d}] {repr(ch)} -> -")
        elif ch in ".!?" and morse:
            char = MORSE_TO_CHAR.get(morse, "?")
            decoded.append(char)
            evidence.append(f"[{i:03d}] sentence end -> {morse}={char}")
            morse = ""
    if morse:
        char = MORSE_TO_CHAR.get(morse, "?")
        decoded.append(char)
        evidence.append(f"[end] morse={morse} -> {char}")
    return "".join(decoded), evidence


def bits_to_ascii(bits: str) -> str:
    chars = []
    for i in range(0, len(bits) - 7, 8):
        value = int(bits[i:i + 8], 2)
        chars.append(chr(value) if 32 <= value <= 126 else "?")
    return "".join(chars)


def decode_word_parity_bits(text: str, verbose: bool = False) -> tuple[str, list[str]]:
    bits = []
    evidence: list[str] = []
    for i, word in enumerate(words_in(text), start=1):
        bit = "0" if len(word) % 2 == 0 else "1"
        bits.append(bit)
        if verbose or i <= 80:
            evidence.append(f"[{i:03d}] {word!r:20s} len={len(word):2d} -> {bit}")
    bit_string = "".join(bits)
    decoded = bits_to_ascii(bit_string)
    evidence.append(f"[bits] {bit_string[:128]}{'...' if len(bit_string) > 128 else ''}")
    return decoded, evidence


def scan_caps_anomalies(text: str, verbose: bool = False) -> tuple[str, list[str]]:
    evidence: list[str] = []
    anomalies: list[str] = []
    for token in re.findall(r"\b[A-Za-z][A-Za-z0-9'-]*\b", text):
        if len(token) <= 1:
            continue
        mid_caps = bool(re.search(r"[a-z][A-Z]", token))
        all_caps = token.isupper() and len(token) > 2
        if mid_caps or all_caps:
            anomalies.append(token)
            evidence.append(f"capitalization anomaly: {token}")
    if not evidence:
        evidence.append("No capitalization anomalies found.")
    return "".join(t[0].upper() for t in anomalies[:80]), evidence


DECODERS: dict[str, Callable[..., tuple[str, list[str]]]] = {
    "sentence_morse": decode_sentence_morse,
    "paragraph_morse": decode_paragraph_morse,
    "first_acrostic": decode_first_acrostic,
    "last_acrostic": decode_last_acrostic,
    "punct_morse": decode_punct_morse,
    "word_parity_bits": decode_word_parity_bits,
    "caps_anomalies": scan_caps_anomalies,
}


SHORT_SENTENCES = [
    "Fair point.", "Seems likely.", "Worth testing.", "Makes sense.",
    "Fair enough.", "Ship it.", "I agree.", "Good call.",
    "Seems plausible.", "Noted.", "Looks fine.", "Probably works.",
]
LONG_SENTENCES = [
    "The boring implementation is probably easier to keep correct than another clever abstraction.",
    "It also makes the failure mode visible when someone has to debug it later.",
    "That usually matters more than making the first version feel elegant.",
    "The small script is probably easier to maintain than adding another dependency.",
    "This seems like the kind of tradeoff that gets clearer after actual use.",
    "A plain text version also survives better across weird tools and old interfaces.",
    "The main risk is probably overdesigning something that only needed a simple pass.",
    "I would rather keep the behavior obvious than hide it behind too much machinery.",
]
BREAK_SENTENCES = [
    "That is the annoying part.", "The small details matter here.",
    "I would test it first.", "There are tradeoffs either way.",
    "That still seems worth checking.", "The edge cases matter too.",
]


def encode_sentence_morse(message: str) -> str:
    chunks: list[str] = []
    short_i = long_i = break_i = 0
    for ch in message.upper():
        if ch == " ":
            chunks.append("\n\n")
            continue
        if ch not in CHAR_TO_MORSE:
            raise ValueError(f"Cannot encode character: {ch!r}")
        for symbol in CHAR_TO_MORSE[ch]:
            if symbol == ".":
                chunks.append(SHORT_SENTENCES[short_i % len(SHORT_SENTENCES)])
                short_i += 1
            else:
                chunks.append(LONG_SENTENCES[long_i % len(LONG_SENTENCES)])
                long_i += 1
        chunks.append(BREAK_SENTENCES[break_i % len(BREAK_SENTENCES)])
        break_i += 1
    out = ""
    for chunk in chunks:
        if chunk == "\n\n":
            out = out.rstrip() + "\n\n"
        else:
            if out and not out.endswith(("\n", " ")):
                out += " "
            out += chunk
    return out.strip()


def scan_text(text: str, decoders: list[str], min_len: int, min_score: float, verbose: bool,
              short_max: int, long_min: int, para_short_max: int, para_long_min: int) -> list[Hit]:
    hits: list[Hit] = []
    blocks = split_blocks(text) or ([text.strip()] if text.strip() else [])
    for block_i, block in enumerate(blocks, start=1):
        for name in decoders:
            fn = DECODERS[name]
            if name == "sentence_morse":
                decoded, evidence = fn(block, short_max=short_max, long_min=long_min, verbose=verbose)
            elif name == "paragraph_morse":
                decoded, evidence = fn(block, para_short_max=para_short_max, para_long_min=para_long_min, verbose=verbose)
            else:
                decoded, evidence = fn(block, verbose=verbose)
            score = score_decoded_text(decoded)
            if name == "caps_anomalies":
                if len(decoded) >= max(min_len, 3):
                    hits.append(Hit(name, block_i, decoded, min(score, 0.50), evidence))
            elif looks_interesting(decoded, min_len, min_score):
                hits.append(Hit(name, block_i, decoded, score, evidence))
    return sorted(hits, key=lambda h: h.score, reverse=True)


def print_hits(hits: list[Hit], verbose: bool, max_hits: int) -> None:
    if not hits:
        print("No likely candidates found.")
        return
    for n, hit in enumerate(hits[:max_hits], start=1):
        print(f"[{n:02d}] block={hit.block_index} decoder={hit.decoder} score={hit.score:.2f} decoded={hit.decoded!r}")
        if verbose:
            print("     evidence:")
            for line in hit.evidence[:80]:
                print(f"       {line}")
            if len(hit.evidence) > 80:
                print(f"       ... {len(hit.evidence) - 80} more evidence lines")
            print()


def analyze_text(text: str, short_max: int, long_min: int, para_short_max: int, para_long_min: int) -> None:
    print("== Sentence analysis ==")
    for i, sentence in enumerate(split_sentences(text), start=1):
        wc = count_words(sentence)
        label = sentence_class(sentence, short_max, long_min)
        print(f"[{i:03d}] {wc:2d} words -> {'break' if label == '|' else label:5s} | {sentence}")
    print("\n== Paragraph analysis ==")
    for i, para in enumerate(split_blocks(text), start=1):
        wc = count_words(para)
        label = "." if wc <= para_short_max else "-" if wc >= para_long_min else "break"
        print(f"[para {i:03d}] {wc:3d} words -> {label}")


def parse_decoder_list(raw: str) -> list[str]:
    if raw == "all":
        return list(DECODERS.keys())
    names = [x.strip() for x in raw.split(",") if x.strip()]
    bad = [x for x in names if x not in DECODERS]
    if bad:
        raise SystemExit(f"Unknown decoder(s): {', '.join(bad)}. Valid: {', '.join(DECODERS)}")
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description="Local toy text-pattern scanner.")
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encode", help="Generate sentence-length Morse carrier text.")
    enc.add_argument("message")

    dec = sub.add_parser("decode", help="Run one decoder on provided text.")
    dec.add_argument("decoder", choices=sorted(DECODERS.keys()))
    dec.add_argument("file", nargs="?")
    dec.add_argument("-v", "--verbose", action="store_true")
    dec.add_argument("--short-max", type=int, default=4)
    dec.add_argument("--long-min", type=int, default=10)
    dec.add_argument("--para-short-max", type=int, default=12)
    dec.add_argument("--para-long-min", type=int, default=40)

    scan = sub.add_parser("scan", help="Run multiple decoders across text blocks.")
    scan.add_argument("file", nargs="?")
    scan.add_argument("--decoders", default="sentence_morse,first_acrostic,last_acrostic,punct_morse,word_parity_bits,caps_anomalies")
    scan.add_argument("--min-len", type=int, default=2)
    scan.add_argument("--min-score", type=float, default=0.65)
    scan.add_argument("--max-hits", type=int, default=25)
    scan.add_argument("-v", "--verbose", action="store_true")
    scan.add_argument("--short-max", type=int, default=4)
    scan.add_argument("--long-min", type=int, default=10)
    scan.add_argument("--para-short-max", type=int, default=12)
    scan.add_argument("--para-long-min", type=int, default=40)

    ana = sub.add_parser("analyze", help="Show sentence/paragraph classifications.")
    ana.add_argument("file", nargs="?")
    ana.add_argument("--short-max", type=int, default=4)
    ana.add_argument("--long-min", type=int, default=10)
    ana.add_argument("--para-short-max", type=int, default=12)
    ana.add_argument("--para-long-min", type=int, default=40)

    args = parser.parse_args()

    if args.command == "encode":
        print(encode_sentence_morse(args.message))
    elif args.command == "analyze":
        analyze_text(read_input(args.file), args.short_max, args.long_min, args.para_short_max, args.para_long_min)
    elif args.command == "decode":
        text = read_input(args.file)
        fn = DECODERS[args.decoder]
        if args.decoder == "sentence_morse":
            decoded, evidence = fn(text, short_max=args.short_max, long_min=args.long_min, verbose=args.verbose)
        elif args.decoder == "paragraph_morse":
            decoded, evidence = fn(text, para_short_max=args.para_short_max, para_long_min=args.para_long_min, verbose=args.verbose)
        else:
            decoded, evidence = fn(text, verbose=args.verbose)
        print(decoded)
        if args.verbose:
            print("\n== Evidence ==")
            print("\n".join(evidence))
    elif args.command == "scan":
        hits = scan_text(
            read_input(args.file),
            decoders=parse_decoder_list(args.decoders),
            min_len=args.min_len,
            min_score=args.min_score,
            verbose=args.verbose,
            short_max=args.short_max,
            long_min=args.long_min,
            para_short_max=args.para_short_max,
            para_long_min=args.para_long_min,
        )
        print_hits(hits, verbose=args.verbose, max_hits=args.max_hits)


if __name__ == "__main__":
    main()
