import numpy as np, wave
sr=48000; dur=36.0; n=int(sr*dur)
mus=np.zeros((2,n),dtype=np.float32)
rng=np.random.default_rng(11)
def add(sig,t0,gain=0.8):
    i=int(t0*sr)
    if i>=n: return
    L=sig[:max(0,min(len(sig),n-i))]
    mus[0,i:i+len(L)]+=L*gain*0.9
    mus[1,i:i+len(L)]+=L*gain*0.9
def lp(x,a):
    y=np.empty_like(x); acc=0.0
    for i,v in enumerate(x): acc+=a*(v-acc); y[i]=acc
    return y
def pad(freqs,t0,dur,vol=0.3):
    L=int(sr*dur); t=np.arange(L)/sr; sig=np.zeros(L)
    for f in freqs:
        for det in (-5,0,5):
            ff=f*2**(det/1200)
            ph=2*np.pi*np.cumsum(ff*(1+0.003*np.sin(2*np.pi*4*t)))/sr
            sig+=(2*((ph/np.pi)%2-1))*0.22
    sig=lp(sig,0.05)
    e=np.minimum(1,t/(dur*0.4))*np.minimum(1,(dur-t)*2.5)
    add(sig*e*vol,t0)
def harp(f,t0,vol=0.18):
    L=int(sr*1.5); t=np.arange(L)/sr
    sig=sum(np.sin(2*np.pi*f*h*t)/h for h in (1,2,3))
    add(sig*np.exp(-t*3)*vol,t0)
def swell(t0,dur,vol=0.4):
    L=int(sr*dur); t=np.arange(L)/sr; k=t/dur
    f=60+140*k**2
    ph=2*np.pi*np.cumsum(f)/sr
    add(np.sin(ph)*k**2.5*np.minimum(1,(dur-t)*4)*vol,t0)
def hit(t0,vol=0.8):
    L=int(sr*1.4); t=np.arange(L)/sr
    f=50*np.exp(-t*3)+30
    ph=2*np.pi*np.cumsum(f)/sr
    add(np.sin(ph)*np.minimum(1,t*90)*np.exp(-t*3.5)*vol,t0)

# D minor ambient: dark pad, sparse harp, swell into the moment ~24s, hit at ~26s
pad([146.8,220.0,293.7],0,20,0.26)
for k,t0 in enumerate(np.arange(4,20,2.2)):
    harp([293.7,349.2,440.0][k%3]*2,t0,0.13)
pad([146.8,174.6,220.0,293.7],18,14,0.3)
swell(21,4,0.45)
hit(25.0,0.9)
pad([146.8,220.0,293.7,349.2],26,9,0.28)
harp(587.3,30,0.14); harp(440.0,32,0.12)
hit(33.5,0.5)
mus=np.tanh(mus*1.3); mus=mus/np.abs(mus).max()*0.89
pcm=(mus.T*32767).astype(np.int16)
w=wave.open("see_music.wav","wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
w.writeframes(pcm.tobytes()); w.close()
print("see music written")
