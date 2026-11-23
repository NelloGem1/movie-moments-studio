"""Build 3 style samples for the Walter White life-story video."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.dirname(os.path.abspath(__file__))
FFMPEG = r"C:\Users\neilh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.1-full_build\bin\ffmpeg.exe"
VOICE = os.path.join(ASSETS, "voice_bb.mp3")
TRAILER = os.path.join(ASSETS, "bb_trailer.mp4")
W, H = 1920, 1080

def run(args):
    subprocess.run([FFMPEG, "-y"] + args, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def font(sz):
    for p in [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

# ---------- SAMPLE A: trailer montage ----------
def sample_a():
    clips = [(2,7),(25,30),(50,55),(75,80),(100,105),(118,123)]
    parts = []
    for i,(s,e) in enumerate(clips):
        out = os.path.join(ASSETS, f"sa{i}.mp4")
        if os.path.exists(out): parts.append(out); continue
        run(["-ss",str(s),"-to",str(e),"-i",TRAILER,
             "-vf","scale=1920:1080,fps=30,fade=t=in:st=0:d=0.4,fade=t=out:st=4.4:d=0.4",
             "-c:v","libx264","-preset","veryfast","-crf","20","-an",out])
        parts.append(out)
    lst = os.path.join(ASSETS,"sa_list.txt")
    with open(lst,"w") as f:
        for p in parts: f.write(f"file '{p.replace(os.sep,'/')}'\n")
    base = os.path.join(ASSETS,"sa_base.mp4")
    run(["-f","concat","-safe","0","-i",lst,"-c","copy",base])
    final = os.path.join(ASSETS,"sample_A_trailer.mp4")
    run(["-i",base,"-i",VOICE,"-map","0:v","-map","1:a",
         "-c:v","copy","-c:a","aac","-b:a","192k","-shortest",
         "-movflags","+faststart",final])
    print("A done")

# ---------- SAMPLE B: text cards ----------
def sample_b():
    cards = [
        ("WALTER WHITE", "THE MAN BEHIND HEISENBERG"),
        ("A MILD-MANNERED", "CHEMISTRY TEACHER"),
        ("TERMINAL DIAGNOSIS", "AND A FAMILY IN DEBT"),
        ("THE EMPEROR", "OF METH"),
    ]
    imgs = []
    for i,(big,small) in enumerate(cards):
        im = Image.new("RGB",(W,H),(8,8,12))
        d = ImageDraw.Draw(im)
        f1 = font(110); f2 = font(48)
        # wrap big text
        words = big.split(); lines=[]; cur=""
        for wd in words:
            t = (cur+" "+wd).strip()
            if d.textlength(t,font=f1) > W-200: lines.append(cur); cur=wd
            else: cur=t
        lines.append(cur)
        y = H//2 - len(lines)*70
        for ln in lines:
            tw = d.textlength(ln,font=f1)
            d.text(((W-tw)//2, y), ln, font=f1, fill=(230,230,235)); y += 130
        tw2 = d.textlength(small,font=f2)
        d.text(((W-tw2)//2, y+20), small, font=f2, fill=(180,60,60))
        p = os.path.join(ASSETS,f"sb{i}.png"); im.save(p); imgs.append(p)
    # each card ~7.4s with fade
    parts=[]
    for i,p in enumerate(imgs):
        out=os.path.join(ASSETS,f"sb{i}.mp4")
        if os.path.exists(out): parts.append(out); continue
        run(["-loop","1","-t","7.6","-i",p,
             "-vf","fade=t=in:st=0:d=0.5,fade=t=out:st=7.0:d=0.5,format=yuv420p",
             "-c:v","libx264","-preset","veryfast","-crf","20","-an",out])
        parts.append(out)
    lst=os.path.join(ASSETS,"sb_list.txt")
    with open(lst,"w") as f:
        for p in parts: f.write(f"file '{p.replace(os.sep,'/')}'\n")
    base=os.path.join(ASSETS,"sb_base.mp4")
    run(["-f","concat","-safe","0","-i",lst,"-c","copy",base])
    final=os.path.join(ASSETS,"sample_B_textcards.mp4")
    run(["-i",base,"-i",VOICE,"-map","0:v","-map","1:a",
         "-c:v","copy","-c:a","aac","-b:a","192k","-shortest",
         "-movflags","+faststart",final])
    print("B done")

# ---------- SAMPLE C: ken burns stills ----------
def sample_c():
    times=[5,30,60,90,115]
    parts=[]
    for i,t in enumerate(times):
        still=os.path.join(ASSETS,f"sc{i}.jpg")
        run(["-ss",str(t),"-i",TRAILER,"-frames:v","1","-q:v","2",still])
        out=os.path.join(ASSETS,f"sc{i}.mp4")
        if os.path.exists(out): parts.append(out); continue
        # slow zoom in 1.0->1.15 over 6s
        run(["-loop","1","-t","6","-i",still,
             "-vf","scale=2400:1350,zoompan=z='min(zoom+0.0008,1.15)':d=180:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,fade=t=in:st=0:d=0.5,fade=t=out:st=5.3:d=0.5,format=yuv420p",
             "-c:v","libx264","-preset","veryfast","-crf","20","-an",out])
        parts.append(out)
    lst=os.path.join(ASSETS,"sc_list.txt")
    with open(lst,"w") as f:
        for p in parts: f.write(f"file '{p.replace(os.sep,'/')}'\n")
    base=os.path.join(ASSETS,"sc_base.mp4")
    run(["-f","concat","-safe","0","-i",lst,"-c","copy",base])
    final=os.path.join(ASSETS,"sample_C_kenburns.mp4")
    run(["-i",base,"-i",VOICE,"-map","0:v","-map","1:a",
         "-c:v","copy","-c:a","aac","-b:a","192k","-shortest",
         "-movflags","+faststart",final])
    print("C done")

if __name__=="__main__":
    sample_a(); sample_b(); sample_c()
    print("ALL DONE")
