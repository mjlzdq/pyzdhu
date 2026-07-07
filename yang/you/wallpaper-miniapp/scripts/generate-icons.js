/**
 * 生成小程序 Tab 图标 - 纯 Node.js 无依赖版本
 * 使用内置的最小有效 PNG 格式
 */
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const DIR = path.join(__dirname, '..', 'images', 'tab');
if (!fs.existsSync(DIR)) fs.mkdirSync(DIR, { recursive: true });

const SIZE = 81;

// 创建一个 RGBA 像素数组并编码为 PNG
function createIconPNG(drawFn) {
  const pixels = Buffer.alloc(SIZE * SIZE * 4, 0);
  drawFn(pixels, SIZE);
  
  // PNG 文件结构
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  
  // IHDR chunk
  const ihdr_data = Buffer.alloc(13);
  ihdr_data.writeUInt32BE(SIZE, 0);  // width
  ihdr_data.writeUInt32BE(SIZE, 4);  // height
  ihdr_data[8] = 8;   // bit depth
  ihdr_data[9] = 6;   // color type (RGBA)
  ihdr_data[10] = 0;  // compression
  ihdr_data[11] = 0;  // filter
  ihdr_data[12] = 0;  // interlace
  
  // IDAT: 每行前加 filter byte (0 = None)
  const rawData = Buffer.alloc(SIZE * (1 + SIZE * 4));
  for (let y = 0; y < SIZE; y++) {
    rawData[y * (1 + SIZE * 4)] = 0; // filter byte
    pixels.copy(rawData, y * (1 + SIZE * 4) + 1, y * SIZE * 4, (y + 1) * SIZE * 4);
  }
  const idat_data = zlib.deflateSync(rawData);
  
  function chunk(type, data) {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length, 0);
    const typeB = Buffer.from(type, 'ascii');
    const crcData = Buffer.concat([typeB, data]);
    const crc = Buffer.alloc(4);
    crc.writeUInt32BE(crc32(crcData), 0);
    return Buffer.concat([len, typeB, data, crc]);
  }
  
  return Buffer.concat([
    signature,
    chunk('IHDR', ihdr_data),
    chunk('IDAT', idat_data),
    chunk('IEND', Buffer.alloc(0))
  ]);
}

// CRC32 实现
function crc32(buf) {
  let table = [], crc = 0xFFFFFFFF;
  for (let i = 0; i < 256; i++) { let c = i; for (let j = 0; j < 8; j++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; table[i] = c; }
  for (let i = 0; i < buf.length; i++) crc = table[(crc ^ buf[i]) & 0xFF] ^ (crc >>> 8);
  return (crc ^ 0xFFFFFFFF) >>> 0;
}

// 设置像素 (x, y) 为 rgba 颜色
function setPixel(px, w, x, y, r, g, b, a = 255) {
  if (x < 0 || x >= w || y < 0 || y >= w) return;
  const idx = (y * w + x) * 4;
  px[idx] = r; px[idx + 1] = g; px[idx + 2] = b; px[idx + 3] = a;
}

// 画填充圆
function fillCircle(px, w, cx, cy, radius, r, g, b, a = 255) {
  for (let y = Math.max(0, Math.floor(cy - radius)); y <= Math.min(w - 1, Math.ceil(cy + radius)); y++) {
    for (let x = Math.max(0, Math.floor(cx - radius)); x <= Math.min(w - 1, Math.ceil(cx + radius)); x++) {
      if ((x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2) setPixel(px, w, x, y, r, g, b, a);
    }
  }
}

// 画线段 (Bresenham)
function drawLine(px, w, x0, y0, x1, y1, r, g, b, thickness = 6) {
  const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
  let err = dx - dy;
  while (true) {
    fillCircle(px, w, x0, y0, thickness / 2, r, g, b);
    if (x0 === x1 && y0 === y1) break;
    const e2 = 2 * err;
    if (e2 > -dy) { err -= dy; x0 += sx; }
    if (e2 < dx) { err += dx; y0 += sy; }
  }
}

// 画填充矩形
function fillRect(px, w, x, y, rw, rh, r, g, b, a = 255) {
  for (let py = Math.max(0, y); py < Math.min(w, y + rh); py++) {
    for (let px2 = Math.max(0, x); px2 < Math.min(w, x + rw); px2++) setPixel(px, w, px2, py, r, g, b, a);
  }
}

// 画填充三角形
function fillTriangle(px, w, x1, y1, x2, y2, x3, y3, r, g, b) {
  const minY = Math.max(0, Math.floor(Math.min(y1, y2, y3)));
  const maxY = Math.min(w - 1, Math.ceil(Math.max(y1, y2, y3)));
  for (let y = minY; y <= maxY; y++) {
    const intersections = [];
    [[x1, y1], [x2, y2], [x3, y3]].forEach(([px0, py0], i, arr) => {
      const [pxn, pyn] = arr[(i + 1) % 3];
      if ((py0 <= y && pyn > y) || (pyn <= y && py0 > y)) {
        const t = (y - py0) / (pyn - py0);
        intersections.push(Math.round(px0 + t * (pxn - px0)));
      }
    });
    if (intersections.length === 2) {
      const [xs, xe] = [Math.min(...intersections), Math.max(...intersections)];
      for (let x = Math.max(0, xs); x <= Math.min(w - 1, xe); x++) setPixel(px, w, x, y, r, g, b);
    }
  }
}

const C = Math.floor(SIZE / 2);

// ====== 图标绘制函数 ======

function drawHome(active) {
  const color = active ? [7, 193, 96] : [153, 153, 153]; // #07C160 or #999999
  return (px, w) => {
    // 房子主体三角形屋顶
    fillTriangle(px, w, C, 14, C - 28, 40, C + 28, 40, ...color);
    // 房子矩形主体
    fillRect(px, w, C - 28, 38, 56, 28, ...color);
    // 门（白色/透明）
    fillRect(px, w, C - 9, 48, 18, 18, 255, 255, 255);
    // 窗户左
    fillRect(px, w, C - 24, 44, 10, 10, 255, 255, 255);
    // 窗户右
    fillRect(px, w, C + 14, 44, 10, 10, 255, 255, 255);
  };
}

function drawCategory(active) {
  const color = active ? [7, 193, 96] : [153, 153, 153];
  return (px, w) => {
    const s = 17, gap = 5;
    // 四个方块
    fillRect(px, w, C - s - gap, C - s - gap, s, s, ...color);
    fillRect(px, w, C + gap, C - s - gap, s, s, ...color);
    fillRect(px, w, C - s - gap, C + gap, s, s, ...color);
    fillRect(px, w, C + gap, C + gap, s, s, ...color);
  };
}

function drawSearch(active) {
  const color = active ? [7, 193, 96] : [153, 153, 153];
  return (px, w) => {
    // 圆形镜片
    fillCircle(px, w, C - 4, C - 4, 20, ...color);
    // 内部镂空（白色）
    fillCircle(px, w, C - 4, C - 4, 13, 255, 255, 255);
    // 手柄
    const angle = Math.PI / 4;
    const handleStartX = C - 4 + Math.cos(angle) * 18;
    const handleStartY = C - 4 + Math.sin(angle) * 18;
    drawLine(px, w, Math.round(handleStartX), Math.round(handleStartY), C + 16, C + 16, ...color, 7);
  };
}

function drawMine(active) {
  const color = active ? [7, 193, 96] : [153, 153, 153];
  return (px, w) => {
    // 头
    fillCircle(px, w, C, 25, 15, ...color);
    // 身体半圆
    fillCircle(px, w, C, 58, 24, ...color);
    // 肩部以上白色区域（形成半圆形身体效果）
    for (let y = 0; y < 42; y++) {
      for (let x = 0; x < w; x++) {
        const dx = x - C, dy = y - 58;
        if (dx * dx + dy * dy < 24 * 24 && y < 42) {
          setPixel(px, w, x, y, 255, 255, 255, 0);
        }
      }
    }
  };
}

// ====== 生成所有图标 ======
console.log('🎨 正在生成 Tab 图标...\n');

const icons = [
  ['home', drawHome(false)],
  ['home-active', drawHome(true)],
  ['category', drawCategory(false)],
  ['category-active', drawCategory(true)],
  ['search', drawSearch(false)],
  ['search-active', drawSearch(true)],
  ['mine', drawMine(false)],
  ['mine-active', drawMine(true)]
];

icons.forEach(([name, drawFn]) => {
  const png = createIconPNG(drawFn);
  fs.writeFileSync(path.join(DIR, `${name}.png`), png);
  console.log(`  ✅ ${name}.png (${png.length} bytes)`);
});

console.log('\n🎉 全部完成！共生成 8 个 Tab 图标');
