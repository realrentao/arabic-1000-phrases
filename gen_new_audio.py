# -*- coding: utf-8 -*-
"""为 6 方言细分后新增的阿拉伯语文本补 edge-tts 配音。

- 只生成 new_texts.json 里的新文本，已有 3224 条音频不动
- 音色沿用原项目 ar-AE-FatimaNeural（阿联酋女声）
- 文件名 / 映射规则与仓库 gen_audio.py 完全一致：sha1(ar)[:12].mp3
- 生成完成后重写 js/audio.js：原有映射 + 成功生成的新映射
"""
import os, json, asyncio, hashlib, sys

import edge_tts

BASE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE, "audio")
AUDIO_JS = os.path.join(BASE, "js", "audio.js")
VOICE = "ar-AE-FatimaNeural"
CONCURRENCY = 12
RETRIES = 3


def hash_name(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12] + ".mp3"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


async def gen_one(text, sem, stats):
    path = os.path.join(AUDIO_DIR, hash_name(text))
    if os.path.exists(path) and os.path.getsize(path) > 0:
        stats["skip"] += 1
        return True
    for attempt in range(RETRIES):
        try:
            async with sem:
                await edge_tts.Communicate(text, VOICE).save(path)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                stats["ok"] += 1
                return True
        except Exception as e:
            if attempt == RETRIES - 1:
                print("FAIL", repr(text[:40]), e, flush=True)
            else:
                await asyncio.sleep(1.2 * (attempt + 1))
    stats["fail"] += 1
    return False


async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    new_texts = load_json(os.path.join(BASE, "new_texts.json"))
    orig = load_json(os.path.join(BASE, "data.json.orig"))
    old_texts = set()
    for s in orig["sections"]:
        for r in s["rows"]:
            for d in r["dialects"].values():
                if d.get("ar"):
                    old_texts.add(d["ar"])

    print("new texts:", len(new_texts), "| existing texts:", len(old_texts), flush=True)
    sem = asyncio.Semaphore(CONCURRENCY)
    stats = {"ok": 0, "skip": 0, "fail": 0}
    tasks = [gen_one(t, sem, stats) for t in new_texts]
    done = 0
    for coro in asyncio.as_completed(tasks):
        await coro
        done += 1
        if done % 25 == 0:
            print("  progress", done, "/", len(new_texts), stats, flush=True)

    # 原有映射（线上仓库已有音频）+ 成功生成的新映射
    amap = {t: "audio/" + hash_name(t) for t in old_texts}
    added = 0
    for t in new_texts:
        p = os.path.join(AUDIO_DIR, hash_name(t))
        if os.path.exists(p) and os.path.getsize(p) > 0:
            amap[t] = "audio/" + hash_name(t)
            added += 1
    with open(AUDIO_JS, "w", encoding="utf-8") as f:
        f.write("// Auto-generated: arabic text -> audio path (ar-AE Fatima)\n")
        f.write("const AUDIO_MAP = ")
        json.dump(dict(sorted(amap.items())), f, ensure_ascii=False, indent=1)
        f.write(";\n")
    print("DONE", stats, "| new audio mapped:", added, "| total map:", len(amap), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
