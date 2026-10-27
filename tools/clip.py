import sys, math, subprocess, os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
name, url = sys.argv[1], sys.argv[2]
FPS=24; W,H=1600,1000
x0,y0,ww,bar=96,90,1408,34
def frame(shot):
    c=Image.new('RGB',(W,H),'#F3F4F6'); d=ImageDraw.Draw(c)
    d.rectangle([x0-1,y0-1,x0+ww,H],fill='#E4E6EA')
    d.rectangle([x0,y0,x0+ww-1,y0+bar-1],fill='#FFFFFF')
    d.line([x0,y0+bar-1,x0+ww-1,y0+bar-1],fill='#E4E6EA')
    for k in range(3):
        cx=x0+18+k*16; cy=y0+bar//2
        d.rectangle([cx-4,cy-4,cx+4,cy+4],fill='#D5D9DF' if k<2 else '#1F4FD8')
    s=shot.resize((ww,round(shot.height*ww/shot.width)),Image.LANCZOS)
    c.paste(s.crop((0,0,ww,H-y0-bar)),(x0,y0+bar)); return c
ease=lambda t:0.5-0.5*math.cos(math.pi*t)
os.makedirs('frames',exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_page(viewport={'width':1440,'height':900},device_scale_factor=2,locale='ca-ES')
    pg.goto(url,wait_until='load',timeout=90000); pg.wait_for_timeout(2500)
    for t in ('Només essencials','Rebutja','Rebutjar'):
        try: pg.get_by_role('button',name=t,exact=True).first.click(timeout=1500); break
        except Exception: pass
    pg.add_style_tag(content='html{scroll-behavior:auto!important}*{scrollbar-width:none!important}::-webkit-scrollbar{display:none}')
    dist=min(1350, pg.evaluate('document.documentElement.scrollHeight-innerHeight'))
    for y in range(0,dist+1,300): pg.evaluate(f'scrollTo(0,{y})'); pg.wait_for_timeout(250)
    pg.evaluate('scrollTo(0,0)'); pg.wait_for_timeout(1500)
    hold=int(0.6*FPS); move=int(2.4*FPS)
    ys=[0]*hold+[round(dist*ease(i/move)) for i in range(move+1)]+[dist]*hold+[round(dist*(1-ease(i/move))) for i in range(1,move)]
    import io
    for i,y in enumerate(ys):
        pg.evaluate(f'scrollTo(0,{y})'); pg.wait_for_timeout(40)
        shot=Image.open(io.BytesIO(pg.screenshot())).convert('RGB')
        frame(shot).save(f'frames/{i:04d}.png')
    b.close()
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i','frames/%04d.png','-vf','scale=1280:800:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','26','-pix_fmt','yuv420p','-movflags','+faststart','-an',f'clips/{name}.mp4'],check=True)
