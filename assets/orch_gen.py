import numpy as np, wave
sr=48000; dur=57.0; n=int(sr*dur)
mus=np.zeros((2,n),dtype=np.float32)
rng=np.random.default_rng(7)

def add(sig,t0,pan=0.0,gain=0.8):
    i=int(t0*sr)
    if i>=n: return
    L=sig[:max(0,min(len(sig),n-i))]
    gl=np.sqrt(0.5*(1-pan)); gr=np.sqrt(0.5*(1+pan))
    mus[0,i:i+len(L)]+=L*gl*gain
    mus[1,i:i+len(L)]+=L*gr*gain

def lp(x,a):
    y=np.empty_like(x); acc=0.0
    for i,v in enumerate(x): acc+=a*(v-acc); y[i]=acc
    return y

def strings(freqs,t0,dur,vol=0.3,vib=5.0):
    L=int(sr*dur); t=np.arange(L)/sr
    sig=np.zeros(L)
    for f in freqs:
        for det in (-6,-2,2,6):
            ff=f*2**(det/1200)
            vibf=1+0.004*np.sin(2*np.pi*vib*t)
            ph=2*np.pi*np.cumsum(ff*vibf)/sr
            sig+=(2*((ph/np.pi)%2-1))*0.25
    sig=lp(sig,0.06)
    e=np.minimum(1,t/(dur*0.3))*np.minimum(1,(dur-t)*3)
    add(sig*e*vol,t0)

def note(freq,t0,dur,vol=0.3,bright=0.15):
    L=int(sr*dur); t=np.arange(L)/sr
    ph=2*np.pi*np.cumsum(freq*(1+0.003*np.sin(2*np.pi*5.5*t)))/sr
    sig=(2*((ph/np.pi)%2-1))*0.5+np.sin(ph)*0.5
    sig=lp(sig,bright)
    e=np.minimum(1,t/0.04)*np.exp(-t*1.2)*np.minimum(1,(dur-t)*8)
    add(sig*e*vol,t0)

def brass(freqs,t0,dur=1.2,vol=0.35):
    L=int(sr*dur); t=np.arange(L)/sr
    sig=np.zeros(L)
    for f in freqs:
        for det in (-8,0,8):
            ff=f*2**(det/1200)
            ph=2*np.pi*np.cumsum(ff)/sr
            sig+=(2*((ph/np.pi)%2-1))*0.3
    sig=lp(sig,0.12)
    e=np.minimum(1,t/0.02)*np.exp(-t*2.2)
    add(sig*e*vol,t0)

def harp(freq,t0,vol=0.22):
    L=int(sr*1.4); t=np.arange(L)/sr
    sig=sum(np.sin(2*np.pi*freq*h*t)/h for h in (1,2,3,4))
    add(sig*np.exp(-t*3.5)*vol,t0)

def celesta(freq,t0,vol=0.15):
    L=int(sr*0.9); t=np.arange(L)/sr
    sig=np.sin(2*np.pi*freq*t)+0.4*np.sin(2*np.pi*freq*3*t)+0.15*np.sin(2*np.pi*freq*5*t)
    add(sig*np.exp(-t*6)*vol,t0)

def timpani(t0,f=70,vol=0.7):
    L=int(sr*0.9); t=np.arange(L)/sr
    fr=f*np.exp(-t*4)+35
    ph=2*np.pi*np.cumsum(fr)/sr
    add(np.sin(ph)*np.exp(-t*5)*vol,t0)

def timpani_roll(t0,dur,vol=0.4):
    hits=int(dur/0.09)
    for k in range(hits):
        timpani(t0+k*0.09*(1-k/hits*0.5),70+30*k/hits,vol*(0.4+0.6*k/hits))

def taiko(t0,f0=75,f1=42,dec=0.5,vol=0.9):
    L=int(sr*dec); t=np.arange(L)/sr
    f=f1+(f0-f1)*np.exp(-t*18)
    ph=2*np.pi*np.cumsum(f)/sr
    env=np.exp(-t*9)
    hit=np.sin(ph)*env
    click=lp(rng.standard_normal(L),0.05)*np.exp(-t*200)*0.25
    add(hit+click,t0,vol*0.9)

def boom(t0,vol=0.9):
    L=int(sr*1.2); t=np.arange(L)/sr
    f=48*np.exp(-t*3)+28
    ph=2*np.pi*np.cumsum(f)/sr
    env=np.minimum(1,t*80)*np.exp(-t*4)
    add(np.sin(ph)*env*vol,t0)

D3,F3,A3,C4=146.8,174.6,220.0,261.6
D4,F4,A4=293.7,349.2,440.0

strings([D3*0.5,F3*0.5,A3*0.5],0,5.2,0.28)
strings([D3,F3,A3],4.8,5.0,0.22)

arp_notes=[A3,D4,F4,A4,F4,D4,A3,D4]
for k,t0 in enumerate(np.arange(5.5,26.5,1.1)):
    harp(arp_notes[k%8]*2,t0,0.16)
    if k%3==0: celesta(arp_notes[(k*2)%8]*4,t0+0.3,0.10)
strings([D3*0.5,A3*0.5,D4*0.5],5,24,0.16)

for k in range(60):
    t0=27+k*0.1
    n_=[D4,F4,A4][k%3]
    note(n_,t0,0.12,0.12,0.1)
timpani_roll(30.0,3.0,0.45)
brass([D4,F4,A4],32.7,1.4,0.3)
boom(33.0,1.0); taiko(33.0,vol=1.0); timpani(33.0,60,0.8)

oseq=[D3,D3,F3,D3,A3*0.5,D3,D3,C4]
for k in range(24):
    t0=33+k*0.5
    note(oseq[k%8],t0,0.4,0.22,0.08)
for bt in [39,45]:
    brass([D4,F4,A4],bt-0.05,1.2,0.32); timpani(bt,65,0.7); taiko(bt,vol=0.8)
for k in range(24):
    L=int(sr*0.06); t=np.arange(L)/sr
    add(lp(rng.standard_normal(L),0.3)*np.exp(-t*80)*0.10,33.25+k*0.5)

strings([D3,F3,A3,D4],45.2,5.5,0.3)
brass([D4,F4,A4],45.0,1.6,0.4); brass([D4,F4,A4],47.0,1.4,0.35); brass([D4,F4,A4],49.0,1.6,0.4)
for k in range(12):
    taiko(45+k*0.5,f0=100,f1=45,dec=0.35,vol=0.6)
timpani_roll(43.5,1.5,0.5)
boom(51.0,0.8); timpani(51.0,62,0.8)

strings([D3*0.5,F3*0.5,A3*0.5,D4*0.5],51.5,5.0,0.3)
harp(D4*2,52.5,0.2); harp(A4*2,53.5,0.18); celesta(A4*4,54.2,0.15)
boom(55.5,1.0); taiko(55.5,f0=85,f1=38,dec=1.0,vol=1.0); timpani(55.5,55,0.9)

mus=np.tanh(mus*1.3)
peak=np.abs(mus).max(); mus=mus/peak*0.89
pcm=(mus.T*32767).astype(np.int16)
w=wave.open("orchestra.wav","wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
w.writeframes(pcm.tobytes()); w.close()
print("orchestra cue written")
