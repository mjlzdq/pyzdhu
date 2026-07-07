/**
 * 羊了个羊风格 - 金字塔堆叠三消游戏引擎
 */
class GameEngine {
  constructor(config = {}) {
    this.cfg = Object.assign({
      layers: 5,
      maxSlot: 7,
      cardTypes: ['🐶','🐱','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯','🦁','🐮','🐷','🐸','🐵','🐔','🐧','🐦'],
      totalTypes: 10,
      cardsPerType: 3,
    }, config);

    this.slot = [];
    this.removedStack = [];
    this.score = 0;
    this.steps = 0;
    this.isGameOver = false;
    this.isWin = false;
    this.maxSlot = this.cfg.maxSlot;
    this.extraSlotCount = 0;
    this.tools = { revoke: 0, shuffle: 0, extraSlot: 0, hint: 0 };
    this.history = [];
    this.cards = [];
    this.cardW = 0;
    this.cardH = 0;
    this.boardWidth = 0;
    this.boardHeight = 0;

    this.generateCards();
    this.calcCardSize();
    this.calcPyramidPositions();
    this.syncTools();
  }

  syncTools() {
    const app = getApp();
    if (app && app.globalData && app.globalData.gameData && app.globalData.gameData.tools) {
      this.tools = { ...app.globalData.gameData.tools };
    }
  }

  generateCards() {
    const types = this.cfg.cardTypes;
    const totalTypes = Math.min(this.cfg.totalTypes, types.length);
    const shuffled = [...types].sort(() => Math.random() - 0.5);
    const selectedTypes = shuffled.slice(0, totalTypes);

    this.cards = [];
    let idCounter = 0;

    selectedTypes.forEach(type => {
      for (let i = 0; i < this.cfg.cardsPerType; i++) {
        this.cards.push({
          id: 'c' + (idCounter++),
          type: type,
          layer: 0,
          x: 0, y: 0,
          removed: false,
          blocked: false,
          selected: false,
          hint: false,
        });
      }
    });

    // 打乱卡片顺序
    for (let i = this.cards.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [this.cards[i], this.cards[j]] = [this.cards[j], this.cards[i]];
    }
  }

  calcCardSize() {
    const sysInfo = wx.getSystemInfoSync();
    this.boardWidth = sysInfo.windowWidth - 16;

    // 限制游戏区域高度（非 grid 模式的默认值，grid 模式会被 updateBoardSize 覆盖）
    this.boardHeight = Math.min(sysInfo.windowHeight * 0.5, 480);

    // 卡片大小：一行放 6 列
    const cols = 6;
    const gap = 5;   // 网格模式统一使用 gap=5
    const cardW = Math.floor((this.boardWidth - gap * (cols + 1)) / cols);
    this.cardW = cardW;
    this.cardH = Math.floor(cardW * 1.1);

    // 网格模式：根据卡片数量和实际 board 高度重新计算更优的卡片尺寸
    if (this.cfg.layoutMode === 'grid') {
      this._recalcGridCardSize();
    }
  }

  /**
   * 网格模式：根据卡片数量和可用高度，计算最优卡片尺寸让卡片适配游戏板
   */
  _recalcGridCardSize() {
    const totalCards = this.cards.length;
    if (totalCards <= 0) return;

    const cols = 6;
    const gap = 5;
    const rows = Math.ceil(totalCards / cols);

    // 用接近全部可用高度来计算（留出少量底部边距）
    const availableH = this.boardHeight - gap; // 减去一个gap作为上下边距
    // 根据行数直接反算最优卡片高度
    const optimalCardH = Math.floor((availableH - (rows - 1) * gap) / rows);

    if (optimalCardH > 0) {
      this.cardH = optimalCardH;
      this.cardW = Math.floor(this.cardH / 1.1);
      // 确保宽度不超过列宽限制
      const maxCardW = Math.floor((this.boardWidth - gap * (cols + 1)) / cols);
      if (this.cardW > maxCardW) {
        this.cardW = maxCardW;
        this.cardH = Math.floor(this.cardW * 1.1);
      }
      // 设置最小尺寸下限
      const minCardH = 38;
      if (this.cardH < minCardH) {
        this.cardH = minCardH;
        this.cardW = Math.floor(minCardH / 1.1);
      }
    }
  }

  calcPyramidPositions() {
    if (this.cfg.layoutMode === 'grid') {
      this.calcGridPositions();
      return;
    }

    const totalLayers = this.cfg.layers;
    const allCards = [...this.cards];
    const cols = 6;
    const gap = 3;

    // 每层卡片数：底层最多，顶层最少
    const cardsPerLayer = [];
    let remaining = allCards.length;
    const totalWeight = (totalLayers * (totalLayers + 1)) / 2;
    for (let l = 0; l < totalLayers; l++) {
      const weight = totalLayers - l;
      if (l === totalLayers - 1) {
        cardsPerLayer.push(remaining);
      } else {
        const count = Math.max(3, Math.round(allCards.length * weight / totalWeight));
        cardsPerLayer.push(count);
        remaining -= count;
      }
    }

    let cardIdx = 0;
    const rowH = this.cardH + gap;
    // 最大可用高度，留边距
    const maxHeight = this.boardHeight - this.cardH - gap * 2;

    for (let layer = 0; layer < totalLayers; layer++) {
      const count = cardsPerLayer[layer];
      const layerCols = Math.min(cols, count);
      const rows = Math.ceil(count / layerCols);

      // 该层居中
      const layerWidth = layerCols * (this.cardW + gap) + gap;
      const baseX = (this.boardWidth - layerWidth) / 2;
      // 层间偏移：减小偏移量，避免溢出
      const shiftX = layer * (this.cardW * 0.25);
      const shiftY = layer * (rowH * 0.25);

      // 生成该层所有网格位置
      const positions = [];
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < layerCols; c++) {
          if (positions.length < count) {
            let x = baseX + gap + c * (this.cardW + gap) + shiftX;
            let y = gap + r * rowH + shiftY;
            // 限制在可视区域内
            x = Math.max(gap, Math.min(x, this.boardWidth - this.cardW - gap));
            y = Math.max(gap, Math.min(y, maxHeight));
            positions.push({ x, y });
          }
        }
      }

      // 轻微随机抖动（±1px）
      const jittered = positions.map(p => ({
        x: p.x + (Math.random() - 0.5) * 2,
        y: p.y + (Math.random() - 0.5) * 2,
      }));

      for (let i = 0; i < count; i++) {
        const card = allCards[cardIdx + i];
        card.layer = layer;
        card.x = jittered[i].x;
        card.y = jittered[i].y;
      }
      cardIdx += count;
    }

    this.updateBlockedStatus();
  }

  /**
   * 网格对齐布局 — 用于所有模式
   * 卡片整齐排列成 N列 x M行 网格
   * 注意：网格模式所有卡片在同一层（layer=0），不产生遮挡
   */
  calcGridPositions() {
    const allCards = [...this.cards];
    const cols = 6;
    const gap = 5;

    let cardW = this.cardW;
    let cardH = this.cardH;

    const rows = Math.ceil(allCards.length / cols);

    // 水平居中
    const gridWidth = cols * (cardW + gap) - gap;
    const baseX = Math.max(gap, (this.boardWidth - gridWidth) / 2);

    // 垂直方向：从顶部开始排列，留少量上边距
    const baseY = gap;
    const gridHeight = rows * (cardH + gap) - gap;

    // 网格模式：所有卡片在同一层，不产生遮挡（这是关键！）
    for (let i = 0; i < allCards.length; i++) {
      const row = Math.floor(i / cols);
      const col = i % cols;

      allCards[i].layer = 0;
      allCards[i].x = baseX + col * (cardW + gap);
      allCards[i].y = baseY + row * (cardH + gap);
    }

    this.updateBlockedStatus();
  }

  updateBlockedStatus() {
    this.cards.forEach(card => {
      if (card.removed) {
        card.blocked = true;
        return;
      }
      // 只有被上层卡片覆盖才 blocked
      card.blocked = this.cards.some(other =>
        !other.removed && other.layer > card.layer && this.isOverlapping(card, other)
      );
    });
  }

  /**
   * 用实际的 board 尺寸更新卡片位置（用于页面渲染后重新布局）
   */
  updateBoardSize(width, height) {
    this.boardWidth = width;
    this.boardHeight = height;
    // 重新计算卡片大小
    const cols = 6;
    const gap = 5;   // 网格模式统一使用 gap=5
    const cardW = Math.floor((this.boardWidth - gap * (cols + 1)) / cols);
    this.cardW = cardW;
    this.cardH = Math.floor(cardW * 1.1);

    // 网格模式：根据实际高度优化卡片尺寸
    if (this.cfg.layoutMode === 'grid') {
      this._recalcGridCardSize();
    }

    // 重新计算所有卡片位置
    this.calcPyramidPositions();
  }

  isOverlapping(a, b) {
    const ax1 = a.x, ay1 = a.y;
    const ax2 = a.x + this.cardW, ay2 = a.y + this.cardH;
    const bx1 = b.x, by1 = b.y;
    const bx2 = b.x + this.cardW, by2 = b.y + this.cardH;

    const ox = Math.min(ax2, bx2) - Math.max(ax1, bx1);
    const oy = Math.min(ay2, by2) - Math.max(ay1, by1);
    if (ox <= 0 || oy <= 0) return false;

    const overlapArea = ox * oy;
    const cardArea = this.cardW * this.cardH;
    // 覆盖 35% 以上才算遮挡
    return overlapArea > cardArea * 0.35;
  }

  selectCard(cardId) {
    if (this.isGameOver || this.isWin) return { success: false, reason: '游戏已结束' };

    const card = this.cards.find(c => c.id === cardId);
    if (!card || card.removed) {
      console.warn('[Engine] selectCard 卡片不存在或已移除, cardId:', cardId, 'total cards:', this.cards.length);
      return { success: false, reason: '卡片不存在' };
    }
    if (card.blocked) return { success: false, reason: '卡片被遮挡' };

    const totalSlots = this.maxSlot + this.extraSlotCount;
    if (this.slot.length >= totalSlots) {
      this.isGameOver = true;
      return { success: false, reason: '槽位已满' };
    }

    this.history.push({
      card: { ...card },
      slot: [...this.slot],
    });

    card.removed = true;
    this.removedStack.push({ type: card.type, id: card.id });
    this.slot.push({ type: card.type, sourceId: card.id });
    this.steps++;
    this.updateBlockedStatus();

    const matchResult = this.checkMatch();

    const remaining = this.cards.filter(c => !c.removed);
    if (remaining.length === 0 && this.slot.length === 0) {
      this.isWin = true;
      this.score += 100;
    }

    return { success: true, matchResult };
  }

  checkMatch() {
    let matched = false;
    let matchCount = 0;

    // 只要槽位中有 3 个相同类型就消除（不需要相邻）
    while (true) {
      let found = false;
      const counts = {};
      this.slot.forEach((s, idx) => {
        if (!counts[s.type]) counts[s.type] = [];
        counts[s.type].push(idx);
      });

      for (const type in counts) {
        if (counts[type].length >= 3) {
          // 消除该类型的 3 张卡片（取前3张）
          const indices = counts[type].sort((a, b) => b - a).slice(0, 3);
          indices.forEach(idx => this.slot.splice(idx, 1));
          this.score += 10;
          matched = true;
          matchCount++;
          found = true;
          break;
        }
      }
      if (!found) break;
    }

    return { matched, matchCount };
  }

  checkGameStatus() {
    if (this.isWin) return 'win';
    const totalSlots = this.maxSlot + this.extraSlotCount;
    if (this.slot.length >= totalSlots) {
      this.isGameOver = true;
      return 'gameover';
    }
    const available = this.cards.filter(c => !c.removed && !c.blocked);
    if (available.length === 0 && this.slot.length > 0) {
      this.isGameOver = true;
      return 'gameover';
    }
    return 'playing';
  }

  revoke() {
    if (this.history.length === 0) return false;
    const last = this.history.pop();
    const card = this.cards.find(c => c.id === last.card.id);
    if (card) {
      card.removed = false;
    }
    this.slot = last.slot;
    this.removedStack.pop();
    this.updateBlockedStatus();
    return true;
  }

  shuffle() {
    const activeCards = this.cards.filter(c => !c.removed);
    const positions = activeCards.map(c => ({ x: c.x, y: c.y }));
    for (let i = positions.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [positions[i], positions[j]] = [positions[j], positions[i]];
    }
    activeCards.forEach((card, idx) => {
      card.x = positions[idx].x;
      card.y = positions[idx].y;
    });
    this.updateBlockedStatus();
    return true;
  }

  addExtraSlot() {
    this.extraSlotCount++;
    return true;
  }

  showHint() {
    const slotCounts = {};
    this.slot.forEach(s => {
      slotCounts[s.type] = (slotCounts[s.type] || 0) + 1;
    });

    let hintCards = [];
    for (const type in slotCounts) {
      if (slotCounts[type] >= 2) {
        const available = this.cards.find(c => !c.removed && !c.blocked && c.type === type);
        if (available) { hintCards.push(available); break; }
      }
    }

    if (hintCards.length === 0) {
      const typeCounts = {};
      this.cards.forEach(c => {
        if (!c.removed && !c.blocked) {
          typeCounts[c.type] = (typeCounts[c.type] || 0) + 1;
        }
      });
      for (const type in typeCounts) {
        if (typeCounts[type] >= 2) {
          hintCards = this.cards.filter(c => !c.removed && !c.blocked && c.type === type).slice(0, 2);
          break;
        }
      }
    }

    if (hintCards.length > 0) {
      hintCards.forEach(c => { c.hint = true; });
      return true;
    }
    return false;
  }

  clearHints() {
    this.cards.forEach(c => { c.hint = false; });
  }

  getState() {
    return {
      cards: this.cards,
      slot: this.slot,
      removedStack: [...this.removedStack],
      score: this.score,
      steps: this.steps,
      isGameOver: this.isGameOver,
      isWin: this.isWin,
      maxSlot: this.maxSlot,
      extraSlotCount: this.extraSlotCount,
      tools: { ...this.tools },
      cardW: this.cardW,
      cardH: this.cardH,
    };
  }
}

module.exports = GameEngine;
