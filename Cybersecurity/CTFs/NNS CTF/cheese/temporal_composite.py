"""Test persistence-style composites of consecutive AS1130 frames."""

from pathlib import Path
from PIL import Image, ImageDraw

from render_frames import read_map, render


WINDOW = 6
MODE = "majority"  # one of: or, and, majority


def get_grids():
    vals=[]
    for line in Path('i2c_packets.txt').read_text().splitlines():
        p=[int(x,16) for x in line.split()[2:]]
        if len(p)==134 and p[:2]==[0x60,0x18]: vals.append(p[2:])
    anodes,cathodes=read_map()
    return [[row[::-1] for row in render(v,anodes,cathodes)[::-1]] for v in vals]


def combine(grids):
    threshold={"or":1,"and":len(grids),"majority":(len(grids)+1)//2}[MODE]
    return ["".join("#" if sum(g[y][x]=='#' for g in grids)>=threshold else "." for x in range(17)) for y in range(7)]


def main():
    source=get_grids()
    # Sample at a nominal character period, retaining readable label numbering.
    grids=[combine(source[i:i+WINDOW]) for i in range(0,len(source)-WINDOW+1,6)]
    scale,label,cols=12,18,10
    cw,ch=17*scale,7*scale+label
    im=Image.new('RGB',(cw*cols,ch*((len(grids)+cols-1)//cols)), '#202020')
    d=ImageDraw.Draw(im)
    for i,g in enumerate(grids):
        x0,y0=i%cols*cw,i//cols*ch
        d.text((x0+2,y0),str(i*6),fill='white')
        for y,row in enumerate(g):
            for x,v in enumerate(row):
                if v=='#':d.rectangle((x0+x*scale,y0+label+y*scale,x0+(x+1)*scale-1,y0+label+(y+1)*scale-1),fill='white')
    im.save(f'composite_{MODE}_{WINDOW}.png')


if __name__=='__main__':main()
