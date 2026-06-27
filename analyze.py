#!/usr/bin/env python3
"""
Seinfeld vocabulary analysis for a non-native (East-European) English learner.

Idea: find words that are UNCOMMON in general English (low Zipf) yet RECUR across
Seinfeld episodes -> the high-value vocabulary worth learning. Filter out proper
nouns (character names) and isolate the show's signature Yiddish/loanwords.
"""
import os, re, json, glob, math, unicodedata
from collections import Counter, defaultdict
from wordfreq import zipf_frequency
from nltk.corpus import wordnet as wn

# Languages an East-European English learner is likely to know. If an English
# word also exists (as loanword / cognate / native word) in one of these, it is
# FAMILIAR and therefore easy; if absent from all of them, it is genuinely hard.
EE_LANGS = ["ro", "pl", "ru", "cs", "hu", "bg", "uk", "sk"]


def ee_familiarity(word):
    """Max Zipf of the exact token across East-European languages (0 = absent)."""
    return max(zipf_frequency(word, l) for l in EE_LANGS)


def deaccent(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


_DEF_CACHE = {}


def define(word):
    """First WordNet gloss for a word, '' if none (coinages, names)."""
    if word in _DEF_CACHE:
        return _DEF_CACHE[word]
    syns = wn.synsets(word)
    d = ""
    if syns:
        # prefer the most frequent sense; tag part of speech
        s = syns[0]
        pos = {"n": "noun", "v": "verb", "a": "adj", "s": "adj",
               "r": "adv"}.get(s.pos(), "")
        gloss = s.definition()
        d = (f"({pos}) " if pos else "") + gloss
    _DEF_CACHE[word] = d
    return d


_SPECIAL = {"won't": "will", "can't": "can", "shan't": "shall",
            "ain't": "is", "y'all": "you", "let's": "let"}
# fix artifacts from accent-stripped source text
_NORMALIZE = {"fianc": "fiance", "fiancee": "fiance",
              "caf": "cafe", "prot": "protege", "clich": "cliche",
              "expos": "expose", "risqu": "risque"}
# pure junk tokens to drop (OCR/encoding glitches in source)
_JUNK = {"lik", "lzzy", "didn", "couldn", "wouldn", "doesn", "isn"}


def clean_word(w):
    """Lowercased token (may contain apostrophe) -> base vocabulary word."""
    w = w.replace("’", "'")
    w = deaccent(w).lower()
    if w in _SPECIAL:
        return _SPECIAL[w]
    if w.endswith("n't"):          # couldn't->could, doesn't->does, isn't->is
        w = w[:-3]
    elif "'" in w:                 # it's->it, they're->they, george's->george
        w = w.split("'")[0]
    return _NORMALIZE.get(w, w)

TX = "transcripts"
OUT = "data.json"

# ---- Seinfeld-signature Yiddish / loanwords (the show is famous for these) ----
YIDDISH = {
    "schmuck", "schlep", "schlepped", "schlepping", "spiel", "putz", "klutz",
    "schmooze", "schmoozing", "kvetch", "kvetching", "shtick", "schtick",
    "mensch", "chutzpah", "tchotchke", "tchotchkes", "yada", "nosh", "schmear",
    "meshugge", "meshuggeneh", "glitch", "maven", "schlemiel", "shlub",
    "verklempt", "oy", "bupkis", "schmaltz", "schmaltzy", "putzes",
}

# words that are interjections / fillers — flag separately, low learning value
INTERJECTIONS = {"uh", "oh", "ah", "ha", "hey", "huh", "hmm", "ow", "ooh",
                 "whoa", "yeah", "yep", "nope", "wow", "huh", "eh", "shh",
                 "ugh", "ahh", "ohh", "aw", "aww", "yikes", "phew"}

# Seinfeld-invented words / catchphrases: cultural literacy, NOT dictionary vocab
COINAGE = {"festivus", "schmoopie", "regifter", "regifting", "regift", "sidler",
           "sidling", "manssiere", "mimbo", "shusher", "shushing", "shush",
           "anti", "dentite", "yada", "serenity", "shrinkage", "spongeworthy",
           "double", "dipping", "bizarro", "kavorka", "assman"}

# common conversational idioms / phrasal expressions (hardest for non-natives)
IDIOMS = [
    "come on", "big deal", "no way", "shut up", "get out", "you know",
    "i mean", "kind of", "sort of", "a lot", "give me a break",
    "what's the deal", "going on", "make out", "hang out", "show up",
    "figure out", "pick up", "find out", "deal with", "look at",
    "take care", "no big deal", "by the way", "as a matter of fact",
    "for crying out loud", "you got to be kidding", "i can't believe",
    "knock it off", "freak out", "rip off", "screw up", "blow off",
    "pull off", "back off", "calm down", "what is the deal",
]

WORD_RE = re.compile(r"[A-Za-zÀ-ſ]+(?:'[A-Za-z]+)*")
SENT_RE = re.compile(r"[^.!?\n]*[.!?]")


def episode_meta(path):
    b = os.path.basename(path)
    m = re.match(r"S(\d+)E(\d+)-(.+)\.txt", b)
    return int(m.group(1)), int(m.group(2)), m.group(3).replace("_", " ")


def main():
    files = sorted(glob.glob(os.path.join(TX, "*.txt")))
    total = Counter()                 # lowercased word -> total occurrences
    lower_mid = Counter()             # occurrences that were lowercase mid-sentence
    epcount = defaultdict(set)        # word -> set of episodes
    examples = {}                     # word -> example sentence
    per_season = defaultdict(Counter)
    tokens_total = 0

    for fi, path in enumerate(files):
        s, e, name = episode_meta(path)
        text = open(path, encoding="utf-8").read()
        # drop our 2-line header
        text = "\n".join(text.split("\n")[2:])
        sentences = SENT_RE.findall(text)
        # token-level pass for capitalization context
        for line in re.split(r"(?<=[.!?])\s+|\n", text):
            for ti, tok in enumerate(WORD_RE.findall(line)):
                low = clean_word(tok)
                if len(low) < 2 or not low.isalpha() or low in _JUNK:
                    continue
                total[low] += 1
                tokens_total += 1
                epcount[low].add((s, e))
                per_season[s][low] += 1
                if tok[0].islower() and ti > 0:   # lowercase, mid-sentence
                    lower_mid[low] += 1
        # example sentences
        for sent in sentences:
            clean = sent.strip()
            if not (4 <= len(clean.split()) <= 22):
                continue
            for tok in WORD_RE.findall(clean):
                low = clean_word(tok)
                if low and low not in examples and len(low) > 2:
                    examples[low] = (clean, s, e, name)

    print(f"files={len(files)} tokens={tokens_total} vocab={len(total)}")

    rows = []
    for w, c in total.items():
        if c < 2:                       # appears only once -> skip noise
            continue
        if not w.isalpha():
            continue
        # proper-noun filter: must appear lowercase mid-sentence at least twice
        # (unless it's a known Yiddish/loanword we want to keep)
        if w not in YIDDISH and lower_mid[w] < 2:
            continue
        zipf = zipf_frequency(w, "en")
        # learning value: recurring AND rare. peak interest zipf in [1.5, 4.0]
        rarity = max(0.0, 5.5 - zipf)
        recur = math.log(c + 1)
        score = round(rarity * recur, 3)
        # East-European difficulty: rare in English AND absent from EE languages.
        ee = ee_familiarity(w)
        unfamiliar = min(1.0, max(0.0, (3.0 - ee) / 3.0))  # 1=absent, 0=well known
        ee_score = round(rarity * recur * unfamiliar, 3)
        if w in COINAGE:
            cat = "coinage"
        elif w in YIDDISH:
            cat = "yiddish"
        elif w in INTERJECTIONS:
            cat = "interjection"
        elif zipf == 0:
            cat = "very-rare"
        elif zipf < 2.5:
            cat = "rare"
        elif zipf < 3.5:
            cat = "uncommon"
        else:
            cat = "common"
        ex = examples.get(w)
        ex_text = ex[0] if ex else ""
        ex_ep = f"S{ex[1]:02d}E{ex[2]:02d}" if ex else ""
        ex_title = ex[3] if ex else ""
        # all episodes the word appears in, chronological
        eps = sorted(f"S{a:02d}E{b:02d}" for a, b in epcount[w])
        rows.append({
            "word": w, "count": c, "episodes": len(epcount[w]),
            "zipf": round(zipf, 2), "score": score, "category": cat,
            "ee": round(ee, 2), "ee_score": ee_score,
            "example": ex_text, "ep": ex_ep, "ep_title": ex_title,
            "eps": eps, "def": define(w),
        })

    rows.sort(key=lambda r: r["score"], reverse=True)

    # --- aggregates for the dashboard ---
    # learner list = REAL uncommon dictionary words, recurring (exclude coinages
    # and zipf==0 non-words). These are the genuinely useful vocab to learn.
    learner = [r for r in rows if r["category"] in ("yiddish", "rare", "uncommon")
               and r["zipf"] >= 1.5 and r["count"] >= 3]
    cat_counts = Counter(r["category"] for r in rows)

    # East-European-hard: real recurring words that are absent / very rare in
    # East-European languages (no loanword, no cognate to fall back on).
    for r in rows:
        r["ee_hard"] = bool(r["ee"] < 2.0 and r["zipf"] >= 1.5
                            and r["count"] >= 3 and r["category"] != "coinage"
                            and r["def"])
    ee_hard = sorted([r for r in rows if r["ee_hard"]],
                     key=lambda r: r["ee_score"], reverse=True)

    # Rare words: the most obscure / literary REAL English words in the show.
    # Real = has a WordNet definition (filters coinages, names, junk). Sorted
    # rarest-first (lowest Zipf), tie-broken by how often the show uses them.
    rare = sorted(
        [r for r in rows if r["def"] and r["zipf"] <= 3.0
         and r["category"] not in ("coinage", "interjection")],
        key=lambda r: (r["zipf"], -r["count"]))

    # --- idiom / phrasal-expression scan over the raw corpus ---
    fulltext = " ".join(
        " ".join(open(f, encoding="utf-8").read().split("\n")[2:]).lower()
        for f in files)
    fulltext = re.sub(r"[^a-z' ]", " ", fulltext.replace("’", "'"))
    fulltext = re.sub(r"\s+", " ", fulltext)
    idiom_rows = []
    for phrase in IDIOMS:
        n = fulltext.count(" " + phrase + " ")
        if n:
            idiom_rows.append({"phrase": phrase, "count": n})
    idiom_rows.sort(key=lambda r: r["count"], reverse=True)
    # zipf histogram over learner-relevant vocabulary
    zbins = Counter()
    for r in rows:
        zbins[round(r["zipf"] * 2) / 2] += 1  # 0.5 buckets
    yiddish_rows = [r for r in rows if r["category"] == "yiddish"]

    data = {
        "stats": {
            "episodes": len(files), "tokens": tokens_total,
            "vocab": len(total), "analyzed": len(rows),
            "learner_words": len(learner), "ee_hard_words": len(ee_hard),
            "rare_words": len(rare),
        },
        "learner": learner[:400],
        "ee_hard": ee_hard[:400],
        "rare": rare[:400],
        "all_rows": rows,
        "categories": dict(cat_counts),
        "zipf_hist": dict(sorted(zbins.items())),
        "yiddish": sorted(yiddish_rows, key=lambda r: r["count"], reverse=True),
        "coinage": sorted([r for r in rows if r["category"] == "coinage"],
                          key=lambda r: r["count"], reverse=True),
        "idioms": idiom_rows,
        "top_scatter": [r for r in rows if r["count"] >= 3][:1500],
    }
    json.dump(data, open(OUT, "w"), ensure_ascii=False)
    with open("data.js", "w", encoding="utf-8") as f:
        f.write("window.DATA = ")
        json.dump(data, f, ensure_ascii=False)
        f.write(";")
    print(f"wrote {OUT}: analyzed={len(rows)} learner={len(learner)} "
          f"ee_hard={len(ee_hard)} rare={len(rare)} yiddish={len(yiddish_rows)}")
    print("top 15 learner words:",
          ", ".join(f"{r['word']}({r['count']})" for r in learner[:15]))
    print("top 15 EE-hard words:",
          ", ".join(f"{r['word']}(ee{r['ee']})" for r in ee_hard[:15]))
    print("top 15 rare words:",
          ", ".join(f"{r['word']}(z{r['zipf']})" for r in rare[:15]))


if __name__ == "__main__":
    main()
