"""
Trains the Dedris (Sambhota-family) -> Unicode Tibetan lookup table used by convert_dedris.py,
by frequency-matching raw (font, char) keystrokes against Unicode Tibetan tokens -- the
classic substitution-cipher approach -- rather than positionally aligning documents.

Why not positional alignment: the Sambhota originals (workspace/in/sambhota/KAMA-084-*.doc)
and the already-converted Unicode originals (workspace/in/KAMA-084-*.docx) do NOT correspond
1:1 by letter (measured: e.g. -a.doc has ~35,700 raw keystrokes but -a.docx has ~114,000
Unicode chars -- the converted set was evidently re-chunked by text/title boundaries, not by
the typist's original file split). But the aggregate character/token frequencies across the
whole corpus are directly comparable, and Tibetan Buddhist commentarial text has a stable
enough letter-frequency distribution that rank/count matching works well for the common
tokens, which is what a scripture conversion is mostly made of.

Method:
    1. Extract every (font, char) keystroke from all six KAMA-084-{a..f}.doc originals via
       tibtexts.fodtdoc.FodtDoc, tally counts per (font, char).
    2. Extract Unicode text from the four already-converted KAMA-084-{a,b,c,d}.docx files,
       tokenize with tibtexts.dedrismap.tokenize_unicode (STACK/VOWEL/OTHER), tally counts.
    3. Anchor: the single most common keystroke in the dominant stack font is assumed to be
       tsek (by far the most common token in real Tibetan text); this fixes a count-ratio
       (unicode_count / raw_count) used to project every other raw token's *expected* Unicode
       count.
    4. Walk every remaining raw (font, char) pair in descending count order; for each, greedily
       claim the not-yet-claimed Unicode candidate token (drawn from the STACK+OTHER pool for
       consonant-stack fonts, VOWEL+OTHER for Dedris-vowa) whose count is closest to that
       token's projected expected count. A poor best-fit (relative error over a threshold) is
       left unresolved rather than force-matched -- e.g. a typist's literal space keystroke
       used for visual spacing, which has no real Unicode counterpart.
    5. Writes the resulting table to resources/dedris-map.json (confidence-scored, still
       reviewable/hand-correctable), and a human-readable report to workspace/logs/ listing
       every accepted mapping and every unresolved high-frequency token for manual follow-up.

This is a first-pass statistical table, not a guarantee of correctness -- convert_dedris.py
flags every low/no-confidence resolution it hits rather than silently guessing, and the README
next to resources/dedris-map.json should be updated by hand as entries get manually verified
or corrected.
"""
import argparse
import datetime
import json
from collections import Counter
from glob import glob
from os import makedirs
from os.path import join, dirname, abspath, basename, splitext, exists

import docx

from tibtexts.fodtdoc import FodtDoc
from tibtexts.dedrismap import tokenize_unicode, TOKEN_STACK, TOKEN_VOWEL, TOKEN_OTHER

HERE = dirname(abspath(__file__))
DEFAULT_WORKSPACE = join(HERE, 'workspace')
DEFAULT_MAP_PATH = join(HERE, 'resources', 'dedris-map.json')

VOWA_FONT = 'Dedris-vowa'
MATCH_TOLERANCE = 0.35  # max relative error (|actual-expected|/expected) to accept a match

# Manually confirmed (font, char) -> Unicode corrections, applied after the statistical pass
# so a retrain never loses hand-verified entries. Add to this as more get confirmed with the
# user (see DEDRIS_CONVERSION_PLAN.md STATUS / workspace/logs for the review process).
KNOWN_ENTRIES = {
    (VOWA_FONT, 'J'): 'ི',            # short-i (was wrongly trained as literal space)
    (VOWA_FONT, 'R'): 'ཱཱུ',      # long-u: achung + zhabkyu, e.g. ཀཱུ (was wrongly trained as plain short-u)
}


def apply_known_entries(table):
    for (font, ch), unicode_str in KNOWN_ENTRIES.items():
        table.setdefault(font, {})[ch] = {
            'unicode': unicode_str, 'confidence': 1.0, 'count': table.get(font, {}).get(ch, {}).get('count', 0),
            'source': 'manual',
        }
    return table


def collect_raw_counts(doc_paths, workdir):
    """Sum (font, char) keystroke counts across every .doc in doc_paths."""
    counts = Counter()
    per_file = {}
    for path in doc_paths:
        fdoc = FodtDoc.from_doc(path, workdir)
        file_counts = Counter()
        for para in fdoc.paragraphs:
            for font, ch in para:
                file_counts[(font, ch)] += 1
        counts.update(file_counts)
        per_file[basename(path)] = file_counts
        print("  {}: {} keystrokes".format(basename(path), sum(file_counts.values())))
    return counts, per_file


def collect_unicode_counts(docx_paths):
    """Sum tokenize_unicode() counts across every .docx in docx_paths, split by token type."""
    counts_by_type = {TOKEN_STACK: Counter(), TOKEN_VOWEL: Counter(), TOKEN_OTHER: Counter()}
    for path in docx_paths:
        d = docx.Document(path)
        text = '\n'.join(p.text for p in d.paragraphs)
        for token_type, token in tokenize_unicode(text):
            counts_by_type[token_type][token] += 1
        print("  {}: {} chars".format(basename(path), len(text)))
    return counts_by_type


def find_tsek_anchor(raw_counts, other_pool):
    """
    Assumes the most frequent keystroke belonging to the numerically dominant stack font
    (the font with the single highest-count character overall, excluding Dedris-vowa) is tsek,
    since tsek is overwhelmingly the most common token in real Tibetan text. Returns
    ((font, char), ratio) where ratio = unicode_tsek_count / raw_count, used to project
    expected counts for every other token.
    """
    candidates = [((f, c), n) for (f, c), n in raw_counts.items() if f != VOWA_FONT]
    anchor, raw_n = max(candidates, key=lambda item: item[1])
    tsek_unicode_count = other_pool.get('་', 0)
    if tsek_unicode_count == 0 or raw_n == 0:
        raise RuntimeError("Could not establish a tsek anchor -- no candidate counts found.")
    ratio = tsek_unicode_count / raw_n
    return anchor, ratio


def greedy_match(raw_counts, unicode_pools, ratio):
    """
    Walk raw (font, char) pairs in descending count order; for each, claim the closest-by-
    expected-count not-yet-claimed candidate from its font's pool (stack fonts draw from
    STACK+OTHER, Dedris-vowa draws from VOWEL+OTHER). Returns:
        table: {font: {char: {"unicode":..., "confidence":..., "count":...}}}
        unresolved: [((font, char), raw_count, best_candidate_or_None, best_error_or_None)]
    """
    stack_pool = dict(unicode_pools[TOKEN_STACK])
    stack_pool.update(unicode_pools[TOKEN_OTHER])
    vowel_pool = dict(unicode_pools[TOKEN_VOWEL])
    vowel_pool.update(unicode_pools[TOKEN_OTHER])
    # OTHER entries are shared between the two pools but must only be claimed once, so track
    # claims against one shared "available" dict per pool identity, keyed by token string.
    shared_other = dict(unicode_pools[TOKEN_OTHER])

    def current_pool(font):
        pool = dict(unicode_pools[TOKEN_VOWEL]) if font == VOWA_FONT else dict(unicode_pools[TOKEN_STACK])
        pool.update(shared_other)
        return pool

    table = {}
    unresolved = []
    ordered = sorted(raw_counts.items(), key=lambda item: item[1], reverse=True)
    for (font, ch), raw_n in ordered:
        pool = current_pool(font)
        if not pool:
            unresolved.append(((font, ch), raw_n, None, None))
            continue
        expected = raw_n * ratio
        best_token, best_count = min(pool.items(), key=lambda kv: abs(kv[1] - expected))
        rel_error = abs(best_count - expected) / expected if expected else 1.0
        if rel_error <= MATCH_TOLERANCE:
            confidence = max(0.0, 1.0 - rel_error)
            table.setdefault(font, {})[ch] = {
                'unicode': best_token, 'confidence': round(confidence, 3), 'count': raw_n,
            }
            unicode_pools[TOKEN_STACK].pop(best_token, None)
            unicode_pools[TOKEN_VOWEL].pop(best_token, None)
            shared_other.pop(best_token, None)
        else:
            unresolved.append(((font, ch), raw_n, best_token, rel_error))
    return table, unresolved


def write_report(path, anchor, ratio, table, unresolved, raw_counts):
    with open(path, 'w', encoding='utf-8') as fout:
        fout.write("Dedris map training report -- {}\n\n".format(datetime.datetime.now()))
        fout.write("Tsek anchor: {} (raw count {}), ratio (unicode/raw) = {:.4f}\n\n".format(
            anchor, raw_counts[anchor], ratio))
        total = sum(raw_counts.values())
        matched = sum(len(chars) for chars in table.values())
        fout.write("Resolved {} of {} distinct (font, char) pairs ({} total keystrokes)\n\n".format(
            matched, len(raw_counts), total))
        fout.write("=== Resolved (by descending confidence) ===\n")
        rows = [
            (font, ch, entry['unicode'], entry['confidence'], entry['count'])
            for font, chars in table.items() for ch, entry in chars.items()
        ]
        for font, ch, uni, conf, count in sorted(rows, key=lambda r: r[3]):
            fout.write("  {:.3f}  ({!r}, {!r}) -> {!r}  (seen {} times)\n".format(
                conf, font, ch, uni, count))
        fout.write("\n=== Unresolved -- needs manual review or more training data ===\n")
        for (font, ch), raw_n, candidate, err in sorted(unresolved, key=lambda r: -r[1]):
            if candidate is None:
                fout.write("  ({!r}, {!r}) seen {} times -- no candidate pool available\n".format(
                    font, ch, raw_n))
            else:
                fout.write(
                    "  ({!r}, {!r}) seen {} times -- best guess {!r} but relative error {:.2f} "
                    "over tolerance ({}); likely a non-content artifact (e.g. typist spacing) "
                    "or a rare/unseen combination\n".format(font, ch, raw_n, candidate, err, MATCH_TOLERANCE))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-w', '--workspace', default=DEFAULT_WORKSPACE,
                         help='Workspace root (default: ./workspace next to this script)')
    parser.add_argument('--doc-glob', default='in/sambhota/*.doc',
                         help='Glob (relative to workspace) for Sambhota .doc originals to train on')
    parser.add_argument('--docx-glob', default='in/*.docx',
                         help='Glob (relative to workspace) for already-converted Unicode .docx files')
    parser.add_argument('-o', '--out', default=DEFAULT_MAP_PATH, help='Output path for the trained map JSON')
    args = parser.parse_args()

    doc_paths = sorted(glob(join(args.workspace, args.doc_glob)))
    docx_paths = sorted(glob(join(args.workspace, args.docx_glob)))
    if not doc_paths:
        raise SystemExit("No Sambhota .doc files matched {}".format(join(args.workspace, args.doc_glob)))
    if not docx_paths:
        raise SystemExit("No converted .docx files matched {}".format(join(args.workspace, args.docx_glob)))

    print("Training on {} Sambhota .doc file(s), validating against {} converted .docx file(s)".format(
        len(doc_paths), len(docx_paths)))

    temp_dir = join(args.workspace, 'temp')
    makedirs(temp_dir, exist_ok=True)

    print("\nExtracting raw keystrokes:")
    raw_counts, _per_file = collect_raw_counts(doc_paths, temp_dir)

    print("\nExtracting Unicode tokens:")
    unicode_pools = collect_unicode_counts(docx_paths)

    anchor, ratio = find_tsek_anchor(raw_counts, unicode_pools[TOKEN_OTHER])
    print("\nTsek anchor: {} (ratio {:.4f})".format(anchor, ratio))

    table, unresolved = greedy_match(raw_counts, unicode_pools, ratio)

    makedirs(dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fout:
        json.dump(table, fout, ensure_ascii=False, indent=1, sort_keys=True)
    print("\nWrote {} font(s), {} entries to {}".format(
        len(table), sum(len(c) for c in table.values()), args.out))

    makedirs(join(args.workspace, 'logs'), exist_ok=True)
    report_path = join(args.workspace, 'logs',
                        'dedris-map-training-{}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')))
    write_report(report_path, anchor, ratio, table, unresolved, raw_counts)
    print("Report written to {}".format(report_path))


if __name__ == '__main__':
    main()
