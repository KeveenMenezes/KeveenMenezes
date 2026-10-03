#!/usr/bin/env python3
"""Turns the "Duck Waddling" sticker GIF (Tenor, found via Pinterest) into the
astronaut duck used by generate.py: removes the white background and floor shadow,
then draws a glass helmet, neck ring, antenna and mission patch on every frame.

Needs Pillow; generate.py only embeds the resulting PNGs.

    curl -sL https://i.pinimg.com/originals/39/4f/50/394f50c2f154626f383e6ba7c4c8477c.gif -o waddle.gif
    python scripts/astronaut_duck.py waddle.gif
"""
import json
import math
import os
import sys
from collections import deque

from PIL import Image, ImageDraw, ImageSequence

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "duck")
SIZES = {"walk": 352, "walk_small": 96}  # output heights (about 1.5x the displayed size)


# ---------------------------------------------------------------- background
MAG=(255,0,255)
def cut(f):
    rgb=f.convert('RGB'); W,H=rgb.size
    for seed in [(0,0),(W-1,0),(0,H-1),(W-1,H-1),(W//2,0),(0,H//2),(W-1,H//2),(W//2,H-1)]:
        if rgb.getpixel(seed)!=MAG: ImageDraw.floodfill(rgb,seed,MAG,thresh=70)
    px=rgb.load()
    # shadow blobs in the lower part
    for y in range(int(H*.6),H,3):
        for x in range(0,W,3):
            r,g,b=px[x,y]
            if (r,g,b)!=MAG and 40<=r<=64 and abs(r-g)<6 and abs(g-b)<6:
                ImageDraw.floodfill(rgb,(x,y),MAG,thresh=30)
    out=Image.new('RGBA',(W,H),(0,0,0,0)); op=out.load()
    for y in range(H):
        for x in range(W):
            if px[x,y]!=MAG: op[x,y]=px[x,y]+(255,)
    # trim light/grey fringe left next to removed pixels
    for _ in range(2):
        kill=[]
        for y in range(1,H-1):
            for x in range(1,W-1):
                r,g,b,a=op[x,y]
                if a and 70<r<235 and abs(r-g)<12 and abs(g-b)<12:
                    n=sum(1 for dx in (-1,0,1) for dy in (-1,0,1) if op[x+dx,y+dy][3]==0)
                    if n>=3: kill.append((x,y))
        for x,y in kill: op[x,y]=(0,0,0,0)
    return out


# ---------------------------------------------------------------- shadow leftovers + head tracking
INK=(4,2,4)

def scrub(img):
    """Remove leftover dithered shadow: flood from the outside through light/grey pixels;
    the black outline stops it, so the white body survives."""
    W,H=img.size; p=img.load()
    floor=372  # the shadow only lives below the body
    def passable(c, y=None):
        r,g,b,a=c
        if not a: return False
        orange = r>200 and 60<g<140 and b<60
        yellow = r>170 and g>150 and b<110
        return r>=40 and not orange and not yellow and abs(r-g)<20 and abs(g-b)<20
    seen=set(); q=deque()
    for y in range(H):
        for x in range(W):
            if p[x,y][3]==0:
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny=x+dx,y+dy
                    if 0<=nx<W and floor<=ny<H and (nx,ny) not in seen and passable(p[nx,ny]):
                        seen.add((nx,ny)); q.append((nx,ny))
    while q:
        x,y=q.popleft(); p[x,y]=(0,0,0,0)
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<W and floor<=ny<H and (nx,ny) not in seen and passable(p[nx,ny]):
                seen.add((nx,ny)); q.append((nx,ny))
    # drop tiny islands
    seen=set()
    for y in range(H):
        for x in range(W):
            if p[x,y][3] and (x,y) not in seen:
                comp=[(x,y)]; seen.add((x,y)); i=0
                while i<len(comp):
                    cx,cy=comp[i]; i+=1
                    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
                        nx,ny=cx+dx,cy+dy
                        if 0<=nx<W and 0<=ny<H and (nx,ny) not in seen and p[nx,ny][3]:
                            seen.add((nx,ny)); comp.append((nx,ny))
                if len(comp)<400:
                    for cx,cy in comp: p[cx,cy]=(0,0,0,0)
    return img

def head_info(img):
    W,H=img.size; p=img.load()
    ys=[y for y in range(H) for x in range(0,W,2) if p[x,y][3]]
    top=min(ys)
    xs=[x for y in range(top,top+80) for x in range(W) if p[x,y][3]]
    hcx=sum(xs)/len(xs)
    beak=[(x,y) for y in range(top,top+160) for x in range(W) if p[x,y][3] and p[x,y][0]>170 and p[x,y][1]>150 and p[x,y][2]<110]
    bx=sum(x for x,_ in beak)/len(beak); by=sum(y for _,y in beak)/len(beak)
    return top,hcx,(bx,by),beak


# ---------------------------------------------------------------- astronaut gear
INK_A=(4,2,4,255)
SS=4
R=90
PAD=64

def overlay(src, i):
    img=Image.new('RGBA',(src.width,src.height+PAD),(0,0,0,0)); img.paste(src,(0,PAD))
    W,H=img.size
    top,hcx,(bx,by),_=head_info(img)
    cx=hcx*0.74+bx*0.26; cy=top+72
    big=(W*SS,H*SS)
    S=lambda v: v*SS
    def circ(d,c,r,**kw): d.ellipse([S(c[0]-r),S(c[1]-r),S(c[0]+r),S(c[1]+r)],**kw)
    def oval(d,c,rx,ry,**kw): d.ellipse([S(c[0]-rx),S(c[1]-ry),S(c[0]+rx),S(c[1]+ry)],**kw)

    front=Image.new('RGBA',big,(0,0,0,0)); df=ImageDraw.Draw(front)

    # mission patch on the chest, on the side the duck is facing
    face=(bx-hcx)
    pc=(bx+face*0.6+2, top+222)
    circ(df,pc,17,fill=INK_A); circ(df,pc,12.5,fill=(115,85,221,255))
    star=[(pc[0]+(8.5 if k%2==0 else 3.6)*math.cos(math.radians(-90+36*k)),
           pc[1]+(8.5 if k%2==0 else 3.6)*math.sin(math.radians(-90+36*k))) for k in range(10)]
    df.polygon([(S(x),S(y)) for x,y in star],fill=(255,255,255,255))
    circ(df,(pc[0]+7,pc[1]-8),2.2,fill=(255,138,31,255))

    # glass bubble (soft tint over the head)
    glass=Image.new('RGBA',big,(0,0,0,0)); dg=ImageDraw.Draw(glass)
    circ(dg,(cx,cy),R,fill=(170,212,255,64))
    front.alpha_composite(glass); df=ImageDraw.Draw(front)

    # neck ring
    rc=(cx-2,cy+R-10); rx,ry=R*0.8,17
    oval(df,rc,rx,ry,fill=INK_A)
    oval(df,rc,rx-6,ry-6,fill=(190,197,214,255))
    oval(df,(rc[0],rc[1]-3),rx-10,ry-10,fill=(226,231,243,255))
    df.rounded_rectangle([S(rc[0]-rx*0.55),S(rc[1]-6),S(rc[0]-rx*0.1),S(rc[1]-3)],radius=S(2),fill=(255,255,255,255))
    for k in (-1,1):
        circ(df,(rc[0]+k*rx*0.62,rc[1]+2),3,fill=(122,130,154,255))

    # rim, highlights
    circ(df,(cx,cy),R,outline=INK_A,width=S(8))
    circ(df,(cx,cy),R-6,outline=(228,240,255,255),width=S(3))
    df.arc([S(cx-R+17),S(cy-R+17),S(cx+R-17),S(cy+R-17)],start=196,end=250,fill=(255,255,255,235),width=S(11))
    a=math.radians(262); circ(df,(cx+(R-23)*math.cos(a),cy+(R-23)*math.sin(a)),5,fill=(255,255,255,235))
    df.arc([S(cx-R+14),S(cy-R+14),S(cx+R-14),S(cy+R-14)],start=20,end=48,fill=(255,255,255,150),width=S(5))

    # antenna with a blinking light
    a=math.radians(-112); base=(cx+R*math.cos(a),cy+R*math.sin(a)); tip=(base[0]-10,base[1]-30)
    df.line([S(base[0]),S(base[1]),S(tip[0]),S(tip[1])],fill=INK,width=S(7))
    on=(i//3)%2==0
    circ(df,tip,11,fill=INK_A); circ(df,tip,7,fill=(120,240,140,255) if on else (46,170,74,255))
    if on: circ(df,(tip[0]-2.6,tip[1]-2.6),2.4,fill=(255,255,255,255))

    front=front.resize((W,H),Image.LANCZOS)
    out=img.copy(); out.alpha_composite(front)
    return out


def main(src):
    frames, durations = [], []
    for i, f in enumerate(ImageSequence.Iterator(Image.open(src))):
        durations.append(f.info.get("duration", 50))
        frames.append(overlay(scrub(cut(f)), i))
    box = None
    for f in frames:
        b = f.getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    box = (box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 2)
    w, h = box[2] - box[0], box[3] - box[1]
    for name, height in SIZES.items():
        out = os.path.join(ROOT, name)
        os.makedirs(out, exist_ok=True)
        size = (round(w * height / h), height)
        for i, f in enumerate(frames):
            img = f.crop(box).resize(size, Image.LANCZOS)
            img = img.quantize(colors=128, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
            img.save(os.path.join(out, f"{i:02d}.png"), optimize=True)
    with open(os.path.join(ROOT, "meta.json"), "w") as f:
        json.dump({"frames": len(frames), "frame_ms": round(sum(durations) / len(durations)), "aspect": round(w / h, 4)}, f, indent=2)
    print("wrote", len(frames), "frames to", ROOT)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "waddle.gif")
