const fs = require('fs');
const zlib = require('zlib');
const path = require('path');

const S = 81;
const C = Math.floor(S / 2);
const DIR = __dirname + '/../images/tab';

function makePNG(pixels) {
    function crc32(buf) {
        let table = [], crc = 0xFFFFFFFF;
        for (let i = 0; i < 256; i++) { let c = i; for (let j = 0; j < 8; j++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; table[i] = c; }
        for (let i = 0; i < buf.length; i++) crc = table[(crc ^ buf[i]) & 0xFF] ^ (crc >>> 8);
        return (crc ^ 0xFFFFFFFF) >>> 0;
    }
    function chunk(type, data) {
        const body = Buffer.concat([Buffer.from(type), data]);
        return Buffer.concat([
            Buffer.alloc(4, 0), body,
            Buffer.alloc(4, 0)
        ]);
    }
    
    const sig = Buffer.from([137,80,78,71,13,10,26,10]);
    const ihdrData = Buffer.alloc(13);
    ihdrData.writeUInt32BE(S, 0);
    ihdrData.writeUInt32BE(S, 4);
    ihdrData[8] = 8; ihdrData[9] = 6;
    const raw = Buffer.alloc(S * (1 + S * 4));
    for (let y = 0; y < S; y++) {
        raw[y * (1 + S * 4)] = 0;
        pixels.copy(raw, y * (1 + S * 4) + 1, y * S * 4, (y + 1) * S * 4);
    }
    const idat = zlib.deflateSync(raw);
    return Buffer.concat([sig, 
        Buffer.from([0,0,0,13,73,72,68,82,...ihdrData,0,0,0,0]),
        Buffer.from([0,0,0,(idat.length>>24)&0xff,(idat.length>>16)&0xff,(idat.length>>8)&0xff,idat.length&0xff,73,68,65,84,...idat]),
        Buffer.from([0,0,0,0,73,69,78,68,82])
    ]);
}

function createBuf() {
    return Buffer.alloc(S * S * 4, 0);
}
function setP(buf, x, y, r, g, b, a) {
    if (x < 0 || x >= S || y < 0 || y >= S) return;
    const i = (y * S + x) * 4;
    buf[i] = r & 255; buf[i+1] = g & 255; buf[i+2] = b & 255; buf[i+3] = (a === undefined ? 255 : a) & 255;
}
function fillRect(b, x, y, w, h, r, g, b2, a) {
    for (let py = Math.max(0,y); py < Math.min(S, y+h); py++)
        for (let px = Math.max(0,x); px < Math.min(S, x+w); px++)
            setP(b, px, py, r, g, b2, a);
}
function fillCircle(b, cx, cy, rad, r, g, b2, a) {
    for (let py = Math.max(0,Math.floor(cy-rad)); py <= Math.min(S-1,Math.ceil(cy+rad)); py++)
        for (let px = Math.max(0,Math.floor(cx-rad)); px <= Math.min(S-1,Math.ceil(cx+rad)); px++)
            if ((px-cx)*(px-cx)+(py-cy)*(py-cy) <= rad*rad)
                setP(b, px, py, r, g, b2, a);
}
function tri(b, x1,y1,x2,y2,x3,y3,r,g,b2) {
    const ymin=Math.max(0,Math.round(Math.min(y1,y2,y3))), ymax=Math.min(S-1,Math.round(Math.max(y1,y2,y3)));
    for (let y=ymin;y<=ymax;y++) {
        const ins=[];
        [[x1,y1],[x2,y2],[x3,y3]].forEach(([ax,ay],i,arr)=>{
            const [bx,by]=arr[(i+1)%3];
            if ((ay<=y&&by>y)||(by<=y&&ay>y)) ins.push(ax+(y-ay)/(by-ay)*(bx-ax));
        });
        if (ins.length===2) {
            const [lo,hi]=[Math.round(Math.min(ins[0],ins[1])), Math.round(Math.max(ins[0],ins[1]))];
            for (let x=Math.max(0,lo);x<=Math.min(S-1,hi);x++) setP(b,x,y,r,g,b2);
        }
    }
}

const GR=[153,153,153], GN=[7,193,96];

function home(act) {
    const c=act?GN:GR, b=createBuf();
    tri(b,C,14,C-26,38,C+26,38,...c);
    fillRect(b,C-26,36,52,28,...c);
    fillRect(b,C-8,48,16,16,255,255,255);
    fillRect(b,C-22,44,9,9,255,255,255);
    fillRect(b,C+13,44,9,9,255,255,255);
    return makePNG(b);
}
function cat(act) {
    const c=act?GN:GR, b=createBuf();
    const s=15, g=5;
    fillRect(b,C-s-g,C-s-g,s,s,...c); fillRect(b,C+g,C-s-g,s,s,...c);
    fillRect(b,C-s-g,C+g,s,s,...c); fillRect(b,C+g,C+g,s,s,...c);
    return makePNG(b);
}
function search(act) {
    const c=act?GN:GR, b=createBuf();
    fillCircle(b,C-3,C-3,17,...c);
    fillCircle(b,C-3,C-3,11,255,255,255);
    // handle
    const a=Math.PI/4, hx=C-3+Math.cos(a)*14, hy=C-3+Math.sin(a)*14;
    for (let t=0;t<=1;t+=0.05) {
        const mx=Math.round(hx+t*(C+13-hx)), my=Math.round(hy+t*(C+13-hy));
        fillCircle(b,mx,my,2.5,...c);
    }
    return makePNG(b);
}
function mine(act) {
    const c=act?GN:GR, b=createBuf();
    fillCircle(b,C,24,13,...c);
    fillCircle(b,C,56,22,...c);
    // clear upper half of body
    for (let y=0;y<40;y++)
        for (let x=0;x<S;x++)
            if ((x-C)*(x-C)+(y-56)*(y-56)<22*22) setP(b,x,y,0,0,0,0);
    return makePNG(b);
}

if (!fs.existsSync(DIR)) fs.mkdirSync(DIR, {recursive:true});

const icons = [
    ['home',home(false)],['home-active',home(true)],
    ['category',cat(false)],['category-active',cat(true)],
    ['search',search(false)],['search-active',search(true)],
    ['mine',mine(false)],['mine-active',mine(true)]
];

icons.forEach(([name,data]) => {
    const p = path.join(DIR, name+'.png');
    fs.writeFileSync(p, data);
    console.log('OK '+name+'.png ('+(data.length/1024).toFixed(1)+'KB)');
});
console.log('DONE - all 8 icons generated');
