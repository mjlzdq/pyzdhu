// pages/index/index.js
const app = getApp();

Page({
  data: {
    categories: [
      { name: '风景', icon: '🏞️' },
      { name: '动漫', icon: '🎨' },
      { name: '简约', icon: '✨' },
      { name: '文字', icon: '📝' },
      { name: '头像', icon: '👤' },
      { name: '萌宠', icon: '🐱' },
      { name: '星空', icon: '🌌' },
      { name: '植物', icon: '🌿' }
    ],
    currentCategory: '',
    wallpapers: [],
    leftList: [],
    rightList: [],
    page: 1,
    pageSize: 20,
    loading: false,
    noMore: false,
    bannerAdUnitId: 'adunit-xxxxxxxxxxxxxx',
    bannerAdVisible: true
  },

  onLoad() {
    this.loadWallpapers();
  },

  onShow() {
    // 每次回到首页，如果列表为空则重新加载
    if (this.data.wallpapers.length === 0) {
      this.setData({ page: 1, noMore: false });
      this.loadWallpapers();
    }
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.setData({ page: 1, noMore: false });
    this.loadWallpapers(true);
  },

  // 触底加载更多
  onReachBottom() {
    if (!this.data.loading && !this.data.noMore) {
      this.loadWallpapers();
    }
  },

  // 加载壁纸数据
  loadWallpapers(refresh = false) {
    if (this.data.loading) return;
    this.setData({ loading: true });

    const that = this;
    const { page, pageSize, currentCategory } = this.data;

    if (wx.cloud) {
      // 云开发方式加载
      const db = wx.cloud.database();
      let query = db.collection('wallpapers');

      if (currentCategory) {
        query = query.where({ category: currentCategory });
      }

      query
        .orderBy('createTime', 'desc')
        .skip((page - 1) * pageSize)
        .limit(pageSize)
        .get()
        .then(res => {
          that.processWallpapers(res.data, refresh);
        })
        .catch(err => {
          console.error('加载壁纸失败:', err);
          that.loadMockData(refresh);
        });
    } else {
      // 无云开发时使用模拟数据
      this.loadMockData(refresh);
    }
  },

  // 处理壁纸数据，计算瀑布流高度
  processWallpapers(data, refresh) {
    if (!data || data.length === 0) {
      this.setData({ 
        loading: false, 
        noMore: true 
      });
      wx.stopPullDownRefresh();
      return;
    }

    // 为每张壁纸计算展示高度（根据图片宽高比，预设宽度约175px）
    const processed = data.map(item => {
      const ratio = item.height && item.width ? item.height / item.width : 1.5;
      // 列宽约 175px (rpx换算后)
      const displayHeight = Math.round(175 * ratio);
      return { ...item, displayHeight };
    });

    let wallpapers;
    if (refresh) {
      wallpapers = processed;
    } else {
      wallpapers = [...this.data.wallpapers, ...processed];
    }

    // 瀑布流分列（贪心算法，较矮的列优先）
    const leftList = [];
    const rightList = [];
    let leftHeight = 0;
    let rightHeight = 0;

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
      page: refresh ? 1 : this.data.page + 1,
      loading: false,
      noMore: data.length < this.data.pageSize
    });

    wx.stopPullDownRefresh();
  },

  // 模拟数据（开发和测试用）
  loadMockData(refresh) {
    const mockWallpapers = [];
    const categories = ['风景', '动漫', '简约', '文字', '头像', '萌宠', '星空', '植物'];
    
    for (let i = 0; i < 20; i++) {
      const cat = categories[Math.floor(Math.random() * categories.length)];
      const width = 400;
      const height = Math.floor(Math.random() * 400 + 300); // 300-700
      
      mockWallpapers.push({
        _id: `mock_${Date.now()}_${i}`,
        url: `https://picsum.photos/${width}/${height}?random=${Date.now() + i}`,
        thumbUrl: `https://picsum.photos/${width}/${height}?random=${Date.now() + i}`,
        width,
        height,
        category: cat,
        tags: [cat, '高清', '壁纸'],
        likes: Math.floor(Math.random() * 999),
        createTime: Date.now() - i * 3600000
      });
    }

    this.processWallpapers(mockWallpapers, refresh);
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
    this.loadWallpapers();
  },

  // 跳转搜索页
  goSearch() {
    wx.navigateTo({ url: '/pages/search/search' });
  },

  // 跳转详情页
  goDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  },

  // 广告加载成功
  onBannerLoad() {
    console.log('Banner广告加载成功');
  },

  // 广告加载失败
  onBannerError(err) {
    console.log('Banner广告加载失败:', err);
    this.setData({ bannerAdVisible: false });
  }
});
