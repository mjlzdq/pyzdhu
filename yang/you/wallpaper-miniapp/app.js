// app.js
App({
  globalData: {
    userInfo: null,
    openId: '',
    isLogin: false,
    // 激励视频广告单元ID，上线前替换为正式ID
    rewardedVideoAdUnitId: 'adunit-xxxxxxxxxxxxxx',
    // 插屏广告单元ID
    interstitialAdUnitId: 'adunit-xxxxxxxxxxxxxx',
    // Banner广告单元ID
    bannerAdUnitId: 'adunit-xxxxxxxxxxxxxx',
    // 收藏数据
    favorites: [],
    // 浏览历史
    history: []
  },

  onLaunch() {
    // 初始化云开发
    if (wx.cloud) {
      wx.cloud.init({
        env: 'your-env-id', // 替换为你的云开发环境ID
        traceUser: true
      });
    }

    // 从本地缓存读取收藏和历史
    const favorites = wx.getStorageSync('favorites') || [];
    const history = wx.getStorageSync('history') || [];
    this.globalData.favorites = favorites;
    this.globalData.history = history;

    // 登录
    this.wxLogin();
  },

  // 微信登录获取openId
  wxLogin() {
    const that = this;
    wx.login({
      success(res) {
        if (res.code && wx.cloud) {
          wx.cloud.callFunction({
            name: 'login',
            data: { code: res.code },
            success: (loginRes) => {
              that.globalData.openId = loginRes.result.openid;
              that.globalData.isLogin = true;
            },
            fail: () => {
              // 云函数调用失败，仍可正常使用（收藏用本地存储）
              that.globalData.isLogin = true;
            }
          });
        } else {
          that.globalData.isLogin = true;
        }
      }
    });
  },

  // 检查是否已收藏
  isFavorite(wallpaperId) {
    return this.globalData.favorites.includes(wallpaperId);
  },

  // 切换收藏状态
  toggleFavorite(wallpaperId) {
    const index = this.globalData.favorites.indexOf(wallpaperId);
    if (index > -1) {
      this.globalData.favorites.splice(index, 1);
      wx.setStorageSync('favorites', this.globalData.favorites);
      return false; // 取消收藏
    } else {
      this.globalData.favorites.push(wallpaperId);
      wx.setStorageSync('favorites', this.globalData.favorites);
      return true; // 已收藏
    }
  },

  // 添加到浏览历史
  addHistory(wallpaper) {
    let history = this.globalData.history;
    // 去重
    history = history.filter(item => item._id !== wallpaper._id);
    // 添加到最前面
    history.unshift(wallpaper);
    // 最多保留100条
    if (history.length > 100) {
      history = history.slice(0, 100);
    }
    this.globalData.history = history;
    wx.setStorageSync('history', history);
  }
});
