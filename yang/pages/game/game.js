// pages/game/game.js
const app = getApp();
const GameEngine = require('../../utils/game-engine');
const adHelper = require('../../utils/ad-helper');
const audioManager = require('../../utils/audio-manager');

Page({
  data: {
    // 卡片数据
    cards: [],
    slot: [],
    score: 0,
    steps: 0,
    isGameOver: false,
    isWin: false,
    showModal: false,
    maxSlot: 7,
    extraSlotCount: 0,
    // 道具数量（页面级，从全局同步）
    tools: { revoke: 0, shuffle: 0, extraSlot: 0, hint: 0 },
    // 卡片尺寸（WXML 内联样式使用）
    cardW: 0,
    cardH: 0,
    // 广告弹窗
    showAdModal: false,
    adToolType: '',
    adToolName: '',
    // Toast
    toastMsg: '',
    // 模式
    mode: 'easy',
    challengeLevel: 1,
    // Banner 广告
    adReady: false,
    // 防止快速点击旧 DOM（通过 engine.cards.find 校验）
  },

  onLoad(options) {
    const mode = options.mode || 'easy';
    const level = parseInt(options.level) || 1;
    this.setData({ mode, challengeLevel: level });

    // 先创建引擎（使用默认高度），等获取到实际高度后再重新计算位置
    const cfg = this.getModeConfig(mode, level);
    this.engine = new GameEngine(cfg);
    this.syncState();

    // 获取 game-board 实际高度，重新计算卡片位置
    this._queryBoardSize();
  },

  _queryBoardSize() {
    wx.createSelectorQuery().select('.game-board').boundingClientRect(rect => {
      if (rect && rect.height > 0) {
        // 用实际高度更新引擎
        this.engine.updateBoardSize(rect.width, rect.height);
        this.syncState();
      }
    }).exec();
  },

  onReady() {
    // Banner 广告通过 WXML <ad> 组件渲染，无需 JS 创建
  },

  onUnload() {
    if (this._toastTimer) clearTimeout(this._toastTimer);
  },

  getModeConfig(mode, level) {
    const configs = {
      easy: { layers: 3, maxSlot: 7, totalTypes: 8, cardsPerType: 3, layoutMode: 'grid' },
      normal: { layers: 4, maxSlot: 7, totalTypes: 12, cardsPerType: 3, layoutMode: 'grid' },
      nightmare: { layers: 5, maxSlot: 7, totalTypes: 16, cardsPerType: 3, layoutMode: 'grid' },
      challenge: { layers: level, maxSlot: 7, totalTypes: 8 + level * 2, cardsPerType: 3, layoutMode: 'grid' },
    };
    return configs[mode] || configs.easy;
  },

  syncState() {
    const state = this.engine.getState();
    this.setData({
      cards: state.cards,
      slot: state.slot,
      score: state.score,
      steps: state.steps,
      isGameOver: state.isGameOver,
      isWin: state.isWin,
      showModal: state.isGameOver || state.isWin,
      maxSlot: state.maxSlot,
      extraSlotCount: state.extraSlotCount,
      tools: { ...app.globalData.gameData.tools },
      cardW: state.cardW,
      cardH: state.cardH,
    });

    if ((state.isGameOver || state.isWin) && !this._gameEndHandled) {
      this._gameEndHandled = true;
      this.handleGameEnd(state.isWin, state.score);
    }
  },

  // ===================== 点击卡片 =====================
  onCardTap(e) {
    if (this.data.isGameOver || this.data.isWin) return;
    const cardId = e.currentTarget.dataset.id;

    // 检查卡片是否属于当前引擎（防止点击旧 DOM）
    const card = this.engine.cards.find(c => c.id === cardId);
    if (!card) {
      console.warn('[游戏页] 卡片不存在，可能点击了旧 DOM，已忽略');
      return;
    }

    const result = this.engine.selectCard(cardId);
    audioManager.playSfx('click');
    if (!result.success) {
      // 先同步状态（可能触发了游戏结束）
      this.syncState();
      if (!this.data.isGameOver) {
        this.showToast(result.reason || '操作无效');
      } else {
        audioManager.playSfx('lose');
      }
      return;
    }
    // 匹配成功播放音效
    if (result.matchResult && result.matchResult.matched) {
      audioManager.playSfx('match');
    }
    this.syncState();
  },

  // ===================== 道具系统 =====================

  /**
   * 使用道具
   * 道具足够 → 直接使用
   * 道具不足 → 弹出确认框，看广告获取
   */
  useTool(e) {
    const type = e.currentTarget.dataset.type;
    const gd = app.globalData.gameData;
    if (gd.tools[type] > 0) {
      // 先执行道具效果，成功后再扣减
      const result = this.executeTool(type);
      if (result) {
        app.useTool(type);
        this.syncState();
        this.showToast(this.getToolUseMsg(type));
      }
    } else {
      // 道具不足，提示看广告
      const names = { revoke: '撤回', shuffle: '洗牌', extraSlot: '加槽', hint: '提示' };
      this.setData({
        showAdModal: true,
        adToolType: type,
        adToolName: names[type] || type,
      });
    }
  },

  /**
   * 看广告获取道具并立即使用
   */
  watchAdGetTool() {
    this.setData({ showAdModal: false });
    const toolType = this.data.adToolType;
    const toolName = this.data.adToolName;

    adHelper.showRewardedVideo({
      onRewarded: () => {
        this.grantToolReward(toolType, toolName);
      },
      onSkipped: () => wx.showToast({ title: '需要看完广告才能获得道具哦~', icon: 'none' }),
      onError: () => wx.showToast({ title: '广告加载失败，请稍后再试', icon: 'none' }),
    });
  },

  /**
   * 广告看完 → 发道具 + 自动使用
   */
  grantToolReward(type, name) {
    // 先执行道具效果，成功后再增加道具数量
    const result = this.executeTool(type);
    if (result) {
      app.addTools(type);
      this.syncState();
      this.showToast('✅ ' + name + '使用成功');
    }
  },

  /**
   * 关闭广告弹窗（放弃看广告）
   */
  closeAdModal() {
    this.setData({ showAdModal: false });
  },

  /**
   * 执行道具效果
   */
  executeTool(type) {
    const result = (() => {
      switch (type) {
        case 'revoke': return this.engine.revoke();
        case 'shuffle': return this.engine.shuffle();
        case 'extraSlot': return this.engine.addExtraSlot();
        case 'hint': return this.engine.showHint();
        default: return false;
      }
    })();
    if (result) {
      audioManager.playSfx('tool');
    }
    return result;
  },

  getToolUseMsg(type) {
    const msgs = { revoke: '↩️ 已撤回', shuffle: '🔀 已洗牌', extraSlot: '➕ 槽位+1', hint: '💡 已提示' };
    return msgs[type] || '';
  },

  // ===================== 道具 + 按钮（直接看广告获取） =====================

  getToolByAd(e) {
    const type = e.currentTarget.dataset.tool;
    const names = { revoke: '撤回', shuffle: '洗牌', extraSlot: '加槽', hint: '提示' };
    this.setData({
      showAdModal: true,
      adToolType: type,
      adToolName: names[type] || type,
    });
  },

  // ===================== 游戏结束处理 =====================

  handleGameEnd(isWin, score) {
    // 播放结果音效
    if (isWin) {
      audioManager.playSfx('win');
    } else {
      audioManager.playSfx('lose');
    }

    const gd = app.globalData.gameData;
    const mode = this.data.mode;

    gd.totalGames++;
    if (isWin) {
      gd.totalWins++;
      if (score > gd.highScore) gd.highScore = score;

      if (mode === 'easy') gd.easyWins++;
      else if (mode === 'normal') gd.normalWins++;
      else if (mode === 'nightmare') gd.nightmareWins++;
      else if (mode === 'challenge') {
        const level = this.data.challengeLevel;
        if (level > gd.challengeMaxLevel) {
          gd.challengeMaxLevel = level;
          gd.challengeMaxClearCount = 1;
        } else if (level === gd.challengeMaxLevel) {
          gd.challengeMaxClearCount++;
        }
        // 闯关模式通关奖励 5 积分
        app.addPoints(5);
      }

      // 解锁条件
      if (gd.easyWins >= 10) gd.normalUnlocked = true;
    }

    app.saveGameData();

    // 闯关模式上传成绩到云端排行榜
    if (mode === 'challenge' && isWin && wx.cloud) {
      this.uploadChallengeRank(gd.playerName, gd.challengeMaxLevel);
    }
  },

  /**
   * 上传闯关成绩到云端排行榜
   */
  uploadChallengeRank(name, maxLevel) {
    wx.cloud.callFunction({
      name: 'uploadRank',
      data: { name, maxLevel },
    }).then(res => {
      if (res.result && res.result.success) {
        // 同步最新排行到本地
        const gd = app.globalData.gameData;
        gd.rankings = res.result.rankings.map(item => ({
          name: item.name,
          maxLevel: item.maxLevel,
          isSelf: item.name === gd.playerName,
        }));
        const selfInList = gd.rankings.find(r => r.isSelf);
        if (!selfInList && maxLevel > 0) {
          gd.rankings.push({ name, maxLevel, isSelf: true });
          gd.rankings.sort((a, b) => b.maxLevel - a.maxLevel);
          if (gd.rankings.length > 10) gd.rankings.pop();
        }
        app.saveGameData();
      }
    }).catch(() => {});
  },

  // ===================== 重新开始 =====================
  restart() {
    this._gameEndHandled = false;
    // 先清空旧卡片数据，防止点击旧 DOM
    this.setData({ cards: [], slot: [], isGameOver: false, isWin: false, showModal: false });
    const cfg = this.getModeConfig(this.data.mode, this.data.challengeLevel);
    this.engine = new GameEngine(cfg);
    this.syncState();
  },

  // ===================== 返回首页 =====================
  goHome() {
    // 展示插屏广告，关闭后返回首页
    adHelper.showInterstitialAd(() => {
      wx.navigateBack();
    });
  },

  // ===================== 下一关（闯关模式） =====================
  nextLevel() {
    // 每闯一关消耗 10 积分
    const points = app.getPoints();
    if (points < 10) {
      wx.showToast({ title: '积分不足，需要 10 积分', icon: 'none' });
      return;
    }
    app.usePoints(10);
    this._gameEndHandled = false;
    const nextLevel = this.data.challengeLevel + 1;
    // 先清空旧卡片数据，防止点击旧 DOM
    this.setData({ cards: [], slot: [], isGameOver: false, isWin: false, showModal: false });
    const cfg = this.getModeConfig('challenge', nextLevel);
    this.engine = new GameEngine(cfg);
    this.setData({ challengeLevel: nextLevel });
    this.syncState();
  },

  // ===================== Toast =====================
  showToast(msg) {
    this.setData({ toastMsg: msg });
    if (this._toastTimer) clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => {
      this.setData({ toastMsg: '' });
    }, 1500);
  },

  noop() {},

  // ===================== Banner 广告 =====================
  adLoad() {
    console.log('[游戏页] Banner 广告加载成功');
    this.setData({ adReady: true });
  },
  adError(err) {
    console.error('[游戏页] Banner 广告加载失败', err);
    this.setData({ adReady: false });
  },
  adClose() {
    console.log('[游戏页] Banner 广告关闭');
    this.setData({ adReady: false });
  },

  onShareAppMessage() {
    const inviterId = app.globalData.gameData.userId;
    return {
      title: '合就完了 - 来挑战我吧！',
      path: '/pages/index/index?inviter=' + inviterId,
    };
  },
});
