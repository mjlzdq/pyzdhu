// pages/index/index.js
const app = getApp();
const adHelper = require('../../utils/ad-helper');
const audioManager = require('../../utils/audio-manager');

Page({
  data: {
    gameData: {},
    showNewPlayerGift: false,
    signData: { canSign: false, signedToday: false },
    points: 0,
    showRanking: false,
    showGiftPanel: false,
    showSettings: false,
    // 积分不足弹窗
    showNoPointsModal: false,
    noPointsData: { modeName: '', cost: 0, current: 0, mode: '' },
    // 原生模板广告
    adReady: false,
    // 用户头像
    avatarUrl: '',
  },

  onLoad(options) {
    // 读取本地存储的头像
    const savedAvatar = wx.getStorageSync('userAvatarUrl');
    if (savedAvatar) {
      this.setData({ avatarUrl: savedAvatar });
    }

    this.loadData();
    this.checkNewPlayerGift();
    this.checkDailySign();

    // 处理邀请逻辑
    const inviterId = options.inviter || '';
    if (inviterId) {
      this.processInvitation(inviterId);
    }
  },

  /**
   * 处理邀请：被邀请者通过分享链接进入
   * 只有新用户（首次进入）才有效
   */
  processInvitation(inviterId) {
    const result = app.handleInvitation(inviterId);
    if (!result.success) {
      // 邀请无效（非新用户/已受邀/自己邀请自己），静默处理
      return;
    }

    // 邀请成功：给邀请人加积分（通过云端或本地）
    this.awardInviter(inviterId, result.bonus);
  },

  /**
   * 给邀请人发放积分奖励
   */
  awardInviter(inviterId, bonus) {
    // 方案1：通过云函数给邀请人加积分
    if (wx.cloud) {
      wx.cloud.callFunction({
        name: 'awardInviteBonus',
        data: { inviterId, bonus },
      }).catch(() => {
        // 云函数调用失败，使用本地存储方案作为备选
        this.awardInviterLocal(inviterId, bonus);
      });
    } else {
      this.awardInviterLocal(inviterId, bonus);
    }
  },

  /**
   * 本地备用：将奖励暂存，等邀请人下次启动时检查领取
   */
  awardInviterLocal(inviterId, bonus) {
    const pending = wx.getStorageSync('pendingInviteRewards') || [];
    pending.push({ inviterId, bonus, time: Date.now() });
    wx.setStorageSync('pendingInviteRewards', pending);
  },

  onReady() {
    // 原生模板广告通过 WXML <ad-custom> 组件渲染，无需 JS 创建
  },

  onShow() {
    this.loadData();
    this.checkDailySign();
    this.fetchCloudRankings();
  },

  onUnload() {
    // 原生模板广告由框架自动管理，无需手动销毁
  },

  loadData() {
    const gd = app.globalData.gameData;
    this.setData({
      gameData: gd,
      points: app.getPoints(),
    });
  },

  // ===================== 用户头像 =====================

  /**
   * 用户点击头像区域选择微信头像
   * 使用 button open-type="chooseAvatar" 获取，微信官方推荐方式
   * 上传到云存储获取永久链接
   */
  onChooseAvatar(e) {
    const avatarUrl = e.detail.avatarUrl;
    if (!avatarUrl) return;

    // 先显示临时头像
    this.setData({ avatarUrl });
    wx.setStorageSync('userAvatarUrl', avatarUrl);

    // 上传到云存储获取永久链接
    if (wx.cloud) {
      const cloudPath = 'avatars/' + app.globalData.gameData.userId + '_' + Date.now() + '.png';
      wx.cloud.uploadFile({
        cloudPath: cloudPath,
        filePath: avatarUrl,
      }).then(res => {
        // 获取永久链接
        return wx.cloud.getTempFileURL({
          fileList: [res.fileID],
        });
      }).then(res => {
        if (res.fileList && res.fileList[0] && res.fileList[0].tempFileURL) {
          const permanentUrl = res.fileList[0].tempFileURL;
          this.setData({ avatarUrl: permanentUrl });
          wx.setStorageSync('userAvatarUrl', permanentUrl);
        }
      }).catch(err => {
        console.error('头像上传云存储失败:', err);
        // 上传失败也不影响使用，只是头像链接是临时的
      });
    }
  },

  // ===================== 新人礼包（无需广告，直接领取） =====================

  checkNewPlayerGift() {
    const gd = app.globalData.gameData;
    if (gd.isNewPlayer) {
      this.setData({ showNewPlayerGift: true });
    }
  },

  /**
   * 领取新人礼包
   * 仅限新人，直接领取，无需广告
   */
  claimGift() {
    this.setData({ showNewPlayerGift: false });

    const result = app.claimNewPlayerGift();
    if (result.success) {
      this.loadData();
      wx.showToast({ title: '🎉 每种道具 +3！', icon: 'none', duration: 2000 });
    }
  },

  /**
   * 跳过新人礼包（放弃领取）
   */
  skipGift() {
    const gd = app.globalData.gameData;
    gd.isNewPlayer = false;
    app.saveGameData();
    this.setData({ showNewPlayerGift: false });
  },

  // ===================== 每日签到 =====================

  checkDailySign() {
    const signData = app.checkDailySign();
    this.setData({ signData });
  },

  /**
   * 直接领取签到奖励（不看广告）：+20 积分
   */
  onDailySignBasic() {
    console.log('[签到] 点击直接领取');
    const signData = app.checkDailySign();
    console.log('[签到] 状态:', JSON.stringify(signData));
    if (signData.signedToday) {
      wx.showToast({ title: '今日已签到，明天再来~', icon: 'none' });
      return;
    }

    const result = app.dailySignBasic();
    console.log('[签到] 结果:', JSON.stringify(result));
    if (result.success) {
      this.loadData();
      this.checkDailySign();
      wx.showToast({ title: '✅ 签到成功！+20 积分', icon: 'none', duration: 2000 });
    }
  },

  /**
   * 看广告签到：看完广告后领取
   * - 如果没领过直接奖励：40 积分 + 4 种道具
   * - 如果已领过直接奖励：补 20 积分 + 4 种道具
   */
  onDailySignAd() {
    console.log('[签到] 点击看广告签到');
    const signData = app.checkDailySign();
    console.log('[签到] 状态:', JSON.stringify(signData));
    if (!signData.canWatchAd) {
      wx.showToast({ title: '今日已通过广告签到', icon: 'none' });
      return;
    }

    const isUpgrade = signData.signedToday && !signData.signAdWatched;
    const adHelper = require('../../utils/ad-helper');
    adHelper.showRewardedVideo({
      onRewarded: () => {
        const result = app.dailySignAd();
        if (result.success) {
          this.loadData();
          this.checkDailySign();
          if (result.isUpgrade) {
            wx.showToast({ title: '✅ 补签成功！+20积分 + 道具', icon: 'none', duration: 2000 });
          } else {
            wx.showToast({ title: '✅ 签到成功！+40积分 + 道具', icon: 'none', duration: 2000 });
          }
        }
      },
      onError: () => {
        wx.showToast({ title: '广告加载失败，请稍后再试', icon: 'none' });
      },
    });
  },

  // ===================== 排行 =====================

  /**
   * 获取云端排行榜（60 秒节流，避免频繁请求消耗配额）
   */
  fetchCloudRankings() {
    const now = Date.now();
    if (this._lastRankFetch && now - this._lastRankFetch < 60000) {
      return; // 60 秒内不重复请求
    }
    this._lastRankFetch = now;

    if (!wx.cloud) return;
    const db = wx.cloud.database();
    db.collection('rankings')
      .orderBy('maxLevel', 'desc')
      .limit(10)
      .get()
      .then(res => {
        const gd = app.globalData.gameData;
        const rankings = res.data.map(item => ({
          name: item.name,
          maxLevel: item.maxLevel,
          isSelf: item.name === gd.playerName,
        }));
        const selfInList = rankings.find(r => r.isSelf);
        if (!selfInList && gd.challengeMaxLevel > 0) {
          rankings.push({
            name: gd.playerName,
            maxLevel: gd.challengeMaxLevel,
            isSelf: true,
          });
          rankings.sort((a, b) => b.maxLevel - a.maxLevel);
          if (rankings.length > 10) rankings.pop();
        }
        gd.rankings = rankings;
        app.saveGameData();
        this.setData({ gameData: gd });
      })
      .catch(() => {});
  },

  // ===================== 开始游戏 =====================

  startEasy() {
    const points = app.getPoints();
    if (points < 5) {
      this.showNoPointsModal('easy');
      return;
    }
    app.usePoints(5);
    this.loadData();
    wx.navigateTo({ url: '/pages/game/game?mode=easy' });
  },

  startNormal() {
    if (!app.globalData.gameData.normalUnlocked) {
      wx.showToast({ title: '请先在简单模式通关10次', icon: 'none' });
      return;
    }
    wx.navigateTo({ url: '/pages/game/game?mode=normal' });
  },

  startNightmare() {
    const points = app.getPoints();
    if (points < 15) {
      this.showNoPointsModal('nightmare');
      return;
    }
    app.usePoints(15);
    this.loadData();
    wx.navigateTo({ url: '/pages/game/game?mode=nightmare' });
  },

  startChallenge() {
    const points = app.getPoints();
    if (points < 10) {
      this.showNoPointsModal('challenge');
      return;
    }
    app.usePoints(10);
    this.loadData();
    wx.navigateTo({ url: '/pages/game/game?mode=challenge&level=1' });
  },

  // ===================== 积分系统 =====================

  /**
   * 看广告获取积分
   */
  earnPoints() {
    adHelper.showRewardedVideo({
      onRewarded: () => {
        const newTotal = app.addPoints(10);
        this.setData({ points: newTotal });
        wx.showToast({ title: '✅ +10 积分！', icon: 'none', duration: 2000 });
      },
      onSkipped: () => wx.showToast({ title: '需要看完广告才能获得积分哦~', icon: 'none' }),
      onError: () => wx.showToast({ title: '广告加载失败，请稍后再试', icon: 'none' }),
    });
  },

  /**
   * 积分不足弹窗（自定义弹窗）
   */
  showNoPointsModal(mode) {
    const costs = { easy: 5, normal: 10, nightmare: 15, challenge: 10 };
    const names = { easy: '简单模式', normal: '普通模式', nightmare: '噩梦试炼', challenge: '闯关模式' };
    const cost = costs[mode] || 10;
    const name = names[mode] || mode;
    const points = app.getPoints();

    this.setData({
      showNoPointsModal: true,
      noPointsData: { modeName: name, cost, current: points, mode },
    });
  },

  closeNoPointsModal() {
    this.setData({ showNoPointsModal: false });
  },

  watchAdForPoints() {
    this.setData({ showNoPointsModal: false });
    this.earnPoints();
  },

  // ===================== 原生模板广告事件 =====================

  adLoad() {
    console.log('原生模板广告加载成功');
    this.setData({ adReady: true });
  },

  adError(err) {
    console.error('原生模板广告加载失败', err);
    this.setData({ adReady: false });
  },

  adClose() {
    console.log('原生模板广告关闭');
    this.setData({ adReady: false });
  },

  // ===================== 排行榜面板 =====================

  openRanking() {
    this.setData({ showRanking: true });
    this.fetchCloudRankings();
  },

  closeRanking() {
    this.setData({ showRanking: false });
  },

  // ===================== 礼包面板 =====================

  openGiftPanel() {
    this.setData({ showGiftPanel: true });
  },

  closeGiftPanel() {
    this.setData({ showGiftPanel: false });
  },

  // ===================== 设置面板 =====================

  openSettings() {
    this.setData({ showSettings: true });
  },

  closeSettings() {
    this.setData({ showSettings: false });
  },

  toggleMusic(e) {
    const on = e.detail.value;
    audioManager.toggleMusic(on);
    this.setData({ gameData: app.globalData.gameData });
  },

  toggleSound(e) {
    const on = e.detail.value;
    audioManager.toggleSound(on);
    this.setData({ gameData: app.globalData.gameData });
  },

  copyUserId() {
    const userId = app.globalData.gameData.userId || '';
    wx.setClipboardData({
      data: userId,
      success: () => wx.showToast({ title: '用户ID已复制', icon: 'success' }),
    });
  },

  noop() {},

  onShareAppMessage() {
    // 带上邀请人 userId，被邀请者进入后处理
    const inviterId = app.globalData.gameData.userId;
    return {
      title: '合就完了 - 来挑战我吧！',
      path: '/pages/index/index?inviter=' + inviterId,
    };
  },
});
