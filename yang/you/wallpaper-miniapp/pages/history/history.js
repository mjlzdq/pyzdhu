// pages/history/history.js
const app = getApp();

Page({
  data: {
    wallpapers: [],
    leftList: [],
    rightList: []
  },

  onShow() {
    this.loadHistory();
  },

  loadHistory() {
    const history = app.globalData.history;

    // 格式化时间
    const processed = history.map(item => ({
      ...item,
      displayHeight: item.height && item.width 
        ? Math.round(175 * (item.height / item.width)) 
        : 260,
      viewTime: this.formatTime(item.createTime || Date.now())
    }));

    const leftList = [];
    const rightList = [];
    let leftHeight = 0, rightHeight = 0;

    processed.forEach(item => {
      if (leftHeight <= rightHeight) {
        leftList.push(item);
        leftHeight += item.displayHeight || 200;
      } else {
        rightList.push(item);
        rightHeight += item.displayHeight || 200;
      }
    });

    this.setData({ wallpapers: processed, leftList, rightList });
  },

  formatTime(timestamp) {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    
    const date = new Date(timestamp);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  },

  // 清空浏览记录
  clearHistory() {
    wx.showModal({
      title: '提示',
      content: '确定清空所有浏览记录吗？',
      success: (res) => {
        if (res.confirm) {
          app.globalData.history = [];
          wx.setStorageSync('history', []);
          this.setData({ wallpapers: [], leftList: [], rightList: [] });
          wx.showToast({ title: '已清空', icon: 'none' });
        }
      }
    });
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  }
});
