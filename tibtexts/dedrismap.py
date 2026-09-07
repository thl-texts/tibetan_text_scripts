"""
DedrisMap: the persisted (font_name, char) -> Unicode-string lookup table used to convert
Dedris-family (Sambhota) keystrokes to Unicode Tibetan, plus the Unicode-side tokenizer used
to build that table (see build_dedris_map.py).

Encoding model (confirmed with the person who designed this font family): a single Dedris
keystroke represents an entire pre-rendered consonant stack (one or more Tibetan letters
glued into one glyph), not a single letter -- so one keystroke can resolve to several Unicode
codepoints. Vowel signs are typed separately (font "Dedris-vowa") on top of/after the stack.
Converting is therefore just: resolve each keystroke independently via this table, then
concatenate in keystroke order -- no generic base/subjoined/vowel reordering is needed.
"""
import json
import re
from collections import Counter

# Unicode Tibetan block structure (U+0F00-U+0FFF), used to segment already-Unicode text into
# tokens comparable to Dedris keystrokes: one "stack" token per base-consonant + any subjoined
# forms, one "vowel" token per run of vowel-sign marks, everything else token-per-character.
_CONSONANT = 'ཀ-ཬ'
_SUBJOINED = 'ྐ-ྼ'
_VOWEL = 'ཱ-྄྆྇'

STACK_RE = re.compile('[{0}][{1}]*'.format(_CONSONANT, _SUBJOINED))
VOWEL_RE = re.compile('[{0}]+'.format(_VOWEL))

TOKEN_STACK = 'STACK'
TOKEN_VOWEL = 'VOWEL'
TOKEN_OTHER = 'OTHER'


def tokenize_unicode(text):
    """
    Walk text left to right, greedily emitting (token_type, token_text) tuples: a STACK token
    for a base consonant plus any subjoined forms, a VOWEL token for a run of vowel signs, and
    an OTHER token per remaining character (tsek, shad, spaces, annotation brackets, etc).
    """
    tokens = []
    i, n = 0, len(text)
    while i < n:
        m = STACK_RE.match(text, i)
        if m:
            tokens.append((TOKEN_STACK, m.group()))
            i = m.end()
            continue
        m = VOWEL_RE.match(text, i)
        if m:
            tokens.append((TOKEN_VOWEL, m.group()))
            i = m.end()
            continue
        tokens.append((TOKEN_OTHER, text[i]))
        i += 1
    return tokens


class DedrisMap:
    """
    Loads/holds the trained font->char->Unicode lookup table and reports on its use: unknown
    (font, char) pairs, and every distinct font name it's been asked to resolve (so a user can
    tell which Dedris font files, beyond the ones already vendored, a given volume needs).
    """

    def __init__(self, table=None):
        # table: {font_name: {char: {"unicode": str, "confidence": float, "count": int}}}
        self.table = table or {}
        self.misses = Counter()  # (font, char) -> times seen unresolved
        self.fonts_seen = Counter()  # font_name -> chars resolved against it (known or not)

    @classmethod
    def load(cls, path):
        with open(path, 'r', encoding='utf-8') as fin:
            return cls(json.load(fin))

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as fout:
            json.dump(self.table, fout, ensure_ascii=False, indent=1, sort_keys=True)

    def resolve(self, font_name, char, min_confidence=0.0):
        """
        Returns (unicode_string, confidence) for the given keystroke, or (None, 0.0) if the
        pair is unknown or below min_confidence. Always records the lookup for reporting via
        fonts_seen()/misses().
        """
        self.fonts_seen[font_name] += 1
        entry = self.table.get(font_name, {}).get(char)
        if entry is None or entry.get('confidence', 0.0) < min_confidence:
            self.misses[(font_name, char)] += 1
            return None, 0.0
        return entry['unicode'], entry['confidence']

    def fonts_encountered(self):
        return sorted(self.fonts_seen)

    def miss_report(self):
        return self.misses.most_common()
