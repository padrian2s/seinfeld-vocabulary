# Seinfeld Vocabulary Explorer

An EDA dashboard of the vocabulary across all 9 seasons of *Seinfeld*, built for the
**non-native (East-European) English learner**. It surfaces the words that are
*uncommon in everyday English yet recur across the show* — the high-value vocabulary
worth learning — and flags the ones that are genuinely hard for an East-European
speaker.

👉 **Live dashboard:** open `index.html` (or the GitHub Pages URL).

## What it shows

- **Rarity distribution** of the show's vocabulary (wordfreq Zipf scale).
- **The "learning gap"** — words frequent in the show but rare in English.
- **🇷🇴🇵🇱🇷🇺 East-European difficulty** — words absent from East-European languages
  (ro/pl/ru/cs/hu/bg/uk/sk), so there's no loanword or cognate to fall back on
  (e.g. *armoire, goiter, kibosh, doofus*). Words like *weekend* or *babka* are
  excluded because they already exist in those languages.
- **Show coinages** (festivus, shrinkage…) kept separate from real dictionary words.
- **Conversational idioms / phrasal verbs** — the hardest part for non-natives.
- A **sortable, searchable vocabulary table** with WordNet definitions on hover.

## How it works

```
download.py   # scrape all 172 episode transcripts from subslikescript.com
analyze.py    # tokenize, score rarity (wordfreq) + EE difficulty + WordNet defs
              #   -> data.js   (consumed by the dashboard)
index.html    # self-contained Plotly dashboard (no server needed)
```

Regenerate the data:

```bash
pip install wordfreq nltk
python3 -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
python3 download.py    # writes transcripts/  (not committed — copyright)
python3 analyze.py     # writes data.js
```

## Note on data

Raw episode transcripts are **not** included in this repo (copyright). The dashboard
runs entirely off `data.js`, which contains aggregate word statistics and short
single-line examples. Transcripts are sourced from
[subslikescript.com](https://subslikescript.com/series/Seinfeld-98904).

Rarity via [wordfreq](https://github.com/rspeer/wordfreq) · definitions via WordNet (nltk) · charts via Plotly.
