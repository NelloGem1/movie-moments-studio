"""Batch-build all movie videos in the no-narration trailer-edit style."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_edit as m

JOBS = [
    # --- 2008 retrospective ---
    ("movies_2008", [
        ("y08_im", "y2008/im.mp4"), ("y08_tdk", "y2008/tdk.mp4"),
        ("y08_walle", "y2008/walle.mp4"), ("y08_kungfu", "y2008/kungfu.mp4"),
        ("y08_indiana", "y2008/indiana.mp4"), ("y08_hulk", "y2008/hulk.mp4"),
    ], dict(per_movie=3, win=4.5, seed=11)),

    # --- Avengers: Doomsday (5 videos, 6 teasers) ---
    ("avengers_reveals", [
        ("av_official", "official_teaser.mp4"),
        ("av_return", "return_trailer.mp4"),
    ], dict(per_movie=10, win=4.5, seed=21)),
    ("avengers_steve", [
        ("av_steve", "steve_teaser.mp4"),
    ], dict(per_movie=14, win=4.0, seed=22)),
    ("avengers_thor", [
        ("av_thor", "thor_teaser.mp4"),
    ], dict(per_movie=14, win=4.0, seed=23)),
    ("avengers_xmen", [
        ("av_xmen", "xmen_teaser.mp4"),
        ("av_wakanda", "wakanda_teaser.mp4"),
    ], dict(per_movie=12, win=4.0, seed=24)),
    ("avengers_castmix", [
        ("av_m1", "steve_teaser.mp4"), ("av_m2", "thor_teaser.mp4"),
        ("av_m3", "xmen_teaser.mp4"), ("av_m4", "wakanda_teaser.mp4"),
    ], dict(per_movie=5, win=4.0, seed=25)),

    # --- Dune (5 videos, 4 trailers) ---
    ("dune_final", [
        ("dun_t2", "dune_trailer2.mp4"),
        ("dun_p3", "dune_p3_teaser.mp4"),
    ], dict(per_movie=12, win=4.5, seed=31)),
    ("dune_guide", [
        ("dun_p3", "dune_p3_teaser.mp4"),
    ], dict(per_movie=14, win=4.0, seed=32)),
    ("dune_cast", [
        ("dun_t2", "dune_trailer2.mp4"),
    ], dict(per_movie=16, win=4.0, seed=33)),
    ("dune_theories", [
        ("dun_teaser", "dune_teaser.mp4"),
        ("dun_p3", "dune_p3_teaser.mp4"),
    ], dict(per_movie=9, win=4.5, seed=34)),
    ("dune_recap", [
        ("dun_teaser", "dune_teaser.mp4"),
        ("dun_lynch", "dune_1984.mp4"),
    ], dict(per_movie=9, win=4.5, seed=35)),
]

if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    for name, movies, kw in JOBS:
        if only and name not in only:
            continue
        out = os.path.join(m.ASSETS, name + ".mp4")
        if os.path.exists(out):
            print("SKIP (exists):", name); continue
        t0 = time.time()
        try:
            m.make_edit(name, movies, **kw)
        except Exception as e:
            print(f"FAILED {name}: {e}")
        print(f"=== {name} done in {time.time()-t0:.0f}s ===\n", flush=True)
