"""Cinematic polish pass: teal-orange grade, vignette, grain, sharpen."""
import os, subprocess, sys
import build_video as b

FF = b.FFMPEG

POLISH = (
    "eq=contrast=1.08:saturation=1.18:brightness=-0.01,"
    "colorbalance=rs=-0.04:gs=-0.02:bs=0.06:rm=0.05:gm=0.01:bm=-0.05,"
    "curves=master='0/0.02 0.5/0.52 1/0.97',"
    "vignette=PI/5:mode=forward,"
    "noise=alls=4:allf=t+u,"
    "unsharp=5:5:0.4:5:5:0.0"
)


def polish(src, dst=None):
    dst = dst or src.replace(".mp4", "_polished.mp4")
    fc = f"[0:v]{POLISH}[v]"
    subprocess.run([FF, "-y", "-i", src, "-filter_complex", fc,
                    "-map", "[v]", "-map", "0:a", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "18",
                    "-c:a", "copy", "-movflags", "+faststart", dst],
                   check=True, capture_output=True)
    return dst


if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(polish(f))
