// pages/favorites/favorites.js
const app = getApp();

Page({
  data: {
    wallpapers: [],
    leftList: [],
    rightList: [],
    loading: false
  },

  onShow() {
    this.loadFavorites();
  },

  // 加载收藏列表
  loadFavorites() {
    const favoriteIds = app.globalData.favorites;
    if (favoriteIds.length === 0) {
      this.setData({ wallpapers: [], leftList: [], rightList: [] });
      return;
    }

    this.setData({ loading: true });

    if (wx.cloud) {
      // 从云数据库获取收藏的壁纸详情
      const db = wx.cloud.database();
      const _ = db.command;

      db.collection('wallpapers')
        .where({ _id: _.in(favoriteIds) })
        .get()
        .then(res => {
          this.processWallpapers(res.data);
        })
        .catch(() => {
          // 云数据库查询失败，从本地历史中匹配
          this.loadFromHistory(favoriteIds);
        });
    } else {
      this.loadFromHistory(favoriteIds);
    }
  },

  // 从本地历史数据中匹配收藏
  loadFromHistory(favoriteIds) {
    const history = app.globalData.history;
    const matched = history.filter(item => favoriteIds.includes(item._id));
    this.processWallpapers(matched);
  },

  processWallpapers(data) {
    const processed = data.map(item => {
      const ratio = item.height && item.width ? item.height / item.width : 1.5;
      return { ...item, displayHeight: Math.round(175 * ratio) };
    });

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

    this.setData({
      wallpapers: processed,
      leftList,
      rightList,
      loading: false
    });
  },

  // 取消收藏
  removeFavorite(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示',
      content: '确定取消收藏吗？',
      success: (res) => {
        if (res.confirm) {
          app.toggleFavorite(id);
          this.loadFavorites();
          wx.showToast({ title: '已取消收藏', icon: 'none' });
        }
      }
    });
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  }
});
