// pages/search/search.js
Page({
  data: {
    keyword: '',
    historyList: [],
    hotTags: ['风景', '动漫', '简约', '星空', '头像', '萌宠', '文字', '4K'],
    wallpapers: [],
    leftList: [],
    rightList: [],
    totalCount: 0,
    hasSearched: false,
    page: 1,
    pageSize: 20,
    loading: false,
    noMore: false
  },

  onLoad() {
    this.loadHistory();
  },

  // 加载搜索历史
  loadHistory() {
    const history = wx.getStorageSync('searchHistory') || [];
    this.setData({ historyList: history });
  },

  // 保存搜索历史
  saveHistory(keyword) {
    let history = wx.getStorageSync('searchHistory') || [];
    // 去重
    history = history.filter(item => item !== keyword);
    // 添加到最前面
    history.unshift(keyword);
    // 最多保留20条
    if (history.length > 20) {
      history = history.slice(0, 20);
    }
    wx.setStorageSync('searchHistory', history);
    this.setData({ historyList: history });
  },

  // 输入事件
  onInput(e) {
    this.setData({ keyword: e.detail.value });
  },

  // 搜索确认
  onSearch() {
    const keyword = this.data.keyword.trim();
    if (!keyword) return;

    this.saveHistory(keyword);

    this.setData({
      hasSearched: true,
      page: 1,
      noMore: false,
      wallpapers: [],
      leftList: [],
      rightList: []
    });

    this.doSearch();
  },

  // 搜索历史点击
  searchHistory(e) {
    const keyword = e.currentTarget.dataset.keyword;
    this.setData({ keyword });
    this.onSearch();
  },

  // 热门搜索点击
  searchHot(e) {
    const keyword = e.currentTarget.dataset.keyword;
    this.setData({ keyword });
    this.onSearch();
  },

  // 清除输入
  clearInput() {
    this.setData({
      keyword: '',
      hasSearched: false,
      wallpapers: [],
      leftList: [],
      rightList: []
    });
  },

  // 清除搜索历史
  clearHistory() {
    wx.removeStorageSync('searchHistory');
    this.setData({ historyList: [] });
  },

  // 返回
  goBack() {
    wx.navigateBack();
  },

  // 触底加载更多
  onReachBottom() {
    if (!this.data.loading && !this.data.noMore && this.data.hasSearched) {
      this.doSearch();
    }
  },

  // 执行搜索
  doSearch() {
    if (this.data.loading) return;
    this.setData({ loading: true });

    const that = this;
    const { keyword, page, pageSize } = this.data;

    if (wx.cloud) {
      const db = wx.cloud.database();
      const _ = db.command;

      // 搜索分类和标签
      db.collection('wallpapers')
        .where(_.or([
          { category: db.RegExp({ regexp: keyword, options: 'i' }) },
          { tags: db.RegExp({ regexp: keyword, options: 'i' }) }
        ]))
        .orderBy('createTime', 'desc')
        .skip((page - 1) * pageSize)
        .limit(pageSize)
        .get()
        .then(res => {
          that.processResults(res.data);
        })
        .catch(() => {
          that.mockSearch();
        });
    } else {
      this.mockSearch();
    }
  },

  processResults(data) {
    if (!data || data.length === 0) {
      this.setData({ loading: false, noMore: true });
      return;
    }

    const processed = data.map(item => {
      const ratio = item.height && item.width ? item.height / item.width : 1.5;
      return { ...item, displayHeight: Math.round(175 * ratio) };
    });

    const wallpapers = [...this.data.wallpapers, ...processed];

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
      page: this.data.page + 1,
      loading: false,
      noMore: data.length < this.data.pageSize
    });
  },

  mockSearch() {
    const keyword = this.data.keyword;
    const mockList = [];
    const count = Math.floor(Math.random() * 15 + 5);

    for (let i = 0; i < count; i++) {
      const width = 400;
      const height = Math.floor(Math.random() * 400 + 300);
      mockList.push({
        _id: `search_${Date.now()}_${i}`,
        url: `https://picsum.photos/${width}/${height}?random=${Date.now() + i + 200}`,
        thumbUrl: `https://picsum.photos/${width}/${height}?random=${Date.now() + i + 200}`,
        width,
        height,
        category: keyword,
        tags: [keyword, '高清'],
        likes: Math.floor(Math.random() * 500),
        createTime: Date.now() - i * 3600000
      });
    }

    this.processResults(mockList);
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  }
});
