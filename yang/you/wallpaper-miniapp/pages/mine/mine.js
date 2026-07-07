// pages/mine/mine.js
const app = getApp();

Page({
  data: {
    userInfo: null,
    favoriteCount: 0,
    historyCount: 0,
    downloadCount: 0
  },

  onShow() {
    // 更新统计数据
    const favorites = wx.getStorageSync('favorites') || [];
    const history = wx.getStorageSync('history') || [];
    const downloads = wx.getStorageSync('downloadCount') || 0;

    this.setData({
      favoriteCount: favorites.length,
      historyCount: history.length,
      downloadCount
    });
  },

  onLoad() {
    // 获取用户信息（可选）
    wx.getUserInfo({
      success: (res) => {
        this.setData({ userInfo: res.userInfo });
      },
      fail: () => {
        // 用户拒绝授权，使用默认头像
      }
    });
  },

  // 跳转收藏页
  goFavorites() {
    wx.navigateTo({ url: '/pages/favorites/favorites' });
  },

  // 跳转浏览历史
  goHistory() {
    wx.navigateTo({ url: '/pages/history/history' });
  },

  // 分享
  onShareAppMessage() {
    return {
      title: '超多高清壁纸免费下载，快来试试吧！',
      path: '/pages/index/index',
      imageUrl: ''
    };
  }
});
