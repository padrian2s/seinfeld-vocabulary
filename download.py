#!/usr/bin/env python3
"""Download every Seinfeld episode transcript from subslikescript.com."""
import os, re, sys, time, html, urllib.request, urllib.error

BASE = "https://subslikescript.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
OUTDIR = "transcripts"


def fetch(url, retries=4):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            wait = 2 * (i + 1)
            print(f"    retry {i+1} after error: {e} (sleep {wait}s)")
            time.sleep(wait)
    return None


def extract_transcript(page):
    # Transcript lives in <div class="full-script">...</div>
    m = re.search(r'<div[^>]*class="[^"]*full-script[^"]*"[^>]*>(.*?)</div>', page, re.S)
    if not m:
        return None
    body = m.group(1)
    body = re.sub(r'<br\s*/?>', '\n', body)       # line breaks
    body = re.sub(r'<[^>]+>', '', body)            # strip remaining tags
    body = html.unescape(body)
    body = re.sub(r'\n[ \t]+', '\n', body)
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    return body


def main():
    links = [l.strip() for l in open("links.txt") if l.strip()]
    os.makedirs(OUTDIR, exist_ok=True)
    ok = fail = skip = 0
    for i, path in enumerate(sorted(links, key=lambda p: (
            int(re.search(r'season-(\d+)', p).group(1)),
            int(re.search(r'episode-(\d+)', p).group(1)))), 1):
        season = re.search(r'season-(\d+)', path).group(1)
        epm = re.search(r'episode-(\d+)-(.+)$', path)
        epnum, name = epm.group(1), epm.group(2)
        fname = f"S{int(season):02d}E{int(epnum):02d}-{name}.txt"
        fpath = os.path.join(OUTDIR, fname)
        if os.path.exists(fpath) and os.path.getsize(fpath) > 200:
            skip += 1
            continue
        print(f"[{i}/{len(links)}] {fname}")
        page = fetch(BASE + path)
        if not page:
            fail += 1
            print("    FAILED to fetch")
            continue
        text = extract_transcript(page)
        if not text or len(text) < 200:
            fail += 1
            print("    no transcript found")
            continue
        title = re.search(r'<title>([^<]*)</title>', page)
        header = (title.group(1).strip() if title else fname) + "\n" + "=" * 60 + "\n\n"
        with open(fpath, "w") as f:
            f.write(header + text + "\n")
        ok += 1
        time.sleep(1)  # be polite
    print(f"\nDone. downloaded={ok} skipped={skip} failed={fail} total={len(links)}")


if __name__ == "__main__":
    main()
