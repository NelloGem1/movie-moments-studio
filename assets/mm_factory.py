"""Infinite Movie Moments factory: builds Christmas edits one at a time,
forever. Skips titles already uploaded (mm_uploaded.txt) or already rendered.
Sleeps between passes so it never hammers the machine."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import movie_pipeline as mp
import build_video as b
import make_edit as m
import polish as p

ASSETS = mp.ASSETS
TDL = os.path.join(ASSETS, "trailers_dl")
OUT_DIR = os.path.expanduser("~/Downloads/MOVIE_MOMENTS")
DONE_UP = os.path.join(ASSETS, "mm_uploaded.txt")
os.makedirs(OUT_DIR, exist_ok=True)

# slug, youtube search query, display movie, year
QUEUE = [
    ("home_alone2",  "Home Alone 2 Lost in New York trailer",     "Home Alone 2",            "1992"),
    ("santa_clause", "The Santa Clause trailer",                   "The Santa Clause",        "1994"),
    ("grinch2000",   "How the Grinch Stole Christmas 2000 trailer","How the Grinch Stole Christmas","2000"),
    ("muppet_xmas",  "The Muppet Christmas Carol trailer",         "The Muppet Christmas Carol","1992"),
    ("four_xmas",    "Four Christmases trailer",                   "Four Christmases",        "2008"),
    ("the_holiday",  "The Holiday 2006 trailer",                   "The Holiday",             "2006"),
    ("happiest",     "Happiest Season trailer",                    "Happiest Season",         "2020"),
    ("fatman",       "Fatman 2020 trailer",                        "Fatman",                  "2020"),
    ("krampus",      "Krampus 2015 trailer",                       "Krampus",                 "2015"),
    ("arthur_xmas",  "Arthur Christmas trailer",                   "Arthur Christmas",        "2011"),
    ("the_star",     "The Star 2017 trailer",                      "The Star",                "2017"),
    ("rare_exports", "Rare Exports trailer",                       "Rare Exports",            "2010"),
    ("black_xmas",   "Black Christmas 2019 trailer",               "Black Christmas",         "2019"),
    ("angels_out",   "Angels in the Outfield trailer",             "Angels in the Outfield",  "1994"),
    ("scrooged",     "Scrooged trailer",                           "Scrooged",                "1988"),
    ("deck_halls",   "Deck the Halls trailer",                     "Deck the Halls",          "2006"),
    ("8_crazy",      "Eight Crazy Nights trailer",                 "Eight Crazy Nights",      "2002"),
    ("fred_claus",   "Fred Claus trailer",                         "Fred Claus",              "2007"),
    ("santa2",       "The Santa Clause 2 trailer",                 "The Santa Clause 2",      "2002"),
    ("ninja_xmas",   "The Night Before trailer",                   "The Night Before",        "2015"),
    ("xmas_kranks",  "Christmas with the Kranks trailer",          "Christmas with the Kranks","2004"),
    ("bad_moms",     "A Bad Moms Christmas trailer",               "A Bad Moms Christmas",    "2017"),
    ("best_xmas",    "The Best Christmas Pageant Ever trailer",    "The Best Christmas Pageant Ever","2011"),
    ("prep_xmas",    "Prep and Landing trailer",                   "Prep and Landing",        "2009"),
    ("single_xmas",  "Single All the Way trailer",                 "Single All the Way",      "2021"),
    ("jingle_jungle", "Jingle Jungle trailer",                     "Jingle Jungle",           "2018"),
    ("nacc_xmas",     "The Night Before trailer",                  "The Night Before",        "2015"),
    ("santa_claus3",  "The Santa Clause 3 trailer",                "The Santa Clause 3",      "2006"),
    ("lotr_rho",      "The Lord of the Rings War of the Rohirrim trailer","The Lord of the Rings War of the Rohirrim","2025"),
    ("dog_man",       "Dog Man trailer",                           "Dog Man",                 "2025"),
    ("wolf_man",      "The Wolf Man 2025 trailer",                 "The Wolf Man",            "2025"),
    ("nosferatu",     "Nosferatu 2024 trailer",                    "Nosferatu",               "2024"),
    ("red_one_s2",    "Red One 2 trailer",                         "Red One 2",               "2026"),
]

# ---- wave 2: keep the factory fed ----
QUEUE += [
    # more Christmas
    ("polar_exp",     "The Polar Express trailer",                  "The Polar Express",       "2004"),
    ("iwl",           "Its a Wonderful Life trailer",               "Its a Wonderful Life",    "1946"),
    ("rise_guard",    "Rise of the Guardians trailer",              "Rise of the Guardians",   "2012"),
    ("xmas_chron2",   "The Christmas Chronicles 2 trailer",         "The Christmas Chronicles 2","2020"),
    ("man_xmas",      "The Man Who Invented Christmas trailer",     "The Man Who Invented Christmas","2017"),
    ("last_xmas",     "Last Christmas 2019 trailer",                "Last Christmas",          "2019"),
    ("family_stone",  "The Family Stone trailer",                   "The Family Stone",        "2005"),
    ("miracle_34",    "Miracle on 34th Street trailer",             "Miracle on 34th Street",  "1994"),
    ("white_xmas",    "White Christmas 1954 trailer",               "White Christmas",         "1954"),
    ("xmas_carol",    "A Christmas Carol 2009 trailer",             "A Christmas Carol",       "2009"),
    ("the_snowman",   "The Snowman 2013 trailer",                   "The Snowman",             "2013"),
    ("prancer",       "Prancer 1989 trailer",                       "Prancer",                 "1989"),
    ("the_ref",       "The Ref trailer",                            "The Ref",                 "1994"),
    ("family_man",    "The Family Man trailer",                     "The Family Man",          "2000"),
    ("while_sleep",   "While You Were Sleeping trailer",            "While You Were Sleeping", "1991"),
    ("serendipity",   "Serendipity 2001 trailer",                   "Serendipity",             "2001"),
    ("let_it_snow",   "Let It Snow 2019 trailer",                   "Let It Snow",             "2019"),
    ("xmas_prince",   "A Christmas Prince trailer",                 "A Christmas Prince",      "2017"),
    ("holi_wild",     "Holiday in the Wild trailer",                "Holiday in the Wild",     "2019"),
    ("xmas_again",    "Christmas Again trailer",                    "Christmas Again",         "2024"),
    ("best_man_hol",  "The Best Man Holiday trailer",               "The Best Man Holiday",    "2013"),
    # general / trending movies
    ("kpop_demon",    "KPop Demon Hunters trailer",                 "KPop Demon Hunters",      "2025"),
    ("avengers_doom", "Avengers Doomsday trailer",                  "Avengers Doomsday",       "2026"),
    ("supergirl",     "Supergirl 2026 trailer",                     "Supergirl",               "2026"),
    ("moana_live",    "Moana live action trailer",                  "Moana",                   "2026"),
    ("masters_u",     "Masters of the Universe trailer",            "Masters of the Universe", "2026"),
    ("gi_joe",        "G.I. Joe trailer",                           "G.I. Joe",                "2026"),
    ("minecraft2",    "A Minecraft Movie 2 trailer",                "A Minecraft Movie 2",     "2027"),
    ("dune_p3",       "Dune Part Three trailer",                    "Dune Part Three",         "2026"),
    ("frozen3",       "Frozen 3 trailer",                           "Frozen 3",                "2027"),
    ("cars4",         "Cars 4 trailer",                             "Cars 4",                  "2027"),
    ("toy_story5b",   "Toy Story 5 trailer",                        "Toy Story 5",             "2026"),
    ("sinners2",      "Sinners 2 trailer",                          "Sinners 2",               "2027"),
    ("final_dest",    "Final Destination Bloodlines trailer",       "Final Destination Bloodlines","2025"),
    ("28_years",      "28 Years Later trailer",                     "28 Years Later",          "2025"),
    ("weapon",        "Weapon 2025 trailer",                        "Weapon",                  "2025"),
    ("one_battle",    "One Battle After Another trailer",           "One Battle After Another","2025"),
    ("marty_sup",     "Superman 2025 trailer",                      "Superman",                "2025"),
    ("fantastic4",    "The Fantastic Four trailer",                 "The Fantastic Four",      "2025"),
    ("thunderbolts",  "Thunderbolts trailer",                       "Thunderbolts",            "2025"),
    ("captain_am",    "Captain America Brave New World trailer",    "Captain America Brave New World","2025"),
    ("wicked_fg",     "Wicked For Good trailer",                   "Wicked For Good",        "2025"),
]


def log(*a):
    print(time.strftime("[%H:%M:%S]"), " ".join(str(x) for x in a), flush=True)


def uploaded_titles():
    if not os.path.exists(DONE_UP):
        return set()
    out = set()
    for line in open(DONE_UP, encoding="utf-8"):
        out.add(os.path.splitext(line.strip())[0].lower())
    return out


def fetch_trailer(slug, query):
    dst = os.path.join(TDL, f"mm_{slug}.mp4")
    if os.path.exists(dst) and os.path.getsize(dst) > 1_000_000:
        return dst
    import subprocess
    r = subprocess.run(["yt-dlp", "--no-playlist", "--flat-playlist",
                        "--print", "%(id)s", f"ytsearch5:{query}"],
                       capture_output=True, text=True, timeout=120)
    ids = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    for vid in ids:
        tmp = dst + ".part.mp4"
        rr = subprocess.run(["yt-dlp", "--no-playlist",
                             "-f", "bv*[height>=1080]+ba/bv*[height>=720]+ba/b",
                             "--merge-output-format", "mp4",
                             "-o", tmp,
                             f"https://www.youtube.com/watch?v={vid}"],
                            capture_output=True, text=True, timeout=900)
        if rr.returncode == 0 and os.path.exists(tmp):
            os.replace(tmp, dst)
            log("trailer:", slug, "<-", vid)
            return dst
    raise RuntimeError(f"no trailer for {slug}")


def build_one(slug, movie, year, query):
    title = f"{movie} ({year}) — Christmas Movie Edit"
    out_final = os.path.join(ASSETS, f"mm_{slug}.mp4")
    out_dir_file = os.path.join(OUT_DIR, title + ".mp4")
    # already uploaded?
    if title.lower() in uploaded_titles():
        log("skip uploaded:", title)
        return
    # already rendered and sitting in out dir?
    if os.path.exists(out_dir_file):
        log("skip exists:", title)
        return
    src = fetch_trailer(slug, query)
    rel = os.path.relpath(src, ASSETS).replace(os.sep, "/")
    clips, tail = mp.speech_cuts(rel, max_clips=30, return_tail=True, dmax=8.5)
    est = sum(d for _, d in clips) if clips else 0
    if not clips or est < 105:
        wins = m.energy_windows(rel, count=26, win=5.0, min_gap=4.0,
                                seed=abs(hash(slug)) % 5000)
        clips = [(round(t, 2), round(d, 2)) for t, d in wins]
        tail = None
    if tail:
        T = b.probe_duration(src)
        clips = clips + [(tail, round(T - tail, 2))]
    key = f"mm_{slug}"
    seg = b.build_clean_montage(key, rel, clips, target_name=key + ".mp4")
    mp._finish_single(key, [seg])
    out = os.path.join(ASSETS, key + ".mp4")
    polished = p.polish(out)
    os.replace(polished, out)
    dur = b.probe_duration(out)
    mp.make_thumb(out, movie, f"{year} Trailer Edit",
                  os.path.join(ASSETS, key + ".jpg"))
    if dur >= 100:
        import shutil
        shutil.copy(out, out_dir_file)
    log(f"OK {movie}: {len(clips)} clips, {dur:.0f}s")


def main():
    if os.path.exists(os.path.join(ASSETS, "mm_par_running.flag")):
        log("parallel factory active — exiting")
        return
    log("=== Movie Moments factory started ===")
    while True:
        progressed = False
        for slug, query, movie, year in QUEUE:
            try:
                before = set(os.listdir(OUT_DIR))
                build_one(slug, movie, year, query)
                progressed = True
            except Exception as e:
                log("ERR", slug, repr(e)[:150])
        if not progressed:
            log("queue exhausted — sleeping 30 min, will recheck")
            time.sleep(1800)
        else:
            time.sleep(10)


if __name__ == "__main__":
    main()
