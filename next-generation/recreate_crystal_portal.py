#!/usr/bin/env python3
"""Original 1536px Charoite crystal-portal art for Next startup.

Not an upscaled launcher JPEG. This deterministic original scene uses multiple
independent layers: deep-indigo nebula, luminous faceted crystalline gateway,
distant moonlit world and glossy violet water. Standard Pillow only; the stable
Portal icon is never read or changed. No external assets or network required.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
import random
import sys

SIZE = 1536
SEED = 0xC4A12026
S = SIZE / 1024.0
TAU = math.tau

def point(x, y):
    return (round(x*S), round(y*S))

def render(destination):
    dest = Path(destination)
    if dest.exists() or dest.suffix.lower() != ".png":
        raise ValueError("Require an unused PNG destination")
    rng = random.Random(SEED)
    # A detailed original cosmic color field, deliberately not JPEG upsampling.
    sky = Image.new("RGB", (SIZE, SIZE))
    pix = sky.load()
    for yy in range(SIZE):
        y = yy / S
        for xx in range(SIZE):
            x = xx / S
            dx = (x-512)/415.0
            dy = (y-446)/415.0
            radial = math.sqrt(dx*dx + dy*dy)
            nebula = math.exp(-((radial-.63)/.67)**2) * (0.52 + 0.48 *
                math.sin(x*.023 + math.sin(y*.009)*1.6)**2)
            core = math.exp(-((dx/.47)**2 + ((dy+.04)/.52)**2))
            high = math.exp(-((x-490)/310)**2 - ((y-130)/240)**2)
            red = 8 + 21*nebula + 17*core + 17*high
            green = 4 + 6*nebula + 16*core + 4*high
            blue = 31 + 57*nebula + 73*core + 23*high
            pix[xx, yy] = (min(255,round(red)),min(255,round(green)),min(255,round(blue)))
    canvas = sky.convert("RGBA")
    # Clouds with natural irregularity and diffuse bloom.
    mist = Image.new("RGBA", canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(mist)
    for _ in range(125):
        angle = rng.uniform(0,TAU)
        rr = rng.uniform(50,480)
        cx = 512+rr*math.cos(angle)
        cy = 425+rr*.8*math.sin(angle)
        w,h = rng.uniform(22,150),rng.uniform(16,92)
        fill = rng.choice([(151,55,248,36),(57,57,251,42),
                           (198,80,231,31),(56,136,244,28)])
        draw.ellipse((*point(cx-w,cy-h),*point(cx+w,cy+h)),fill=fill)
    mist=mist.filter(ImageFilter.GaussianBlur(26*S))
    canvas=Image.alpha_composite(canvas,mist)
    draw=ImageDraw.Draw(canvas,"RGBA")
    # A galaxy of sharp pinprick stars and a few diffraction glints.
    for _ in range(760):
        x,y=rng.uniform(7,1017),rng.uniform(8,745)
        r=rng.choices([.42,.65,1.05,1.7,2.5],[42,35,17,5,1])[0]
        intensity=rng.randint(90,245)
        draw.ellipse((*point(x-r,y-r),*point(x+r,y+r)),
                     fill=(208,185,255,intensity))
    for _ in range(42):
        x,y=rng.uniform(24,1000),rng.uniform(25,620)
        arm=rng.uniform(3,14)
        draw.line([point(x-arm,y),point(x+arm,y)],
                  fill=(174,132,255,110),width=max(1,round(.9*S)))
        draw.line([point(x,y-arm*.9),point(x,y+arm*.9)],
                  fill=(233,211,255,155),width=max(1,round(.8*S)))
        draw.ellipse((*point(x-1.2,y-1.2),*point(x+1.2,y+1.2)),
                     fill=(249,237,255,230))
    # A cool blue distant moonworld visible through the portal.
    inner=Image.new("RGBA",canvas.size,(0,0,0,0))
    idraw=ImageDraw.Draw(inner)
    idraw.ellipse((*point(315,240),*point(709,640)),fill=(37,49,161,168))
    for j in range(75):
        angle=rng.uniform(0,TAU)
        radius=rng.uniform(0,173)
        x=512+radius*math.cos(angle)
        y=442+radius*math.sin(angle)
        idraw.ellipse((*point(x-27,y-7),*point(x+29,y+15)),
                      fill=(84,102,236,rng.randrange(8,38)))
    inner=inner.filter(ImageFilter.GaussianBlur(20*S))
    canvas=Image.alpha_composite(canvas,inner)
    draw=ImageDraw.Draw(canvas,"RGBA")
    # Dark mountainous silhouette seen through the shining gateway.
    peaks=[]
    for k in range(36):
        x=245+k*15
        y=610-rng.uniform(2,104) if k%2 else 634-rng.uniform(0,48)
        peaks.append(point(x,y))
    draw.polygon([point(200,703)]+peaks+[point(829,703)],
                 fill=(11,12,52,242))
    # Metallic violet-banded circular gateway, as an original crystal spiral.
    # Separate blurred glow and crisp high-frequency facets, not a flat ring.
    glow=Image.new("RGBA",canvas.size,(0,0,0,0))
    gdraw=ImageDraw.Draw(glow)
    sharp=Image.new("RGBA",canvas.size,(0,0,0,0))
    pdraw=ImageDraw.Draw(sharp)
    def swirl(theta, band, phase):
        mod=1+.041*math.sin(7*theta+phase)+.023*math.cos(13*theta-1.1*phase)
        radius=(307+band)*mod
        return point(515+radius*math.cos(theta)+12*math.cos(theta*3+phase),
                     420+radius*.91*math.sin(theta)+7*math.sin(theta*5-phase))
    for band in [-34,-20,-10,0,13,24,36]:
        for j in range(95):
            start=-2.22+j*.069+rng.uniform(-.014,.014)
            end=min(4.13,start+rng.uniform(.12,.43))
            if end<=start:continue
            pts=[swirl(start+(end-start)*i/16,band,j*.027) for i in range(17)]
            color=rng.choice([(230,124,255,240),(171,67,255,248),
                              (115,66,251,238),(249,190,255,238),
                              (84,125,249,230)])
            pdraw.line(pts,fill=color,width=round(rng.uniform(1.1,3.8)*S),joint="curve")
            gdraw.line(pts,fill=(141,38,255,150),width=round(rng.uniform(10,21)*S))
    # Slow sweeping claw of crystal facets at the top of the ring.
    for k in range(27):
        theta=-2.75+k*.12
        x,y=swirl(theta,0,.13)
        xx,yy=x/S,y/S
        angle=theta+math.pi/2
        radius=rng.uniform(10,43)
        tri=[point(xx-radius*.7*math.cos(angle-.27),yy-radius*.7*math.sin(angle-.27)),
             point(xx+radius*math.cos(angle),yy+radius*math.sin(angle)),
             point(xx-radius*.45*math.cos(angle+.48),yy-radius*.45*math.sin(angle+.48))]
        pdraw.polygon(tri,fill=rng.choice([(139,62,231,184),(233,151,255,191),
                                           (76,78,194,212)]))
        pdraw.line(tri+[tri[0]],fill=(240,199,255,182),width=round(1.2*S))
    canvas=Image.alpha_composite(canvas,glow.filter(ImageFilter.GaussianBlur(17*S)))
    canvas=Image.alpha_composite(canvas,sharp)
    draw=ImageDraw.Draw(canvas,"RGBA")
    # Foreground crystal peaks with exact hard edges, layered translucencies.
    for side in [-1,1]:
        for i in range(15):
            base_x=512+side*(265+i*23)
            height=rng.uniform(44,172)*(1.2 if i%4==0 else 1)
            base_y=rng.uniform(690,765)
            width=rng.uniform(13,37)
            tip=point(base_x+side*rng.uniform(-12,15),base_y-height)
            left=point(base_x-width,base_y)
            right=point(base_x+width,base_y+3)
            draw.polygon([left,tip,right],fill=(25,13,78,230))
            draw.polygon([tip,point(base_x,base_y+3),right],fill=(83,36,164,207))
            draw.line([tip,right],fill=(184,92,245,220),width=round(1.7*S))
            draw.line([tip,left],fill=(112,66,226,201),width=round(1.2*S))
    # Mystic lake with mirrored portal reflections and clean horizontal waves.
    draw.rectangle((*point(0,742),*point(1024,1024)),fill=(12,7,41,228))
    water=Image.new("RGBA",canvas.size,(0,0,0,0))
    wdraw=ImageDraw.Draw(water)
    for j in range(310):
        y=747+j*.97
        spread=80+(y-740)*1.12
        x=512+rng.gauss(0,spread*.54)
        length=rng.uniform(3,53)*(1+(y-740)/410)
        w=max(.5,1.3-(y-740)/1300)
        level=math.exp(-abs(x-512)/(100+(y-740)*2))
        alpha=round(rng.uniform(48,185)*level)
        if alpha<8:continue
        wdraw.line([point(x-length,y),point(x+length,y+rng.uniform(-1,1))],
                   fill=(178,95,255,alpha),width=max(1,round(w*S)))
    for j in range(64):
        y=754+j*3.95
        xwidth=55+(y-754)*1.05
        wiggle=math.sin(y*.15)*15
        wdraw.arc((*point(512-xwidth, y-4),*point(512+xwidth, y+8)),
                  start=5,end=173,fill=(177,119,255,rng.randint(48,152)),
                  width=max(1,round(S)))
    canvas=Image.alpha_composite(canvas,water)
    # Bright central horizon star and crisp diffraction details.
    final=ImageDraw.Draw(canvas,"RGBA")
    for r,alpha in [(47,24),(25,34),(12,80),(4,235)]:
        final.ellipse((*point(512-r,751-r),*point(512+r,751+r)),
                      fill=(220,157,255,alpha))
    final.line([point(512,693),point(512,818)],fill=(226,189,255,130),width=round(1.5*S))
    final.line([point(447,751),point(579,751)],fill=(248,204,255,123),width=round(1.5*S))
    dest.parent.mkdir(parents=True,exist_ok=True)
    canvas.convert("RGB").save(dest,"PNG",optimize=True)
    with Image.open(dest) as image:
        if image.size!=(SIZE,SIZE) or image.format!="PNG":
            raise RuntimeError("Invalid recreated crystal portal art")
    return SIZE,SIZE

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: recreate_crystal_portal.py OUTPUT.png")
    print("CHAROITE_RECREATED_CRYSTAL_PORTAL="+str(render(sys.argv[1])))
