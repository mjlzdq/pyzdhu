#!/usr/bin/env python3
"""Generate tab icons for mini program - run with: python3 scripts/gen_icons.py"""
import struct, zlib, os, math

SIZE = 81
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images', 'tab')
os.makedirs(DIR, exist_ok=True)

def png(pixels):
    def chunk(ctype, data):
        b = (ctype.encode() if isinstance(ctype, str) else ctype) + data
        return struct.pack('>I', len(data)) + b + struct.pack('>I', zlib.crc32(b) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', SIZE, SIZE, 8, 6, 0, 0, 0)
    raw = b''.join(b'\x00' + pixels[i*SIZE*4:(i+1)*SIZE*4] for i in range(SIZE))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')

class P:
    def __init__(self): self.s = SIZE; self.p = bytearray(SIZE * SIZE * 4)
    def sP(self, x, y, r, g, b, a=255):
        if 0 <= x < self.s and 0 <= y < self.s:
            i = (y * self.s + x) * 4; self.p[i:i+4] = [r, g, b, a]
    def fR(self, x, y, w, h, r, g, b, a=255):
        for _y in range(max(0,y), min(self.s,y+h)):
            for _x in range(max(0,x), min(self.s,x+w)): self.sP(_x,_y,r,g,b,a)
    def fC(self, cx, cy, rd, r, g, b, a=255):
        for _y in range(max(0,int(cx-rd)), min(self.s,int(cy+rd)+1)):
            for _x in range(max(0,int(cy-rd)), min(self.s,int(cy+rd)+1)):
                if (_x-cx)**2+(_y-cy)**2 <= rd**2: self.sP(_x,_y,r,g,b,a)
    def fT(self, x1,y1,x2,y2,x3,y3,r,g,b):
        pts = [(x1,y1),(x2,y2),(x3,y3)]
        ymin,ymax = max(0,int(min(y for _,y in pts))), min(self.s-1,int(max(y for _,y in pts)))
        for y in range(ymin, ymax+1):
            ins = []
            for i in range(3):
                (ax,ay),(bx,by) = pts[i],pts[(i+1)%3]
                if (ay<=y<by) or (by<=y<ay):
                    ins.append(int(ax+(y-ay)/(by-ay)*(bx-ax)))
            if len(ins)==2:
                for x in range(max(0,min(ins)), min(self.s,max(ins))+1): self.sP(x,y,r,g,b)
    def dL(self, x0,y0,x1,y1,r,g,b,t=6):
        dx,dy = abs(x1-x0),abs(y1-y0); sx,sy=(1 if x0<x1 else -1),(1 if y0<y1 else -1); e=dx-dy
        while True:
            self.fC(x0,y0,t/2,r,g,b)
            if x0==x1 and y0==y1: break
            e2=2*e
            if e2>-dy: e-=dy; x0+=sx
            if e2<dx: e+=dx; y0+=sy
    def B(self): return bytes(self.p)

C = SIZE // 2
GR = (153,153,153); GN = (7,193,96)

def home(a):
    c = GN if a else GR; p = P()
    p.fT(C,14,C-28,40,C+28,40,*c); p.fR(C-28,38,56,28,*c)
    p.fR(C-9,48,18,18,255,255,255); p.fR(C-24,44,10,10,255,255,255); p.fR(C+14,44,10,10,255,255,255)
    return png(p.B())
def cat(a):
    c = GN if a else GR; p = P(); s,g=17,5
    p.fR(C-s-g,C-s-g,s,s,*c); p.fR(C+g,C-s-g,s,s,*c); p.fR(C-s-g,C+g,s,s,*c); p.fR(C+g,C+g,s,s,*c)
    return png(p.B())
def src(a):
    c = GN if a else GR; p = P()
    p.fC(C-4,C-4,20,*c); p.fC(C-4,C-4,12,255,255,255)
    hsx=C-4+round(math.cos(math.pi/4)*18); hsy=C-4+round(math.sin(math.pi/4)*18)
    p.dL(hsx,hsy,C+16,C+16,*c,7)
    return png(p.B())
def mine(a):
    c = GN if a else GR; p = P()
    p.fC(C,25,15,*c); p.fC(C,58,24,*c)
    for y in range(42):
        for x in range(SIZE):
            if (x-C)**2+(y-58)**2 < 24**2: p.sP(x,y,255,255,255,0)
    return png(p.B())

for name, fn in [('home',lambda:home(False)),('home-active',lambda:home(True)),
    ('category',lambda:cat(False)),('category-active',lambda:cat(True)),
    ('search',lambda:src(False)),('search-active',lambda:src(True)),
    ('mine',lambda:mine(False)),('mine-active',lambda:mine(True))]:
    data = fn()
    with open(os.path.join(DIR, name+'.png'), 'wb') as f: f.write(data)
    print(f'OK {name}.png ({len(data)}b)')
print('DONE')
