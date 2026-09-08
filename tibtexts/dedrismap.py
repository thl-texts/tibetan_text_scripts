"""
DedrisMap: the persisted (font_name, char) -> Unicode-string lookup table used to convert
Dedris-family (Sambhota) keystrokes to Unicode Tibetan (see build_dedris_map_from_fuf.py,
which builds resources/dedris-map.json from the real UDP .fuf keystroke tables).

Encoding model (confirmed against UDP's own .fuf tables): a single Dedris keystroke can
resolve to one or more Unicode codepoints (a base consonant, a subjoined form, a vowel sign,
or a short combination of these). Vowel signs are typed separately (font "Dedris-vowa") on
top of/after the stack. Converting is therefore just: resolve each keystroke independently via
this table, then concatenate in keystroke order -- no generic base/subjoined/vowel reordering
is needed.
"""
import json
from collections import Counter


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
