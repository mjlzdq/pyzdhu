#!/usr/bin/env python3
"""生成微信小程序Tab图标 - 纯代码生成最小PNG, 保证 < 40KB"""
import struct, zlib, os

S = 81  # 尺寸
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images', 'tab')
os.makedirs(DIR, exist_ok=True)

def make_png(px_bytes):
    """从RGBA像素bytes生成PNG"""
    def chunk(ctype, data):
        body = (ctype if isinstance(ctype, bytes) else ctype.encode()) + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', S, S, 8, 6, 0, 0, 0)
    # 每行前加filter byte=0
    raw = bytearray()
    for y in range(S):
        raw += b'\x00' + px_bytes[y*S*4:(y+1)*S*4]
    return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(bytes(raw))) + chunk(b'IEND', b'')

class Canvas:
    def __init__(self):
        self.data = bytearray(S * S * 4)  # RGBA
    def px(self, x, y, r, g, b, a=255):
        if 0 <= x < S and 0 <= y < S:
            i = (y * S + x) * 4
            self.data[i], self.data[i+1], self.data[i+2], self.data[i+3] = r, g, b, a
    def rect(self, x, y, w, h, r, g, b, a=255):
        for py in range(max(0,y), min(S, y+h)):
            for px in range(max(0,x), min(S, x+w)):
                self.px(px, py, r, g, b, a)
    def circle(self, cx, cy, rad, r, g, b, a=255):
        for py in range(max(0,int(cy-rad)), min(S, int(cy+rad)+1)):
            for px in range(max(0,int(cx-rad)), min(S, int(cx+rad)+1)):
                if (px-cx)**2 + (py-cy)**2 <= rad**2:
                    self.px(px, py, r, g, b, a)
    def tri(self, x1,y1, x2,y2, x3,y3, r,g,b):
        pts = [(x1,y1),(x2,y2),(x3,y3)]
        ymin, ymax = max(0, int(min(y for _,y in pts))), min(S-1, int(max(y for _,y in pts)))
        for y in range(ymin, ymax+1):
            ins = []
            for i in range(3):
                (ax,ay),(bx,by) = pts[i], pts[(i+1)%3]
                if (ay<=y<by) or (by<=y<ay):
                    ins.append(int(ax + (y-ay)/(by-ay)*(bx-ax)))
            if len(ins)==2:
                lo, hi = min(ins), max(ins)
                for x in range(max(0,lo), min(S, hi+1)):
                    self.px(x, y, r, g, b)
    def line(self, x0,y0, x1,y1, r,g,b, t=5):
        dx, dy = abs(x1-x0), abs(y1-y0)
        sx = 1 if x0<x1 else -1
        sy = 1 if y0<y1 else -1
        err = dx - dy
        while True:
            self.circle(x0, y0, t/2, r, g, b)
            if x0==x1 and y0==y1: break
            e2 = 2*err
            if e2 > -dy: err -= dy; x0 += sx
            if e2 < dx: err += dx; y0 += sy
    def get(self): return bytes(self.data)

C = S // 2  # center
G = (153,153,153)   # gray unselected
GR = (7,193,96)     # green selected

def icon_home(active):
    color = GR if active else G
    c = Canvas()
    # 屋顶三角形
    c.tri(C, 14, C-26, 38, C+26, 38, *color)
    # 墙壁矩形
    c.rect(C-26, 36, 52, 28, *color)
    # 门
    c.rect(C-8, 48, 16, 16, 255,255,255)
    # 左窗
    c.rect(C-22, 44, 9, 9, 255,255,255)
    # 右窗
    c.rect(C+13, 44, 9, 9, 255,255,255)
    return make_png(c.get())

def icon_category(active):
    color = GR if active else G
    c = Canvas()
    sz, gap = 15, 5
    c.rect(C-sz-gap, C-sz-gap, sz, sz, *color)
    c.rect(C+gap, C-sz-gap, sz, sz, *color)
    c.rect(C-sz-gap, C+gap, sz, sz, *color)
    c.rect(C+gap, C+gap, sz, sz, *color)
    return make_png(c.get())

def icon_search(active):
    import math
    color = GR if active else G
    c = Canvas()
    # 镜片圆环
    c.circle(C-3, C-3, 18, *color)
    c.circle(C-3, C-3, 11, 255,255,255)
    # 手柄
    angle = math.pi / 4
    hx = C-3 + round(math.cos(angle)*15)
    hy = C-3 + round(math.sin(angle)*15)
    c.line(hx, hy, C+14, C+14, *color, 6)
    return make_png(c.get())

def icon_mine(active):
    color = GR if active else G
    c = Canvas()
    # 头
    c.circle(C, 24, 13, *color)
    # 身体圆（下半部分）
    c.circle(C, 56, 22, *color)
    # 清除身体上半部形成半圆效果
    for y in range(40):
        for x in range(S):
            if (x-C)**2 + (y-56)**2 < 22**2:
                c.px(x, y, 0,0,0,0)
    return make_png(c.get())

# 生成全部8个图标
icons = [
    ('home', icon_home(False)),
    ('home-active', icon_home(True)),
    ('category', icon_category(False)),
    ('category-active', icon_category(True)),
    ('search', icon_search(False)),
    ('search-active', icon_search(True)),
    ('mine', icon_mine(False)),
    ('mine-active', icon_mine(True)),
]

for name, data in icons:
    path = os.path.join(DIR, f'{name}.png')
    with open(path, 'wb') as f:
        f.write(data)
    size_kb = len(data) / 1024
    status = '✅' if size_kb <= 40 else '❌ TOO BIG!'
    print(f'  {status} {name}.png — {size_kb:.1f} KB')

print('\nDone!')
