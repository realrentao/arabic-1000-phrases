# -*- coding: utf-8 -*-
"""把 arabic-1000-phrases 的 4 方言对照细分为 6 方言。

原分类：① 标准语 / ② 埃及 / ③ 黎凡特·海湾(合并) / ④ 马格里布
新分类：① 标准 / ② 埃及 / ③ 黎凡特 / ④ 海湾 / ⑤ 伊拉克 / ⑥ 马格里布

④⑤ 以原 ③ 为基线，按高置信度方言差异词表派生；未命中差异词时
说明各方言说法本就一致，直接沿用原 ③（含原有音频，零重复配音）。
派生过的句子 note 标为「派」，前端显示徽章提示核对。

输出：data.json / js/data.js / js/audio.js / new_texts.json
"""
import json, re, os, hashlib, collections

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "data.json.orig")

HARAKAT = re.compile("[\u064B-\u0652\u0670\u0640]")


def strip_h(s):
    return HARAKAT.sub("", s)


def make_replacer(table, bound_l, bound_r):
    keys = sorted(table, key=len, reverse=True)
    pat = re.compile(bound_l + "(" + "|".join(re.escape(k) for k in keys) + ")" + bound_r)
    return lambda t: pat.sub(lambda m: table[m.group(1)], t)


# 注意：边界只能用「阿拉伯字母」，不能用整个 Arabic block——
# U+061F «؟»（阿拉伯问号）也在 U+0600-06FF 内，会挡住词尾匹配。
AR_LETTERS = (r"\u0621-\u063A\u0641-\u064A\u066E-\u066F\u0671-\u06D3\u06D5"
              r"\u06EE-\u06EF\u06FA-\u06FC\u06FF\u0750-\u077F"
              r"\uFB50-\uFBB1\uFBD3-\uFD3D\uFD50-\uFDFB\uFE70-\uFEFC")
AR_L = r"(?<![" + AR_LETTERS + r"])"
AR_R = r"(?![" + AR_LETTERS + r"])"
ROM_L = r"(?<!\w)"
ROM_R = r"(?!\w)"

# ---------------------------------------------------------------- 海湾
GULF_AR = {
    "كيفك": "شلونك", "كيف": "شلون",
    "شو": "شنو", "إيش": "شنو", "ايش": "شنو",
    "بدي": "أبي", "بدك": "تبي", "بدنا": "نبي", "بدو": "يبي",
    "بدها": "تبي", "بدهم": "يبون", "بديها": "أبيها",
    "كتير": "وايد", "كتيرة": "وايدة",
    "مش": "مو",
    "هاد": "هذا", "هاي": "هذي", "هيدا": "هذا", "هيدي": "هذي",
    "هون": "هنا",
    "هلأ": "الحين", "هلق": "الحين", "هلأء": "الحين",
    "منيح": "زين", "منيحة": "زينة",
    "هيك": "كذا",
    "قديش": "كم", "قدّيش": "كم",
    "إمتى": "متى", "إيمتى": "متى",
    "شوي": "شوي",
}
GULF_ROM = {
    "kīfak": "shlūnak", "kīfik": "shlūnik", "kīf": "shlūn", "kayf": "shlūn",
    "shū": "shinū", "sho": "shinū", "ēsh": "shinū",
    "baddī": "abī", "baddi": "abī",
    "biddī": "abī", "biddi": "abī", "biddak": "tibī", "biddik": "tibīn",
    "biddna": "nibī", "biddo": "yibī", "biddha": "tibī", "biddhum": "yibūn",
    "ktīr": "wāyid", "ktīra": "wāyda", "ktir": "wāyid",
    "mish": "mū",
    "hād": "hādhā", "hāy": "hādhī", "hēda": "hādhā", "hēdi": "hādhī",
    "hūn": "hinā", "hōn": "hinā",
    "hallaq": "al-ḥīn", "halla'": "al-ḥīn", "hallaʾ": "al-ḥīn", "halla": "al-ḥīn",
    "mnīḥa": "zayna", "mnīḥ": "zayn",
    "hēk": "kadhā",
    "qaddēsh": "kam", "qaddēš": "kam",
    "īmtā": "matā", "imtā": "matā", "imta": "matā", "mtā": "matā",
}

# ---------------------------------------------------------------- 伊拉克
IRAQI_AR = {
    "كيفك": "شلونك", "كيف": "شلون",
    "شو": "شنو", "إيش": "شنو", "ايش": "شنو",
    "بدي": "أريد", "بدك": "تريد", "بدنا": "نريد", "بدو": "يريد",
    "بدها": "تريد", "بدهم": "يريدون", "بديها": "أريدها",
    "كتير": "هواية", "كتيرة": "هواية",
    "مش": "مو",
    "هاد": "هذا", "هاي": "هذي", "هيدا": "هذا", "هيدي": "هذي",
    "هون": "هنا",
    "هلأ": "هسه", "هلق": "هسه",
    "منيح": "زين", "منيحة": "زينة",
    "هيك": "هيچ",
    "قديش": "كم", "قدّيش": "كم",
    "إمتى": "متى", "إيمتى": "متى",
    "شوي": "شوية", "ما في": "ماكو", "مافي": "ماكو",
}
IRAQI_ROM = {
    "kīfak": "shlūnak", "kīfik": "shlūnik", "kīf": "shlūn", "kayf": "shlūn",
    "shū": "shinū", "sho": "shinū", "ēsh": "shinū",
    "baddī": "arīd", "baddi": "arīd",
    "biddī": "arīd", "biddi": "arīd", "biddak": "trīd", "biddik": "trīdīn",
    "biddna": "nrīd", "biddo": "yrīd", "biddha": "trīd", "biddhum": "yrīdūn",
    "ktīr": "hwāya", "ktīra": "hwāya", "ktir": "hwāya",
    "mish": "mū",
    "hād": "hādhā", "hāy": "hādhī", "hēda": "hādhā", "hēdi": "hādhī",
    "hūn": "hinā", "hōn": "hinā",
    "hallaq": "hasse", "halla'": "hasse", "hallaʾ": "hasse", "halla": "hasse",
    "mnīḥa": "zayna", "mnīḥ": "zayn",
    "hēk": "hīč",
    "qaddēsh": "kam", "qaddēš": "kam",
    "īmtā": "matā", "imtā": "matā", "imta": "matā", "mtā": "matā",
    "shway": "shwayya", "mā fī": "māku", "māfi": "māku", "ma fī": "māku",
}

gulf_ar = make_replacer(GULF_AR, AR_L, AR_R)
iraqi_ar = make_replacer(IRAQI_AR, AR_L, AR_R)
gulf_rom = make_replacer(GULF_ROM, ROM_L, ROM_R)
iraqi_rom = make_replacer(IRAQI_ROM, ROM_L, ROM_R)


def derive(src, ar_fn, rom_fn):
    """返回 (ar, rom, changed)。changed=False 表示各方言说法一致，直接沿用。"""
    plain = strip_h(src["ar"])
    new_ar = ar_fn(plain)
    new_rom = rom_fn(src.get("rom", ""))
    changed = new_ar != plain
    if not changed:
        return src["ar"], src.get("rom", ""), False
    return new_ar, new_rom, True


# 原库「问候与礼貌」章缺失的两句：阿语世界最经典的问候与回礼。
# 这两句是跨方言统一的宗教问候语，写法各方言基本一致，差异主要在读音，
# 故阿文只按站内惯例区分「MSA 带完整尾符 / 方言口语简写」，罗马化标出实际读法。
GREETING_ROWS = [
    {
        "cn": "愿平安降临于你（阿语世界经典问候）",
        "dialects": {
            "msa":       {"ar": "اَلسَّلَامُ عَلَيْكُمْ", "rom": "as-salāmu ʿalaykum", "note": ""},
            "egyptian":  {"ar": "اَلسَّلَامُ عَلَيْكُم",  "rom": "assalāmu ʿalēkum",  "note": ""},
            "levantine": {"ar": "اَلسَّلَامُ عَلَيْكُم",  "rom": "as-salāmu ʿalēkum", "note": ""},
            "gulf":      {"ar": "اَلسَّلَامُ عَلَيْكُم",  "rom": "as-salāmu ʿalaykum", "note": ""},
            "iraqi":     {"ar": "اَلسَّلَامُ عَلَيْكُم",  "rom": "salāmu ʿalaykum",  "note": ""},
            "maghreb":   {"ar": "اَلسَّلَامُ عَلَيْكُم",  "rom": "s-salāmu ʿlīkum",  "note": ""},
        },
    },
    {
        "cn": "也愿平安降临于你（标准回礼）",
        "dialects": {
            "msa":       {"ar": "وَعَلَيْكُمُ السَّلَامُ", "rom": "wa ʿalaykumu s-salām",  "note": ""},
            "egyptian":  {"ar": "وَعَلَيْكُمُ السَّلَام",  "rom": "wa ʿalēkumu s-salām",   "note": ""},
            "levantine": {"ar": "وَعَلَيْكُمُ السَّلَام",  "rom": "wa ʿalēkum is-salām",  "note": ""},
            "gulf":      {"ar": "وَعَلَيْكُمُ السَّلَام",  "rom": "wa ʿalaykumu s-salām", "note": ""},
            "iraqi":     {"ar": "وَعَلَيْكُمُ السَّلَام",  "rom": "wa ʿalaykumu s-salām", "note": ""},
            "maghreb":   {"ar": "وَعَلَيْكُمُ السَّلَام",  "rom": "wa ʿlīkum s-salām",    "note": ""},
        },
    },
]


# 在「你好吗？（对男）」正下方补入对应的「对女」版本。
# 口语里问候分男女：标准语 حَالُكِ、埃及 إِزَّيِّك、黎凡特 كِيفِك、
# 海湾/伊拉克 شلونكِ、马格里布 دَايْرَة；海湾/伊拉克为从黎凡特变体派生，标「派」。
FEMALE_HOWAREYOU = {
    "msa":       {"ar": "كَيْفَ حَالُكِ؟",  "rom": "kayfa ḥāluki",  "note": ""},
    "egyptian":  {"ar": "إِزَّيِّك؟",      "rom": "izzayyik",      "note": ""},
    "levantine": {"ar": "كِيفِك؟",        "rom": "kīfik",         "note": ""},
    "gulf":      {"ar": "شلونكِ؟",        "rom": "shlūnik",       "note": "派"},
    "iraqi":     {"ar": "شلونكِ؟",        "rom": "shlūnik",       "note": "派"},
    "maghreb":   {"ar": "كِيفَ دَايْرَة؟", "rom": "kīf dāyra",     "note": ""},
}


# 「你好吗？（对男）」逐方言核对结论（用户人工核验，全部确认正确）。
# 写入各方言 dialect 的 verify 字段，前端以弱提示文案呈现，仅作质量留痕。
VERIFY_MALE = {
    "msa":       "✅ 完全标准",
    "egyptian":  "✅ 正确（对男性）",
    "levantine": "✅ 正确（黎长音 ī）",
    "gulf":      "✅ 正确",
    "iraqi":     "✅ 正确",
    "maghreb":   "✅ 对（指摩洛哥 Darija）",
}

# 「你好吗？（对女）」按用户核验表更新（阴性词尾）：
VERIFY_FEMALE = {
    "msa":       "✅ 标准阴性",
    "egyptian":  "✅ 埃及地道（女）",
    "levantine": "✅ 黎凡特地道（女）",
    "gulf":      "✅ 海湾地道（女）",
    "iraqi":     "✅ 伊拉克地道（女）",
    "maghreb":   "✅ 摩洛哥地道（女），补了转写",
}


# 「你好（通用）」按用户核验表更新：
# 原库 4 方言（黎/海湾/伊拉克/马格里布）都误填成通用词 marḥaba，
# 现改为各地道口语 hello，并补「字面 / 味道」flavor 说明。
# 伊拉克用户给了 hala / halo 两式，取通用 hala 为正文，halo 写入 flavor。
HELLO_GENERAL = {
    "msa":       {"ar": "مَرْحَباً", "rom": "marḥaban",
                  "flavor": "“愿你宽裕/欢迎”，教科书标准款"},
    "egyptian":  {"ar": "أَهْلَا", "rom": "ahlan",
                  "flavor": "“你像家人一样”，埃及人开口就这句（口语念 ahlā）"},
    "levantine": {"ar": "هَلَا", "rom": "hala",
                  "flavor": "由 ahlan 缩读而来，黎/叙/约/巴的亲切口语"},
    "gulf":      {"ar": "هَلَا وَالله", "rom": "hala wallah",
                  "flavor": "“以真主之名欢迎你”，海湾最热情的招牌"},
    "iraqi":     {"ar": "هَلَا", "rom": "hala",
                  "flavor": "通用；هلو (halo) 借自英语 hello，市井味"},
    "maghreb":   {"ar": "سَلَام", "rom": "salam",
                  "flavor": "摩洛哥/西北非日常的极简 hello"},
}


# 「再见」按用户核验表更新：
# 原库 6 方言全填成通用 maʿa as-salāma（马格里布误作 b-is-salāma），
# 现改为各地道道别语，并补「字面 / 味道」flavor 说明。
# 伊拉克用户明确「暂无专属个性款，宁可空缺不硬凑」——ar 留空字符串，
# 仅保留 flavor 说明；前端 dialectCell 对空 ar 渲染「—」占位 + flavor。
BYE_GENERAL = {
    "msa":       {"ar": "مَعَ السَّلَامَةِ", "rom": "maʿa as-salāma",
                  "flavor": "“伴随平安”——标准语本身就是代表款"},
    "egyptian":  {"ar": "يَلَّا بِي", "rom": "yalla bi",
                  "flavor": "“走吧（bye）”——埃及最溜嘴的市井道别",
                  "ar2": "الله يسلمك", "rom2": "allāh yisallimak"},
    "levantine": {"ar": "يَلَّا سَلَام", "rom": "yalla salām",
                  "flavor": "“走吧，平安”——轻快收尾"},
    "gulf":      {"ar": "اَلله يَحْفَظَك", "rom": "allāh yaḥfaẓak",
                  "flavor": "“愿真主保佑你”——海湾待客暖心祝福"},
    "iraqi":     {"ar": "مَعَ السَّلَامَةِ", "rom": "maʿa as-salāma",
                  "flavor": "伊拉克日常即用标准语的 maʿa as-salāma（用户确认；原留空处已填）"},
    "maghreb":   {"ar": "سَلَام", "rom": "salam",
                  "flavor": "“平安”——摩洛哥极简主义，甩一个就走 🐪"},
}


# 「谢谢」按用户核验表精细化：
# 通用款 شُكْراً（shukran）全方言都懂，作为每格主形；
# 各方言另有「个性款」口语，作为 ar2 第二形式（含男女变体标注于 rom2 / flavor）。
THANKS = {
    "msa":       {"ar": "شُكْراً", "rom": "shukran", "ar2": None, "rom2": None,
                  "flavor": "标准形式，全方言通用——「谢谢」"},
    "egyptian":  {"ar": "شُكْراً", "rom": "shukran", "ar2": "مُتَشَكِّر", "rom2": "mutashakkir(男)/mutashakkira(女)",
                  "flavor": "「我感谢」——埃及地道个性款（对应通用 shukran）"},
    "levantine": {"ar": "شُكْراً", "rom": "shukran", "ar2": "بِتْشَكَّرِك", "rom2": "betshakkarak(男)/betshakkarek(女)",
                  "flavor": "「我谢你」——黎凡特地道个性款"},
    "gulf":      {"ar": "شُكْراً", "rom": "shukran", "ar2": "مَشْكُور", "rom2": "mashkūr(男)/mashkūrah(女)",
                  "flavor": "「你值得谢」——海湾地道个性款"},
    "iraqi":     {"ar": "شُكْراً", "rom": "shukran", "ar2": "مَشْكُور", "rom2": "mashkūr「你值得谢」（同海湾）",
                  "flavor": "同海湾 mashkūr，伊拉克日常即此"},
    "maghreb":   {"ar": "شُكْراً", "rom": "shukran", "ar2": "مِيرْسِي", "rom2": "merci（法语借词）",
                  "flavor": "亦常用 بَارَكَ الله فِيك「愿主祝福你」"},
}

WELCOME_BACK = {
    "msa":       {"ar": "عَفْواً", "rom": "ʿafwan", "ar2List": None,
                  "flavor": "标准形式（通用中性款），全方言通用——「不用谢」"},
    "egyptian":  {"ar": "عَفْواً", "rom": "ʿafwan",
                  "ar2List": [
                      {"ar": "مَعْلِيش", "rom": "maʿlēsh「没事」"},
                      {"ar": "ولا يهمك", "rom": "wala yhemmak「也没关系/别放心上」"},
                  ],
                  "flavor": "埃及地道个性款：مَعْلِيش 最常见，wala yhemmak 亦常用"},
    "levantine": {"ar": "عَفْواً", "rom": "ʿafwan",
                  "ar2List": [
                      {"ar": "تِكْرَم", "rom": "tikram(男)/tikrami(女)「我的荣幸」；ʿalēk 也行"},
                  ],
                  "flavor": "黎凡特地道个性款"},
    "gulf":      {"ar": "عَفْواً", "rom": "ʿafwan",
                  "ar2List": [
                      {"ar": "عَلِيهْ", "rom": "ʿalēh「没什么/为你」"},
                      {"ar": "مَا عَلَيْه", "rom": "mā ʿalayh「没什么/为你」"},
                  ],
                  "flavor": "海湾地道个性款"},
    "iraqi":     {"ar": "عَفْواً", "rom": "ʿafwan",
                  "ar2List": [
                      {"ar": "عَلِيهْ", "rom": "ʿalēh「没什么/为你」（同海湾）"},
                  ],
                  "flavor": "同海湾 ʿalēh，伊拉克日常即此"},
    "maghreb":   {"ar": "عَفْواً", "rom": "ʿafwan",
                  "ar2List": [
                      {"ar": "مَاشِي مُشْكِيل", "rom": "māshī mushkīl「没问题」"},
                      {"ar": "بْلَا جَمِيل", "rom": "bla jmīl「不足挂齿」"},
                  ],
                  "flavor": "马格里布地道个性款"},
}


def hash_name(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12] + ".mp3"


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)

    old_texts = set()
    for s in data["sections"]:
        for r in s["rows"]:
            for d in r["dialects"].values():
                if d.get("ar"):
                    old_texts.add(d["ar"])

    # 原库勘误（须在 old_texts 收集之后应用，使勘误文本进入 new_texts 补配音）：
    # #6「晚安」标准语误将 ص（ṣ）写作 س（s）。动词为 صَبَحَ（醒来），
    # سَبَحَ 意为「游泳」；规范写法 تُصْبَحُ عَلَى خَيْرٍ（tuṣbaḥu ʿalā khayrin）。
    # 注：马格里布列 تسبح/س 为有意记音——Darija 咽化 ص 磨平为 s，读 tsbaḥ，保留。
    CORRECTIONS = {
        "晚安": {"msa": {"ar": "تُصْبَحُ عَلَى خَيْرٍ", "rom": "tuṣbaḥu ʿalā khayrin"}},
    }
    fixed = 0
    for s in data["sections"]:
        for r in s["rows"]:
            fix = CORRECTIONS.get(r["cn"])
            if fix:
                for k, v in fix.items():
                    r["dialects"][k].update(v)
                    fixed += 1
    if fixed:
        print("corrections applied:", fixed)

    stats = collections.Counter()
    new_texts = set()

    for s in data["sections"]:
        for r in s["rows"]:
            dl = r["dialects"]
            lev = dl["levantine"]

            g_ar, g_rom, g_ch = derive(lev, gulf_ar, gulf_rom)
            i_ar, i_rom, i_ch = derive(lev, iraqi_ar, iraqi_rom)

            dl["gulf"] = {"ar": g_ar, "rom": g_rom, "note": "派" if g_ch else ""}
            dl["iraqi"] = {"ar": i_ar, "rom": i_rom, "note": "派" if i_ch else ""}
            # 按新顺序重排，保证 js 输出顺序稳定
            r["dialects"] = {k: dl[k] for k in
                             ["msa", "egyptian", "levantine", "gulf", "iraqi", "maghreb"]}

            # 移除原文「最通用/最口语」推荐标注（含字段本身）
            r.pop("common", None)
            stats["gulf_derived" if g_ch else "gulf_same"] += 1
            stats["iraqi_derived" if i_ch else "iraqi_same"] += 1
            for t in (g_ar, i_ar):
                if t and t not in old_texts:
                    new_texts.add(t)

    # 在「问候与礼貌」章首补入两句经典问候/回礼，并全库重编号保持 1..N 连续
    sec0 = data["sections"][0]
    extra = [{"cn": r["cn"],
              "dialects": {k: dict(v) for k, v in r["dialects"].items()}}
             for r in GREETING_ROWS]
    sec0["rows"] = extra + sec0["rows"]

    # 在「你好吗？（对男）」正下方补入对应的「对女」版本
    male_n = "你好吗？（对男）"
    female_row = {"cn": "你好吗？（对女）",
                  "dialects": {k: dict(v) for k, v in FEMALE_HOWAREYOU.items()}}
    for idx, r in enumerate(sec0["rows"]):
        if r["cn"] == male_n:
            sec0["rows"].insert(idx + 1, female_row)
            for k, v in VERIFY_MALE.items():
                if k in r["dialects"]:
                    r["dialects"][k]["verify"] = v
            for k, v in VERIFY_FEMALE.items():
                if k in female_row["dialects"]:
                    female_row["dialects"][k]["verify"] = v
            break

    # 「你好（通用）」按用户核验表更新：4 方言改为地道口语 hello，并补 flavor
    for s in data["sections"]:
        for r in s["rows"]:
            if r["cn"] == "你好（通用）":
                for k, v in HELLO_GENERAL.items():
                    if k in r["dialects"]:
                        r["dialects"][k]["ar"] = v["ar"]
                        r["dialects"][k]["rom"] = v["rom"]
                        r["dialects"][k]["flavor"] = v["flavor"]
                break

    # 「再见」按用户核验表更新：6 方言改为地道道别语，并补 flavor；
    # 伊拉克用标准语 maʿa as-salāma 填空（用户确认）；埃及另加第二形式 ar2=الله يسلمك。
    for s in data["sections"]:
        for r in s["rows"]:
            if r["cn"] == "再见":
                for k, v in BYE_GENERAL.items():
                    if k in r["dialects"]:
                        r["dialects"][k]["ar"] = v["ar"]
                        r["dialects"][k]["rom"] = v["rom"]
                        r["dialects"][k]["flavor"] = v["flavor"]
                        if v.get("ar2") is not None:
                            r["dialects"][k]["ar2"] = v["ar2"]
                        if v.get("rom2") is not None:
                            r["dialects"][k]["rom2"] = v["rom2"]
                break

    # 「谢谢」按用户核验表精细化：通用款 شُكْراً 作主形（全方言通用），
    # 各方言个性款作 ar2 第二形式；男女变体标注于 rom2 / flavor。
    for s in data["sections"]:
        for r in s["rows"]:
            if r["cn"] == "谢谢":
                for k, v in THANKS.items():
                    if k in r["dialects"]:
                        r["dialects"][k]["ar"] = v["ar"]
                        r["dialects"][k]["rom"] = v["rom"]
                        r["dialects"][k]["flavor"] = v["flavor"]
                        if v.get("ar2") is not None:
                            r["dialects"][k]["ar2"] = v["ar2"]
                            r["dialects"][k]["rom2"] = v["rom2"]
                        else:
                            r["dialects"][k].pop("ar2", None)
                            r["dialects"][k].pop("rom2", None)
                break

    # 「不客气」按用户核验表精细化：通用款 عَفْواً(ʿafwan) 作主形（全方言通用），
    # 各方言个性款作 ar2List 第二形式（埃及/马格里布各两款）；男女变体标注于 rom / flavor。
    for s in data["sections"]:
        for r in s["rows"]:
            if r["cn"] == "不客气":
                for k, v in WELCOME_BACK.items():
                    if k in r["dialects"]:
                        r["dialects"][k]["ar"] = v["ar"]
                        r["dialects"][k]["rom"] = v["rom"]
                        r["dialects"][k]["flavor"] = v["flavor"]
                        if v.get("ar2List") is not None:
                            r["dialects"][k]["ar2List"] = v["ar2List"]
                        else:
                            r["dialects"][k].pop("ar2List", None)
                        # 清理旧的单一 ar2/rom2（若有），避免与 ar2List 并存
                        r["dialects"][k].pop("ar2", None)
                        r["dialects"][k].pop("rom2", None)
                break

    sec0["title"] = re.sub(r"（\d+句）", "（%d句）" % len(sec0["rows"]), sec0["title"])
    n = 0
    for s in data["sections"]:
        for i, r in enumerate(s["rows"]):
            n += 1
            s["rows"][i] = {"num": n, "cn": r["cn"], "dialects": r["dialects"]}

    data["legend"] = (
        "① 标准阿拉伯语(MSA/الفصحى) · ② 埃及阿拉伯语(مصري) · ③ 黎凡特阿拉伯语(شامي) · "
        "④ 海湾阿拉伯语(خليجي) · ⑤ 伊拉克阿拉伯语(عراقي) · ⑥ 马格里布阿拉伯语(دارجة)"
    )
    data["intro"] = [
        "**① 标准阿拉伯语（الفصحى / MSA）**：考试、新闻、正式写作专用",
        "**② 埃及阿拉伯语（مصري / Masri）**：🇪🇬 日常**最通用❗**——阿拉伯世界\"普通话\"，影视媒体全覆盖",
        "**③ 黎凡特阿拉伯语（شامي / Shami）**：🇸🇾🇱🇧🇵🇸🇯🇴 叙利亚·黎巴嫩·巴勒斯坦·约旦",
        "**④ 海湾阿拉伯语（خليجي / Khaliji）**：🇸🇦🇦🇪🇰🇼🇶🇦🇧🇭🇴🇲 沙特·阿联酋·科威特·卡塔尔·巴林·阿曼",
        "**⑤ 伊拉克阿拉伯语（عراقي / Iraqi）**：🇮🇶 伊拉克，介于海湾与黎凡特之间，شلون / أريد / هسه 为标志词",
        "**⑥ 马格里布阿拉伯语（دارجة / Darija）**：🇲🇦🇩🇿🇹🇳 摩洛哥·阿尔及利亚·突尼斯",
        "括号内为罗马化注音（拉丁字母模拟发音），帮助大家开口。",
    ]

    # data.json / js/data.js（紧凑单行输出：体积减半、解析更快）
    with open(os.path.join(BASE, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.makedirs(os.path.join(BASE, "js"), exist_ok=True)
    with open(os.path.join(BASE, "js", "data.js"), "w", encoding="utf-8") as f:
        f.write("// Auto-generated: 6 dialects (standard/egyptian/levantine/gulf/iraqi/maghreb)\n")
        f.write("const DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    # js/audio.js：全部 6 方言文本 -> audio/<sha1[:12]>.mp3
    all_texts = set()
    for s in data["sections"]:
        for r in s["rows"]:
            for d in r["dialects"].values():
                if d.get("ar"):
                    all_texts.add(d["ar"])
                if d.get("ar2"):
                    all_texts.add(d["ar2"])
                if d.get("ar2List"):
                    for item in d["ar2List"]:
                        if item.get("ar"):
                            all_texts.add(item["ar"])
    amap = {t: "audio/" + hash_name(t) for t in sorted(all_texts)}
    # 需要配音的文本 = 全 6 方言文本 - 原库已有音频的文本（含新补入的问候语）
    new_texts = sorted(all_texts - old_texts)
    with open(os.path.join(BASE, "js", "audio.js"), "w", encoding="utf-8") as f:
        f.write("// Auto-generated: arabic text -> audio path (ar-AE Fatima)\n")
        f.write("const AUDIO_MAP = ")
        json.dump(amap, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    with open(os.path.join(BASE, "new_texts.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(new_texts), f, ensure_ascii=False, indent=1)

    print("rows:", sum(len(s["rows"]) for s in data["sections"]))
    print("stats:", dict(stats))
    print("old unique ar:", len(old_texts), "| all 6-dialect unique ar:", len(all_texts))
    print("NEW texts needing TTS:", len(new_texts))
    print("sample new texts:")
    for t in sorted(new_texts)[:12]:
        print("   ", t)


if __name__ == "__main__":
    main()
