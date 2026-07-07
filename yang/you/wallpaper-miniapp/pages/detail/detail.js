// pages/detail/detail.js
const app = getApp();

Page({
  data: {
    wallpaperId: '',
    wallpaper: null,
    isFavorited: false,
    loading: true,
    showAdModal: false,
    toastVisible: false,
    toastText: '',
    // 推荐列表
    recommendList: [],
    leftRecommend: [],
    rightRecommend: []
  },

  onLoad(options) {
    const id = options.id;
    if (!id) {
      wx.showToast({ title: '参数错误', icon: 'error' });
      wx.navigateBack();
      return;
    }

    this.setData({ wallpaperId: id });
    this.loadWallpaper(id);
    this.createRewardedVideoAd();
  },

  // 创建激励视频广告
  createRewardedVideoAd() {
    // 检查是否有广告API（开发工具可能不支持）
    if (!wx.createRewardedVideoAd) return;

    const rewardedVideoAd = wx.createRewardedVideoAd({
      adUnitId: 'adunit-xxxxxxxxxxxxxx' // 替换为正式广告单元ID
    });

    rewardedVideoAd.onLoad(() => {
      console.log('激励视频广告加载成功');
    });

    rewardedVideoAd.onError((err) => {
      console.error('激励视频广告错误:', err);
    });

    rewardedVideoAd.onClose((res) => {
      if (res && res.isEnded) {
        // 用户完整观看了视频，执行下载
        this.doDownload();
      } else {
        // 用户中途关闭了视频
        this.showToast('观看完整视频才能下载哦~');
      }
    });

    this.rewardedVideoAd = rewardedVideoAd;
  },

  // 加载壁纸详情
  loadWallpaper(id) {
    this.setData({ loading: true });

    if (wx.cloud) {
      const db = wx.cloud.database();
      db.collection('wallpapers')
        .doc(id)
        .get()
        .then(res => {
          const wallpaper = res.data;
          this.setWallpaperData(wallpaper);
          this.loadRecommendList(wallpaper.category);
        })
        .catch(() => {
          this.loadMockData(id);
        });
    } else {
      this.loadMockData(id);
    }
  },

  loadMockData(id) {
    const width = 800;
    const height = 1200;
    const wallpaper = {
      _id: id,
      url: `https://picsum.photos/${width}/${height}?random=${id}`,
      thumbUrl: `https://picsum.photos/400/600?random=${id}`,
      width,
      height,
      category: '风景',
      tags: ['风景', '自然', '高清', '4K'],
      likes: 328,
      views: 1520,
      downloads: 86,
      createTime: Date.now()
    };

    this.setWallpaperData(wallpaper);
    this.loadMockRecommend();
  },

  setWallpaperData(wallpaper) {
    const isFavorited = app.isFavorite(wallpaper._id);

    // 添加到浏览历史
    app.addHistory(wallpaper);

    this.setData({
      wallpaper,
      isFavorited,
      loading: false
    });
  },

  // 加载推荐列表（同分类的壁纸）
  loadRecommendList(category) {
    if (!wx.cloud) {
      this.loadMockRecommend();
      return;
    }

    const db = wx.cloud.database();
    db.collection('wallpapers')
      .where({ category })
      .orderBy('likes', 'desc')
      .limit(10)
      .get()
      .then(res => {
        const list = res.data.filter(item => item._id !== this.data.wallpaperId);
        this.processRecommend(list);
      })
      .catch(() => {
        this.loadMockRecommend();
      });
  },

  loadMockRecommend() {
    const mockList = [];
    for (let i = 0; i < 6; i++) {
      const width = 400;
      const height = Math.floor(Math.random() * 400 + 300);
      mockList.push({
        _id: `rec_${Date.now()}_${i}`,
        url: `https://picsum.photos/${width}/${height}?random=${Date.now() + i + 100}`,
        thumbUrl: `https://picsum.photos/${width}/${height}?random=${Date.now() + i + 100}`,
        width,
        height,
        category: '风景',
        likes: Math.floor(Math.random() * 500),
        createTime: Date.now() - i * 7200000
      });
    }
    this.processRecommend(mockList);
  },

  processRecommend(list) {
    const processed = list.map(item => {
      const ratio = item.height && item.width ? item.height / item.width : 1.5;
      return { ...item, displayHeight: Math.round(175 * ratio) };
    });

    const leftRecommend = [];
    const rightRecommend = [];
    let leftHeight = 0, rightHeight = 0;

    processed.forEach(item => {
      if (leftHeight <= rightHeight) {
        leftRecommend.push(item);
        leftHeight += item.displayHeight || 200;
      } else {
        rightRecommend.push(item);
        rightHeight += item.displayHeight || 200;
      }
    });

    this.setData({ recommendList: processed, leftRecommend, rightRecommend });
  },

  // 下载壁纸（弹出激励视频弹窗）
  downloadWallpaper() {
    this.setData({ showAdModal: true });
  },

  // 关闭广告弹窗
  closeAdModal() {
    this.setData({ showAdModal: false });
  },

  // 观看广告并下载
  watchAdAndDownload() {
    this.setData({ showAdModal: false });

    if (this.rewardedVideoAd) {
      // 使用微信激励视频广告
      this.rewardedVideoAd.show().catch(() => {
        // 广告加载失败，重新加载后再展示
        this.rewardedVideoAd.load().then(() => {
          this.rewardedVideoAd.show().catch(() => {
            // 仍然失败，降级为直接下载
            this.doDownload();
          });
        }).catch(() => {
          this.doDownload();
        });
      });
    } else {
      // 开发环境或无广告能力，直接下载
      this.doDownload();
    }
  },

  // 执行下载
  doDownload() {
    const that = this;
    const url = this.data.wallpaper.url;

    wx.showLoading({ title: '下载中...' });

    // 获取保存相册权限
    wx.getSetting({
      success(res) {
        if (!res.authSetting['scope.writePhotosAlbum']) {
          wx.authorize({
            scope: 'scope.writePhotosAlbum',
            success() {
              that.saveImage(url);
            },
            fail() {
              // 用户拒绝授权，引导打开设置
              wx.hideLoading();
              wx.showModal({
                title: '提示',
                content: '需要授权保存到相册才能下载壁纸哦~',
                confirmText: '去授权',
                success(modalRes) {
                  if (modalRes.confirm) {
                    wx.openSetting();
                  }
                }
              });
            }
          });
        } else {
          that.saveImage(url);
        }
      }
    });
  },

  // 保存图片到相册
  saveImage(url) {
    const that = this;
    wx.downloadFile({
      url,
      success(res) {
        if (res.statusCode === 200) {
          wx.saveImageToPhotosAlbum({
            filePath: res.tempFilePath,
            success() {
              wx.hideLoading();
              that.showToast('壁纸已保存到相册 🎉');
              // 更新下载计数
              that.updateDownloadCount();
            },
            fail(err) {
              wx.hideLoading();
              console.error('保存失败:', err);
              that.showToast('保存失败，请重试');
            }
          });
        } else {
          wx.hideLoading();
          that.showToast('下载失败，请重试');
        }
      },
      fail() {
        wx.hideLoading();
        that.showToast('下载失败，请检查网络');
      }
    });
  },

  // 更新下载计数（云数据库）
  updateDownloadCount() {
    if (!wx.cloud || !this.data.wallpaper._id) return;

    const db = wx.cloud.database();
    db.collection('wallpapers').doc(this.data.wallpaper._id).update({
      data: {
        downloads: db.command.inc(1)
      }
    }).catch(() => {});
  },

  // 切换收藏
  toggleFavorite() {
    const wallpaperId = this.data.wallpaper._id;
    const result = app.toggleFavorite(wallpaperId);
    this.setData({ isFavorited: result });

    wx.showToast({
      title: result ? '已收藏' : '已取消收藏',
      icon: 'none',
      duration: 1500
    });
  },

  // 跳转到其他详情
  goDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.redirectTo({ url: `/pages/detail/detail?id=${id}` });
  },

  // Toast 提示
  showToast(text) {
    this.setData({ toastVisible: true, toastText: text });
    setTimeout(() => {
      this.setData({ toastVisible: false });
    }, 2000);
  },

  // 分享给好友
  onShareAppMessage() {
    return {
      title: '送你一张超好看的壁纸！',
      path: `/pages/detail/detail?id=${this.data.wallpaperId}`,
      imageUrl: this.data.wallpaper.thumbUrl || this.data.wallpaper.url
    };
  },

  // 分享到朋友圈
  onShareTimeline() {
    return {
      title: '超清壁纸，快来看看吧~',
      query: `id=${this.data.wallpaperId}`,
      imageUrl: this.data.wallpaper.thumbUrl || this.data.wallpaper.url
    };
  }
});
