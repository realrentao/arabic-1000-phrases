# -*- coding: utf-8 -*-
"""Generate edge-tts MP3 audio (ar-AE female) for every unique Arabic phrase.

Dedupes by Arabic text, runs concurrently with retries, supports resume
(skips files already present). Outputs js/audio.js mapping arabic -> path.
"""
import os, sys, json, hashlib, asyncio, time

import edge_tts

OUT_DIR = r"D:\workbuddy工作区\2026-07-09-22-10-17\arabic1000"
LOG_PATH = os.path.join(OUT_DIR, "gen_audio.log")

_logf = open(LOG_PATH, "a", encoding="utf-8")
def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    _logf.write(s + "\n")
    _logf.flush()
DATA_JSON = os.path.join(OUT_DIR, "data.json")
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
AUDIO_JS = os.path.join(OUT_DIR, "js", "audio.js")

VOICE = "ar-AE-FatimaNeural"   # UAE female
CONCURRENCY = 40
RETRIES = 4
BACKOFF = 1.5

def hash_name(text):
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    return h + ".mp3"

def collect_texts():
    with open(DATA_JSON, encoding="utf-8") as f:
        data = json.load(f)
    seen = {}
    for s in data["sections"]:
        for r in s["rows"]:
            for key, d in r.get("dialects", {}).items():
                ar = d.get("ar", "").strip()
                if ar:
                    seen.setdefault(ar, hash_name(ar))
    return seen  # ar -> filename

async def gen_one(ar, fname, sem, stats):
    path = os.path.join(AUDIO_DIR, fname)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        stats["skip"] += 1
        return True
    delay = BACKOFF
    for attempt in range(RETRIES):
        try:
            async with sem:
                comm = edge_tts.Communicate(ar, VOICE)
                await comm.save(path)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                stats["ok"] += 1
                return True
            else:
                stats["empty"] += 1
                return False
        except Exception as e:
            if attempt < RETRIES - 1:
                await asyncio.sleep(delay)
                delay *= 1.8
            else:
                stats["fail"] += 1
                sys.stderr.write(f"\nFAIL [{ar[:30]}] {e}\n")
                return False

async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    texts = collect_texts()
    total = len(texts)
    log(f"Total unique Arabic phrases: {total}")
    sem = asyncio.Semaphore(CONCURRENCY)
    stats = {"ok": 0, "skip": 0, "fail": 0, "empty": 0}
    start = time.time()
    tasks = [gen_one(ar, fn, sem, stats) for ar, fn in texts.items()]
    done = 0
    for coro in asyncio.as_completed(tasks):
        await coro
        done += 1
        if done % 100 == 0:
            el = time.time() - start
            log(f"  progress {done}/{total}  ok={stats['ok']} skip={stats['skip']} fail={stats['fail']}  ({el:.0f}s)")
    # build map only for successfully generated
    amap = {}
    for ar, fn in texts.items():
        p = os.path.join(AUDIO_DIR, fn)
        if os.path.exists(p) and os.path.getsize(p) > 0:
            amap[ar] = "audio/" + fn
    with open(AUDIO_JS, "w", encoding="utf-8") as f:
        f.write("// Auto-generated: arabic text -> audio path (ar-AE Fatima)\n")
        f.write("const AUDIO_MAP = ")
        json.dump(amap, f, ensure_ascii=False, indent=1)
        f.write(";\n")
    el = time.time() - start
    log(f"DONE in {el:.0f}s | ok={stats['ok']} skip={stats['skip']} fail={stats['fail']} empty={stats['empty']}")
    log(f"Audio files written: {len(amap)} -> {AUDIO_JS}")

if __name__ == "__main__":
    asyncio.run(main())
