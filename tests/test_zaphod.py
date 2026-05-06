from zaphod import decode_sentence_morse, encode_sentence_morse


def test_sentence_morse_round_trip_sos():
    text = encode_sentence_morse("SOS")
    decoded, _ = decode_sentence_morse(text)
    assert decoded == "SOS"
