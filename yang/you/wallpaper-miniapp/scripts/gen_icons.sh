#!/bin/bash
# Generate tab icons using python3
python3 << 'PYEOF'
import struct,zlib,os,math
SIZE=81
DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','images','tab')
os.makedirs(DIR,exist_ok=True)
def png(px):
 def ck(ct,d):
  b=(ct.encode() if isinstance(ct,str) else ct)+d
  return struct.pack('>I',len(d))+b+struct.pack('>I',zlib.crc32(b)&0xffffffff)
 ihdr=struct.pack('>IIBBBBB',SIZE,SIZE,8,6,0,0,0)
 raw=b''.join(b'\x00'+px[i*SIZE*4:(i+1)*SIZE*4] for i in range(SIZE))
 return b'\x89PNG\r\n\x1a\n'+ck(b'IHDR',ihdr)+ck(b'IDAT',zlib.compress(raw))+ck(b'IEND',b'')
class B:
 def __init__(self):
  self.s=SIZE;self.p=bytearray(SIZE*SIZE*4)
 def sp(self,x,y,r,g,b,a=255):
  if 0<=x<self.s and 0<=y<self.s:
   i=(y*self.s+x)*4;self.p[i:i+4]=[r,g,b,a]
 def fr(self,x,y,w,h,r,g,b,a=255):
  for _y in range(max(0,y),min(self.s,y+h)):
   for _x in range(max(0,x),min(self.s,x+w)):self.sp(_x,_y,r,g,b,a)
 def fc(self,cx,cy,rd,r,g,b,a=255):
  for _y in range(max(0,int(cx-rd)),min(self.s,int(cy+rd)+1)):
   for _x in range(max(0,int(cx-rd)),min(self.s,int(cx+rd)+1)):
    if(_x-cx)**2+(_y-cy)**2<=rd**2:self.sp(_x,_y,r,g,b,a)
 def ft(self,x1,y1,x2,y2,x3,y3,r,g,b):
  pts=[(x1,y1),(x2,y2),(x3,y3)]
  ymin,ymax=max(0,int(min(y for _,y in pts))),min(self.s-1,int(max(y for _,y in pts)))
  for y in range(ymin,ymax+1):
   ins=[]
   for i in range(3):
    (ax,ay),(bx,by)=pts[i],pts[(i+1)%3]
    if(ay<=y<by)or(by<=y<ay):ins.append(int(ax+(y-ay)/(by-ay)*(bx-ax)))
   if len(ins)==2:
    for x in range(max(0,min(ins)),min(self.s,max(ins))+1):self.sp(x,y,r,g,b)
 def dl(self,x0,y0,x1,y1,r,g,b,t=6):
  dx,dy=abs(x1-x0),abs(y1-y0);sx,sy=(1 if x0<x1 else -1),(1 if y0<y1 else -1);e=dx-dy
  while True:
   self.fc(x0,y0,t/2,r,g,b)
   if x0==x1 and y0==y1:break
   e2=2*e
   if e2>-dy:e-=dy;x0+=sx
   if e2<dx:e+=dx;y0+=sy
 def data(self):return bytes(self.p)
C=SIZE//2
GR=(153,153,153);GN=(7,193,96)
def home(a):
 c=GN if a else GR;p=B()
 p.ft(C,14,C-28,40,C+28,40,*c);p.fr(C-28,38,56,28,*c)
 p.fr(C-9,48,18,18,255,255,255);p.fr(C-24,44,10,10,255,255,255);p.fr(C+14,44,10,10,255,255,255)
 return png(p.data())
def cat(a):
 c=GN if a else GR;p=B();s,g=17,5
 p.fr(C-s-g,C-s-g,s,s,*c);p.fr(C+g,C-s-g,s,s,*c);p.fr(C-s-g,C+g,s,s,*c);p.fr(C+g,C+g,s,s,*c)
 return png(p.data())
def srch(a):
 c=GN if a else GR;p=B()
 p.fc(C-4,C-4,20,*c);p.fc(C-4,C-4,12,255,255,255)
 hsx=C-4+round(math.cos(math.pi/4)*18);hsy=C-4+round(math.sin(math.pi/4)*18)
 p.dl(hsx,hsy,C+16,C+16,*c,7)
 return png(p.data())
def mine(a):
 c=GN if a else GR;p=B()
 p.fc(C,25,15,*c);p.fc(C,58,24,*c)
 for y in range(42):
  for x in range(SIZE):
   if(x-C)**2+(y-58)**2<24**2:p.sp(x,y,255,255,255,0)
 return png(p.data())
for name,fn in[('home',lambda:home(False)),('home-active',lambda:home(True)),('category',lambda:cat(False)),('category-active',lambda:cat(True)),('search',lambda:srch(False)),('search-active',lambda:srch(True)),('mine',lambda:mine(False)),('mine-active',lambda:mine(True))]:
 d=fn()
 with open(os.path.join(DIR,name+'.png'),'wb') as f:f.write(d)
 print(f'OK {name}.png ({len(d)})')
print('ALL DONE')
PYEOF
