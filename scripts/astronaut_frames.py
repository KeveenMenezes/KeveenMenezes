"""One-off tool: turns the old walking-duck GIF into the pixelated astronaut frames
in assets/astro (used by generate.py). Needs Pillow.

    python scripts/astronaut_frames.py path/to/duck.gif
"""
from PIL import Image, ImageSequence, ImageDraw, ImageChops
import math

def is_hair(p): r,g,b,a=p; return a and r>190 and g>200 and 40<b<130
def is_beak(p): r,g,b,a=p; return a and r>200 and 160<g<215 and b<40
def is_gray(p): r,g,b,a=p; return a and abs(r-g)<12 and abs(g-b)<14 and 45<r<100

def bbox(f, test, step=2):
    px=f.load(); W,H=f.size; xs=[];ys=[]
    for y in range(0,H,step):
        for x in range(0,W,step):
            if test(px[x,y]): xs.append(x); ys.append(y)
    return (min(xs),min(ys),max(xs),max(ys)) if xs else None

def find_swirl(f, top):
    px=f.load(); W,H=f.size; best=None
    for cy in range(int(top)+90,int(H*.78),6):
        for cx in range(40,W-40,6):
            dark=white=0
            for y in range(cy-24,cy+25,4):
                for x in range(cx-24,cx+25,4):
                    r,g,b,a=px[x,y]
                    if a and r<60: dark+=1
                    elif a and r>220 and g>220: white+=1
            ring_ok=True
            for k in range(8):
                rx=int(cx+44*math.cos(k*math.pi/4)); ry=int(cy+44*math.sin(k*math.pi/4))
                if not (0<=rx<W and 0<=ry<H): ring_ok=False; break
                r,g,b,a=px[rx,ry]
                if not (a and r>200 and g>200 and b>200): ring_ok=False; break
            if ring_ok and white>40 and dark>10:
                score=dark
                if not best or score>best[0]: best=(score,cx,cy)
    return best[1:] if best else None

def astronaut(f):
    f=f.convert('RGBA'); W,H=f.size; px=f.load()
    hb=bbox(f,is_hair); bb=bbox(f,is_beak)
    # drop the floor shadow: we're in space
    for y in range(int(H*.72),H):
        for x in range(W):
            if is_gray(px[x,y]): px[x,y]=(0,0,0,0)
    hcx=(hb[0]+hb[2])/2
    bcx=(bb[0]+bb[2])/2; bcy=(bb[1]+bb[3])/2
    cut=hb[3]+14
    cx=hcx*.75+bcx*.25; cy=cut+6; r=86
    # erase hair, headband and its tails above the cut line
    for y in range(0,int(cut)):
        for x in range(max(0,hb[0]-80),min(W,hb[2]+40)):
            px[x,y]=(0,0,0,0)
    sw=find_swirl(f, cut)
    if sw:
        d0=ImageDraw.Draw(f); sx,sy=sw
        d0.ellipse([sx-30,sy-30,sx+30,sy+30],fill=(20,18,30,255))
        d0.ellipse([sx-24,sy-24,sx+24,sy+24],fill=(115,85,221,255))
        d0.polygon([(sx,sy-15),(sx+5,sy-4),(sx+15,sy-3),(sx+7,sy+5),(sx+9,sy+15),(sx,sy+9),(sx-9,sy+15),(sx-7,sy+5),(sx-15,sy-3),(sx-5,sy-4)],fill=(255,255,255,255))
    base=f.copy()
    out=Image.new('RGBA',(W,H),(0,0,0,0)); out.alpha_composite(f)
    d=ImageDraw.Draw(out)
    # helmet shell
    d.ellipse([cx-r-6,cy-r-6,cx+r+6,cy+r+6],fill=(20,18,30,255))
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=(240,243,250,255))
    d.ellipse([cx-r+10,cy-r+48,cx+r-8,cy+r+4],fill=(200,206,222,255))  # shade
    d.ellipse([cx-r,cy-r,cx+r,cy+r-14],fill=(240,243,250,255))
    # visor toward the beak, showing the face through tinted glass
    vx=cx+(bcx-cx)*.35; vy=cy+10; vr=r*.70
    mask=Image.new('L',(W,H),0); ImageDraw.Draw(mask).ellipse([vx-vr,vy-vr*.85,vx+vr,vy+vr*.85],fill=255)
    glass=Image.new('RGBA',(W,H),(30,40,100,255))
    face=base.copy()
    tint=Image.new('RGBA',(W,H),(110,140,255,45))
    glass.alpha_composite(face); glass.alpha_composite(tint)
    rim=Image.new('L',(W,H),0); ImageDraw.Draw(rim).ellipse([vx-vr-6,vy-vr*.85-6,vx+vr+6,vy+vr*.85+6],fill=255)
    out.paste((20,18,30,255),mask=rim)
    out.paste(glass,mask=mask)
    # highlight
    d=ImageDraw.Draw(out)
    d.arc([vx-vr+14,vy-vr*.85+12,vx+vr-14,vy+vr*.85-12],200,250,fill=(235,242,255,255),width=9)
    # neck ring
    d.rounded_rectangle([cx-r*.62,cy+r-8,cx+r*.62,cy+r+12],radius=8,fill=(139,147,167,255),outline=(20,18,30,255),width=5)
    # antenna
    ax=cx-r*.45; ay=cy-r*.85
    d.line([ax,ay,ax-14,ay-34],fill=(175,178,190,255),width=16); d.ellipse([ax-24,ay-46,ax-6,ay-28],fill=(255,138,31,255),outline=(20,18,30,255),width=4)
    return out

def pixelate(img, palette, cell=6):
    W,H=img.size; small=img.resize((W//cell,H//cell),Image.BOX)
    a=small.getchannel('A').point(lambda v:255 if v>110 else 0)
    rgb=small.convert('RGB').quantize(palette=palette,dither=Image.Dither.NONE).convert('RGB')
    small=rgb.convert('RGBA'); small.putalpha(a)
    out=Image.new('RGBA',(small.width+2,small.height+2),(0,0,0,0)); out.paste(small,(1,1))
    p=out.load(); w,h=out.size
    solid={(x,y) for y in range(h) for x in range(w) if p[x,y][3]}
    for x,y in [(x+dx,y+dy) for x,y in solid for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))]:
        if 0<=x<w and 0<=y<h and (x,y) not in solid: p[x,y]=(20,18,30,255)
    return out

def build(path='duck.gif'):
    im=Image.open(path)
    big=[astronaut(f) for f in ImageSequence.Iterator(im)]
    smalls=[b.resize((80,80),Image.BOX) for b in big]
    strip=Image.new('RGB',(80*len(smalls),80))
    for i,sm in enumerate(smalls):
        bg=Image.new('RGB',(80,80),(255,255,255)); bg.paste(sm,mask=sm.getchannel('A').point(lambda v:255 if v>110 else 0)); strip.paste(bg,(80*i,0))
    colors=[(20,18,30),(255,255,255),(240,243,250),(205,210,225),(139,147,167),(90,90,95),(150,150,155),
            (254,102,0),(255,150,40),(232,198,0),(115,85,221),(30,40,100),(60,80,160),(110,140,230),(235,242,255),
            (80,170,230),(175,178,190)]
    pal=Image.new('P',(1,1)); flat=[c for rgb in colors for c in rgb]; pal.putpalette(flat+flat[:3]*(256-len(colors)))
    return [pixelate(b,pal) for b in big]

if __name__=='__main__':
    import os, sys
    frames=build(sys.argv[1])
    out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','assets','astro')
    os.makedirs(out, exist_ok=True)
    for i,fr in enumerate(frames): fr.save(os.path.join(out,f'{i:02d}.png'), optimize=True)
