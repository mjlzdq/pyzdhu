#!/usr/bin/env python3
import struct,zlib,os,math
S=81;D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','images','tab');os.makedirs(D,exist_ok=True)
def P(p):
 def C(t,d):
  b=(t.encode() if type(t)==str else t)+d;return struct.pack('>I',len(d))+b+struct.pack('>I',zlib.crc32(b)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+C(b'IHDR',struct.pack('>IIBBBBB',S,S,8,6,0,0,0))+C(b'IDAT',zlib.compress(bytes(bytearray([0])+bytes(p))))+C(b'IEND',b'')
class Z:
 def __init__(self):self.d=bytearray(S*S*4)
 def p(self,x,y,r,g,b,a=255):
  if 0<=x<S and 0<=y<S:i=(y*S+x)*4;self.d[i:i+4]=[r,g,b,a]
 def R(self,x,y,w,h,r,g,b,a=255):
  for _y in range(max(0,y),min(S,y+h)):
   for _x in range(max(0,x),min(S,x+w)):self.p(_x,_y,r,g,b,a)
 def O(self,cx,cr,r2,r,g,b,a=255):
  for _y in range(max(0,int(cx-cr)),min(S,int(cx+cr)+1)):
   for _x in range(max(0,int(r2-cr)),min(S,int(r2+cr)+1)): 
    if(_x-cx)**2+(_y-r2)**2<=cr*cr:self.p(_x,_y,r,g,b,a)
 def T(self,x1,y1,x2,y2,x3,y3,r,g,b):
  ps=[(x1,y1),(x2,y2),(x3,y3)];yn=max(0,int(min(y for _,y in ps)));yx=min(S-1,int(max(y for _,y in ps)))
  for y in range(yn,yx+1):
   is_=[]
   for i in range(3):(ax,ay),(bx,by)=ps[i],ps[(i+1)%3]
   if(ay<=y<by)or(by<=y<ay):is_.append(int(ax+(y-ay)/(by-ay)*(bx-ax)))
   if len(is_)==2:
    lo,hi=min(is_),max(is_)
    for x in range(max(0,lo),min(S,hi+1)):self.p(x,y,r,g,b)
 def L(self,x0,y0,x1,y1,r,g,b,t=5):
  dx,dy=abs(x1-x0),abs(y1-y0);sx,sy=(1if x0<x1 else -1),(1if y0<y1 else -1);e=dx-dy
  while True:self.O(x0,y0,t/2,x0,y0,r,g,b)
   if x0==x1 and y0==y1:break
   e2=2*e
   if e2>-dy:e-=dy;x0+=sx
   if e2<dx:e+=dx;y0+=sy
 def g(self):return bytes(self.d)
c=S//2;G=(153,153,153);GR=(7,193,96)
def H(a):
 cl=GR if a else G;z=Z();z.T(c,14,c-26,38,c+26,38,*cl);z.R(c-26,36,52,28,*cl);z.R(c-8,48,16,16,255,255,255);z.R(c-22,44,9,9,255,255,255);z.R(c+13,44,9,9,255,255,255);return P(z.g())
def Ct(a):
 cl=GR if a else G;z=Z();s,gp=15,5;z.R(c-s-gp,c-s-gp,s,s,*cl);z.R(c+gp,c-s-gp,s,s,*cl);z.R(c-s-gp,c+gp,s,s,*cl);z.R(c+gp,c+gp,s,s,*cl);return P(z.g())
def Se(a):
 import math;cl=GR if a else G;z=Z();z.O(c-3,c-3,18,c-3,c-3,*cl);z.O(c-3,c-3,11,c-3,c-3,255,255,255);hx=c-3+round(math.cos(math.pi/4)*15);hy=c-3+round(math.sin(math.pi/4)*15);z.L(hx,hy,c+14,c+14,*cl,6);return P(z.g())
def M(a):
 cl=GR if a else G;z=Z();z.O(c,24,13,c,24,*cl);z.O(c,56,22,c,56,*cl);
 for y in range(40):
  for x in range(S):
   if(x-c)**2+(y-56)**2<22**2:z.p(x,y,0,0,0,0)
 return P(z.g())
for n,f in[('home',lambda:H(False)),('home-active',lambda:H(True)),('category',lambda:Ct(False)),('category-active',lambda:Ct(True)),('search',lambda:Se(False)),('search-active',lambda:Se(True)),('mine',lambda:M(False)),('mine-active',lambda:M(True))]:
 d=f();p=os.path.join(D,n+'.png')
 with open(p,'wb') as F:F.write(d)
 print(f'OK {n}.png {len(d)/1024:.1f}KB')
print('ALL DONE')
