// 云函数：初始化数据库集合
// 在云开发控制台上传并运行一次即可
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();

exports.main = async (event, context) => {
  try {
    // 创建 wallpapers 集合（如果不存在会自动创建）
    const wallpaperCollection = db.collection('wallpapers');
    
    // 添加示例壁纸数据
    const sampleWallpapers = [
      {
        url: 'https://picsum.photos/800/1200?random=1',
        thumbUrl: 'https://picsum.photos/400/600?random=1',
        width: 800,
        height: 1200,
        category: '风景',
        tags: ['风景', '自然', '山', '4K'],
        likes: 328,
        views: 1520,
        downloads: 86,
        createTime: Date.now()
      },
      {
        url: 'https://picsum.photos/800/1400?random=2',
        thumbUrl: 'https://picsum.photos/400/700?random=2',
        width: 800,
        height: 1400,
        category: '动漫',
        tags: ['动漫', '二次元', '唯美'],
        likes: 512,
        views: 2300,
        downloads: 156,
        createTime: Date.now() - 3600000
      },
      {
        url: 'https://picsum.photos/800/1000?random=3',
        thumbUrl: 'https://picsum.photos/400/500?random=3',
        width: 800,
        height: 1000,
        category: '简约',
        tags: ['简约', '极简', '纯色', '干净'],
        likes: 186,
        views: 890,
        downloads: 42,
        createTime: Date.now() - 7200000
      },
      {
        url: 'https://picsum.photos/800/1300?random=4',
        thumbUrl: 'https://picsum.photos/400/650?random=4',
        width: 800,
        height: 1300,
        category: '星空',
        tags: ['星空', '银河', '宇宙', '夜景'],
        likes: 445,
        views: 1980,
        downloads: 128,
        createTime: Date.now() - 10800000
      },
      {
        url: 'https://picsum.photos/600/600?random=5',
        thumbUrl: 'https://picsum.photos/300/300?random=5',
        width: 600,
        height: 600,
        category: '头像',
        tags: ['头像', '个性', '简约'],
        likes: 234,
        views: 1100,
        downloads: 67,
        createTime: Date.now() - 14400000
      },
      {
        url: 'https://picsum.photos/800/1200?random=6',
        thumbUrl: 'https://picsum.photos/400/600?random=6',
        width: 800,
        height: 1200,
        category: '萌宠',
        tags: ['萌宠', '猫咪', '可爱', '治愈'],
        likes: 678,
        views: 3200,
        downloads: 210,
        createTime: Date.now() - 18000000
      },
      {
        url: 'https://picsum.photos/800/1100?random=7',
        thumbUrl: 'https://picsum.photos/400/550?random=7',
        width: 800,
        height: 1100,
        category: '植物',
        tags: ['植物', '花卉', '绿色', '清新'],
        likes: 289,
        views: 1340,
        downloads: 78,
        createTime: Date.now() - 21600000
      },
      {
        url: 'https://picsum.photos/800/1250?random=8',
        thumbUrl: 'https://picsum.photos/400/625?random=8',
        width: 800,
        height: 1250,
        category: '文字',
        tags: ['文字', '励志', '语录', '文案'],
        likes: 156,
        views: 760,
        downloads: 35,
        createTime: Date.now() - 25200000
      },
      {
        url: 'https://picsum.photos/800/1350?random=9',
        thumbUrl: 'https://picsum.photos/400/675?random=9',
        width: 800,
        height: 1350,
        category: '风景',
        tags: ['风景', '海', '日落', '唯美'],
        likes: 534,
        views: 2450,
        downloads: 145,
        createTime: Date.now() - 28800000
      },
      {
        url: 'https://picsum.photos/800/1150?random=10',
        thumbUrl: 'https://picsum.photos/400/575?random=10',
        width: 800,
        height: 1150,
        category: '动漫',
        tags: ['动漫', '宫崎骏', '治愈'],
        likes: 412,
        views: 1890,
        downloads: 98,
        createTime: Date.now() - 32400000
      }
    ];

    // 批量添加示例数据
    const addPromises = sampleWallpapers.map(item => {
      return wallpaperCollection.add({ data: item });
    });

    await Promise.all(addPromises);

    return {
      success: true,
      message: '数据库初始化完成',
      count: sampleWallpapers.length
    };
  } catch (err) {
    return {
      success: false,
      error: err.message
    };
  }
};
