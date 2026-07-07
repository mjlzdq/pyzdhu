// pages/category/category.js
Page({
  data: {
    categories: [
      { name: '风景', icon: '🏞️', count: 0 },
      { name: '动漫', icon: '🎨', count: 0 },
      { name: '简约', icon: '✨', count: 0 },
      { name: '文字', icon: '📝', count: 0 },
      { name: '头像', icon: '👤', count: 0 },
      { name: '萌宠', icon: '🐱', count: 0 },
      { name: '星空', icon: '🌌', count: 0 },
      { name: '植物', icon: '🌿', count: 0 },
      { name: '美食', icon: '🍜', count: 0 },
      { name: '城市', icon: '🌆', count: 0 },
      { name: '汽车', icon: '🚗', count: 0 },
      { name: '游戏', icon: '🎮', count: 0 }
    ],
    currentCategory: '',
    wallpapers: [],
    leftList: [],
    rightList: [],
    totalCount: 0,
    page: 1,
    pageSize: 20,
    loading: false,
    noMore: false
  },

  onLoad() {
    this.loadCategoryCounts();
  },

  onShow() {
    if (this.data.wallpapers.length === 0 && this.data.currentCategory) {
      this.loadWallpapers(true);
    }
  },

  onPullDownRefresh() {
    this.setData({ page: 1, noMore: false });
    this.loadWallpapers(true);
  },

  onReachBottom() {
    if (!this.data.loading && !this.data.noMore && this.data.currentCategory) {
      this.loadWallpapers();
    }
  },

  // 加载各分类数量
  loadCategoryCounts() {
    if (!wx.cloud) return;

    const db = wx.cloud.database();
    const categories = this.data.categories;
    const promises = categories.map((cat, index) => {
      return db.collection('wallpapers')
        .where({ category: cat.name })
        .count()
        .then(res => {
          this.setData({ [`categories[${index}].count`]: res.total });
        })
        .catch(() => {});
    });

    Promise.all(promises);
  },

  // 切换分类
  switchCategory(e) {
    const category = e.currentTarget.dataset.category;
    if (category === this.data.currentCategory) return;

    this.setData({
      currentCategory: category,
      page: 1,
      noMore: false,
      wallpapers: [],
      leftList: [],
      rightList: []
    });
    this.loadWallpapers(true);
  },

  // 加载壁纸
  loadWallpapers(refresh = false) {
    if (this.data.loading) return;
    this.setData({ loading: true });

    const that = this;
    const { page, pageSize, currentCategory } = this.data;

    if (wx.cloud) {
      const db = wx.cloud.database();
      db.collection('wallpapers')
        .where({ category: currentCategory })
        .orderBy('createTime', 'desc')
        .skip((page - 1) * pageSize)
        .limit(pageSize)
        .get()
        .then(res => {
          that.processWallpapers(res.data, refresh);
        })
        .catch(() => {
          that.loadMockData(refresh);
        });
    } else {
      this.loadMockData(refresh);
    }
  },

  processWallpapers(data, refresh) {
    if (!data || data.length === 0) {
      this.setData({ loading: false, noMore: true });
      wx.stopPullDownRefresh();
      return;
    }

    const processed = data.map(item => {
      const ratio = item.height && item.width ? item.height / item.width : 1.5;
      return { ...item, displayHeight: Math.round(175 * ratio) };
    });

    const wallpapers = refresh ? processed : [...this.data.wallpapers, ...processed];

    const leftList = [];
    const rightList = [];
    let leftHeight = 0, rightHeight = 0;

    wallpapers.forEach(item => {
      if (leftHeight <= rightHeight) {
        leftList.push(item);
        leftHeight += item.displayHeight || 200;
      } else {
        rightList.push(item);
        rightHeight += item.displayHeight || 200;
      }
    });

    this.setData({
      wallpapers,
      leftList,
      rightList,
      totalCount: wallpapers.length,
      page: refresh ? 1 : this.data.page + 1,
      loading: false,
      noMore: data.length < this.data.pageSize
    });

    wx.stopPullDownRefresh();
  },

  loadMockData(refresh) {
    const that = this;
    const { currentCategory } = this.data;
    const mockWallpapers = [];

    for (let i = 0; i < 20; i++) {
      const width = 400;
      const height = Math.floor(Math.random() * 400 + 300);
      mockWallpapers.push({
        _id: `cat_mock_${Date.now()}_${i}`,
        url: `https://picsum.photos/${width}/${height}?random=${Date.now() + i}`,
        thumbUrl: `https://picsum.photos/${width}/${height}?random=${Date.now() + i}`,
        width,
        height,
        category: currentCategory,
        tags: [currentCategory, '高清'],
        likes: Math.floor(Math.random() * 999),
        createTime: Date.now() - i * 3600000
      });
    }

    this.processWallpapers(mockWallpapers, refresh);
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  }
});
