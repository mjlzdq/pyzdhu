"""
生成小程序 Tab 图标 - Python 无依赖版本
运行: python3 scripts/generate-icons.py
"""
import struct, zlib, os, math

SIZE = 81
DIR = os.path.join(os.path.dirname(__file__), '..', 'images', 'tab')
os.makedirs(DIR, exist_ok=True)

def create_png(pixels):
    """从 RGBA 像素数组 (bytes) 生成 PNG bytes"""
    def chunk(ctype, data):
        c = ctype.encode('ascii') if isinstance(ctype, str) else ctype
        body = c + data
        crc = zlib.crc32(body) & 0xffffffff
        return struct.pack('>I', len(data)) + body + struct.pack('>I', crc)
    
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', SIZE, SIZE, 8, 6, 0, 0, 0)
    raw = b''
    for y in range(SIZE):
        raw += b'\x00' + pixels[y * SIZE * 4:(y + 1) * SIZE * 4]
    
    return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')

class PixelBuffer:
    def __init__(self, size=SIZE):
        self.size = size
        self.px = bytearray(size * size * 4)
    
    def set(self, x, y, r, g, b, a=255):
        if 0 <= x < self.size and 0 <= y < self.size:
            idx = (y * self.size + x) * 4
            self.px[idx:idx+4] = [r, g, b, a]
    
    def fill_rect(self, x, y, w, h, r, g, b, a=255):
        for py in range(max(0,y), min(self.size, y+h)):
            for px in range(max(0,x), min(self.size, x+w)):
                self.set(px, py, r, g, b, a)
    
    def fill_circle(self, cx, cy, rad, r, g, b, a=255):
        for py in range(max(0,int(cy-rad)), min(self.size, int(cy+rad)+1)):
            for px in range(max(0,int(cx-rad)), min(self.size, int(cx-rad)+1)):
                if (px-cx)**2 + (py-cy)**2 <= rad*rad:
                    self.set(px, py, r, g, b, a)
    
    def fill_triangle(self, x1, y1, x2, y2, x3, y3, r, g, b):
        pts = [(x1,y1),(x2,y2),(x3,y3)]
        ymin = max(0, int(min(y for _,y in pts)))
        ymax = min(self.size-1, int(max(y for _,y in pts)))
        for y in range(ymin, ymax+1):
            inters = []
            for i in range(3):
                (ax, ay), (bx, by) = pts[i], pts[(i+1)%3]
                if (ay <= y < by) or (by <= y < ay):
                    t = (y - ay) / (by - ay)
                    inters.append(int(ax + t*(bx - ax)))
            if len(inters) == 2:
                for x in range(max(0, min(inters)), min(self.size, max(inters))+1):
                    self.set(x, y, r, g, b)
    
    def draw_line(self, x0, y0, x1, y1, r, g, b, thick=6):
        dx, dy = abs(x1-x0), abs(y1-y0)
        sx, sy = (1 if x0<x1 else -1), (1 if y0<y1 else -1)
        err = dx - dy
        while True:
            self.fill_circle(x0, y0, thick/2, r, g, b)
            if x0 == x1 and y0 == y1: break
            e2 = 2*err
            if e2 > -dy: err -= dy; x0 += sx
            if e2 < dx: err += dx; y0 += sy
    
    def to_bytes(self): return bytes(self.px)

C = SIZE // 2

def draw_home(active):
    color = (7, 193, 96) if active else (153, 153, 153)
    buf = PixelBuffer()
    buf.fill_triangle(C, 14, C-28, 40, C+28, 40, *color)
    buf.fill_rect(C-28, 38, 56, 28, *color)
    # 门
    buf.fill_rect(C-9, 48, 18, 18, 255, 255, 255)
    # 窗户
    buf.fill_rect(C-24, 44, 10, 10, 255, 255, 255)
    buf.fill_rect(C+14, 44, 10, 10, 255, 255, 255)
    return create_png(buf.to_bytes())

def draw_category(active):
    color = (7, 193, 96) if active else (153, 153, 153)
    buf = PixelBuffer()
    s, gap = 17, 5
    buf.fill_rect(C-s-gap, C-s-gap, s, s, *color)
    buf.fill_rect(C+gap, C-s-gap, s, s, *color)
    buf.fill_rect(C-s-gap, C+gap, s, s, *color)
    buf.fill_rect(C+gap, C+gap, s, s, *color)
    return create_png(buf.to_bytes())

def draw_search(active):
    color = (7, 193, 96) if active else (153, 153, 153)
    buf = PixelBuffer()
    # 镜片圆环
    buf.fill_circle(C-4, C-4, 20, *color)
    buf.fill_circle(C-4, C-4, 12, 255, 255, 255)
    # 手柄
    import math
    angle = math.pi / 4
    hsx = C-4 + round(math.cos(angle)*18)
    hsy = C-4 + round(math.sin(angle)*18)
    buf.draw_line(hsx, hsy, C+16, C+16, *color, 7)
    return create_png(buf.to_bytes())

def draw_mine(active):
    color = (7, 193, 96) if active else (153, 153, 153)
    buf = PixelBuffer()
    # 头
    buf.fill_circle(C, 25, 15, *color)
    # 身体（半圆效果）
    buf.fill_circle(C, 58, 24, *color)
    # 清除身体上半部分形成半圆
    for y in range(42):
        for x in range(SIZE):
            if (x-C)**2 + (y-58)**2 < 24**2:
                buf.set(x, y, 255, 255, 255, 0)
    return create_png(buf.to_bytes())

icons = [
    ('home', draw_home(False)),
    ('home-active', draw_home(True)),
    ('category', draw_category(False)),
    ('category-active', draw_category(True)),
    ('search', draw_search(False)),
    ('search-active', draw_search(True)),
    ('mine', draw_mine(False)),
    ('mine-active', draw_mine(True)),
]

print('🎨 正在生成 Tab 图标...\n')
for name, data in icons:
    path = os.path.join(DIR, f'{name}.png')
    with open(path, 'wb') as f:
        f.write(data)
    print(f'  ✅ {name}.png ({len(data)} bytes)')

print('\n🎉 全部完成！共生成 8 个 Tab 图标')
