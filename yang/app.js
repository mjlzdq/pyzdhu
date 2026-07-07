const audioManager = require('./utils/audio-manager');

App({
  onLaunch() {
    // 初始化云开发
    if (wx.cloud) {
      wx.cloud.init({
        env: 'cloud1-5g6d4pz0c8677075',
        traceUser: true,
      });
    }

    this.initGameData();
    this.syncCloudRankings();
    this.checkPendingInviteRewards();
    // 初始化背景音乐
    audioManager.initBgm();
  },

  /**
   * 获取音频管理器（供页面使用）
   */
  getAudioManager() {
    return audioManager;
  },

  initGameData() {
    const saved = wx.getStorageSync('hejiuGameData');
    if (saved) {
      this.globalData.gameData = saved;
      // 兼容旧数据：如果没有道具字段，补充默认值
      if (!this.globalData.gameData.tools) {
        this.globalData.gameData.tools = { revoke: 0, shuffle: 0, extraSlot: 0, hint: 0 };
      }
      if (!this.globalData.gameData.isNewPlayer) {
        this.globalData.gameData.isNewPlayer = false;
      }
      if (!this.globalData.gameData.lastSignDate) {
        this.globalData.gameData.lastSignDate = '';
      }
      if (this.globalData.gameData.settings === undefined) {
        this.globalData.gameData.settings = { musicOn: true, soundOn: true };
      }
      if (!this.globalData.gameData.userId) {
        this.globalData.gameData.userId = 'U' + Math.floor(Math.random() * 900000 + 100000);
      }
    } else {
      // 全新玩家：新人礼包每种道具 +3
      this.globalData.gameData = {
        highScore: 0,
        totalGames: 0,
        totalWins: 0,
        easyWins: 0,
        normalWins: 0,
        nightmareWins: 0,
        normalUnlocked: false,
        nightmareUnlocked: false,
        challengeMaxLevel: 0,
        challengeMaxClearCount: 0,
        playerName: '玩家' + Math.floor(Math.random() * 9000 + 1000),
        // 道具系统：持久化累计
        tools: { revoke: 0, shuffle: 0, extraSlot: 0, hint: 0 },
        // 新人标识
        isNewPlayer: true,
        // 每日签到日期 + 签到类型
        lastSignDate: '',
        signAdWatched: false,  // 是否已通过看广告签到
        rankings: [],
        // 积分系统
        points: 0,
        // 设置
        settings: { musicOn: true, soundOn: true },
        // 用户ID
        userId: 'U' + Math.floor(Math.random() * 900000 + 100000),
      };
      this.saveGameData();
    }
    // 首页先用本地数据渲染，云端排行异步更新
    if (!this.globalData.gameData.rankings) {
      this.globalData.gameData.rankings = [];
    }
    if (this.globalData.gameData.points === undefined) {
      this.globalData.gameData.points = 0;
    }
  },

  saveGameData() {
    try {
      wx.setStorageSync('hejiuGameData', this.globalData.gameData);
    } catch (e) {}
  },

  /**
   * 使用道具（减少1个）
   */
  useTool(type) {
    const gd = this.globalData.gameData;
    if (!gd.tools) gd.tools = { revoke: 0, shuffle: 0, extraSlot: 0, hint: 0 };
    if (gd.tools[type] <= 0) return false;
    gd.tools[type]--;
    this.saveGameData();
    return true;
  },

  /**
   * 增加道具（看广告后调用）
   */
  addTools(reward) {
    const gd = this.globalData.gameData;
    if (!gd.tools) gd.tools = { revoke: 0, shuffle: 0, extraSlot: 0, hint: 0 };
    // reward 格式: { revoke: 1, shuffle: 2 } 或直接传类型字符串
    if (typeof reward === 'string') {
      gd.tools[reward] = (gd.tools[reward] || 0) + 1;
    } else {
      for (const key in reward) {
        gd.tools[key] = (gd.tools[key] || 0) + reward[key];
      }
    }
    this.saveGameData();
    return { ...gd.tools };
  },

  /**
   * 领取新人礼包
   */
  claimNewPlayerGift() {
    const gd = this.globalData.gameData;
    if (!gd.isNewPlayer) return { success: false, reason: '已领取过' };
    // 每种道具 +3
    gd.tools.revoke += 3;
    gd.tools.shuffle += 3;
    gd.tools.extraSlot += 3;
    gd.tools.hint += 3;
    gd.isNewPlayer = false;
    this.saveGameData();
    return {
      success: true,
      tools: { ...gd.tools },
      reward: { revoke: 3, shuffle: 3, extraSlot: 3, hint: 3 },
    };
  },

  /**
   * 检查每日签到状态
   * 返回: { canSign: boolean, signedToday: boolean, signAdWatched: boolean, canWatchAd: boolean }
   * - canSign: 今天还可以直接领取（没领过）
   * - signedToday: 今天已签到过（领过直接奖励或看过广告）
   * - signAdWatched: 是否已通过看广告签到
   * - canWatchAd: 是否还可以看广告签到（领过直接奖励但没看过广告）
   */
  checkDailySign() {
    const gd = this.globalData.gameData;
    const today = this.getDateStr();
    const signedToday = gd.lastSignDate === today;
    const signAdWatched = signedToday && gd.signAdWatched;
    // 如果没签过到，可以看广告；如果签过到但没看广告，也可以看广告
    const canWatchAd = !signAdWatched && (!signedToday || !gd.signAdWatched);
    return {
      canSign: !signedToday,
      signedToday: signedToday,
      signAdWatched: signAdWatched,
      canWatchAd: canWatchAd,
      today: today,
    };
  },

  /**
   * 每日签到 - 直接领取（不看广告）
   * 返回: { success: boolean, points: 20 }
   */
  dailySignBasic() {
    const gd = this.globalData.gameData;
    const today = this.getDateStr();
    if (gd.lastSignDate === today) {
      return { success: false, reason: '今日已签到' };
    }
    gd.lastSignDate = today;
    gd.signAdWatched = false;
    gd.points = (gd.points || 0) + 20;
    this.saveGameData();
    return { success: true, points: 20 };
  },

  /**
   * 每日签到 - 看广告签到
   * 返回: { success: boolean, points: 40, tools: {...} }
   */
  dailySignAd() {
    const gd = this.globalData.gameData;
    const today = this.getDateStr();
    // 如果已经通过广告签到过，不能再来一次
    if (gd.lastSignDate === today && gd.signAdWatched) {
      return { success: false, reason: '今日已通过广告签到' };
    }
    // 如果之前直接领过，补发奖励差额
    const alreadyBasic = gd.lastSignDate === today && !gd.signAdWatched;
    gd.lastSignDate = today;
    gd.signAdWatched = true;
    // 道具奖励
    gd.tools.revoke = (gd.tools.revoke || 0) + 1;
    gd.tools.shuffle = (gd.tools.shuffle || 0) + 1;
    gd.tools.extraSlot = (gd.tools.extraSlot || 0) + 1;
    gd.tools.hint = (gd.tools.hint || 0) + 1;
    // 积分：如果直接领过就只补 20，否则给 40
    const extraPoints = alreadyBasic ? 20 : 40;
    gd.points = (gd.points || 0) + extraPoints;
    this.saveGameData();
    return {
      success: true,
      points: extraPoints,
      isUpgrade: alreadyBasic,
      tools: { revoke: 1, shuffle: 1, extraSlot: 1, hint: 1 },
    };
  },

  getDateStr() {
    const d = new Date();
    return d.getFullYear() + '-' +
      String(d.getMonth() + 1).padStart(2, '0') + '-' +
      String(d.getDate()).padStart(2, '0');
  },

  /**
   * 从云数据库拉取全局排行
   */
  syncCloudRankings() {
    if (!wx.cloud) return;
    const db = wx.cloud.database();
    db.collection('rankings')
      .orderBy('maxLevel', 'desc')
      .limit(10)
      .get()
      .then(res => {
        const gd = this.globalData.gameData;
        const cloudRankings = res.data.map(item => ({
          name: item.name,
          maxLevel: item.maxLevel,
          isSelf: item.name === gd.playerName,
          _openid: item._openid,
        }));
        const selfInList = cloudRankings.find(r => r.isSelf);
        if (!selfInList && gd.challengeMaxLevel > 0) {
          cloudRankings.push({
            name: gd.playerName,
            maxLevel: gd.challengeMaxLevel,
            isSelf: true,
          });
          cloudRankings.sort((a, b) => b.maxLevel - a.maxLevel);
          if (cloudRankings.length > 10) cloudRankings.pop();
        }
        gd.rankings = cloudRankings;
        this.saveGameData();
      })
      .catch(() => {});
  },

  /**
   * 增加积分（通关奖励或看广告）
   */
  addPoints(amount) {
    const gd = this.globalData.gameData;
    if (gd.points === undefined) gd.points = 0;
    gd.points += amount;
    this.saveGameData();
    return gd.points;
  },

  /**
   * 消耗积分（后续可用于兑换道具等）
   */
  usePoints(amount) {
    const gd = this.globalData.gameData;
    if (gd.points === undefined) gd.points = 0;
    if (gd.points < amount) return false;
    gd.points -= amount;
    this.saveGameData();
    return true;
  },

  /**
   * 获取当前积分
   */
  getPoints() {
    const gd = this.globalData.gameData;
    return gd.points || 0;
  },

  /**
   * 处理邀请逻辑
   * 被邀请者进入时调用，只有新用户（首次注册）且未被邀请过才有效
   * 返回: { success, message, bonus }
   */
  handleInvitation(inviterId) {
    const gd = this.globalData.gameData;
    const myUserId = gd.userId;

    // 1. 不能邀请自己
    if (inviterId === myUserId) {
      return { success: false, message: '不能邀请自己' };
    }

    // 2. 必须是新用户（首次进入）
    if (!gd.isNewPlayer) {
      return { success: false, message: '您已是老玩家，邀请仅对新用户有效' };
    }

    // 3. 检查本地是否已被邀请过
    if (gd.invitedBy) {
      return { success: false, message: '您已通过邀请进入过' };
    }

    // 4. 记录邀请关系
    const bonus = Math.floor(Math.random() * 11) + 5; // 随机 5~15 积分
    gd.invitedBy = inviterId;
    this.saveGameData();

    // 5. 通过云数据库给邀请人加积分（如果云开发可用）
    if (wx.cloud) {
      const db = wx.cloud.database();
      // 先检查邀请记录是否已存在（防止重复）
      db.collection('invitations').add({
        data: {
          inviterId: inviterId,
          inviteeId: myUserId,
          bonus: bonus,
          createdAt: new Date(),
        },
      }).catch(() => {
        // 云函数添加失败不阻塞本地流程
      });
    }

    return { success: true, bonus: bonus };
  },

  /**
   * 检查并领取待处理的邀请奖励（本地存储方案）
   * 在每次启动时调用
   */
  checkPendingInviteRewards() {
    const pending = wx.getStorageSync('pendingInviteRewards') || [];
    if (pending.length === 0) return;

    const gd = this.globalData.gameData;
    const myUserId = gd.userId;

    // 筛选属于当前用户的奖励
    const myRewards = pending.filter(item => item.inviterId === myUserId);
    if (myRewards.length === 0) return;

    let totalBonus = 0;
    myRewards.forEach(item => {
      totalBonus += item.bonus;
    });

    // 给当前用户加积分
    gd.points = (gd.points || 0) + totalBonus;

    // 清除已领取的奖励
    const remaining = pending.filter(item => item.inviterId !== myUserId);
    wx.setStorageSync('pendingInviteRewards', remaining);

    this.saveGameData();

    // 延迟显示提示（等页面渲染完成）
    setTimeout(() => {
      wx.showToast({
        title: '🎉 好友通过邀请加入！+' + totalBonus + ' 积分',
        icon: 'none',
        duration: 2500,
      });
    }, 1500);
  },

  globalData: {
    gameData: {
      highScore: 0,
      totalGames: 0,
      totalWins: 0,
      easyWins: 0,
      normalWins: 0,
      nightmareWins: 0,
      normalUnlocked: false,
      nightmareUnlocked: false,
      challengeMaxLevel: 0,
      challengeMaxClearCount: 0,
      playerName: '',
      tools: { revoke: 0, shuffle: 0, extraSlot: 0, hint: 0 },
      isNewPlayer: true,
      lastSignDate: '',
      rankings: [],
      points: 0,
      settings: { musicOn: true, soundOn: true },
      userId: '',
    },
  },
});
