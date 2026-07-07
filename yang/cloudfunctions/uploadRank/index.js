// 云函数：uploadRank - 上传闯关成绩到云数据库
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();

exports.main = async (event, context) => {
  const wxContext = cloud.getWXContext();
  const { name, maxLevel } = event;

  if (!name || typeof maxLevel !== 'number' || maxLevel <= 0) {
    return { success: false, message: '参数无效' };
  }

  try {
    // 查询当前用户是否已有记录
    const exist = await db.collection('rankings')
      .where({ _openid: wxContext.OPENID })
      .get();

    if (exist.data.length > 0) {
      // 已有记录，更新（只取更高的关卡）
      const old = exist.data[0];
      if (maxLevel > old.maxLevel) {
        await db.collection('rankings').doc(old._id).update({
          data: {
            name: name,
            maxLevel: maxLevel,
            updatedAt: db.serverDate(),
          },
        });
      }
    } else {
      // 新记录
      await db.collection('rankings').add({
        data: {
          _openid: wxContext.OPENID,
          name: name,
          maxLevel: maxLevel,
          createdAt: db.serverDate(),
          updatedAt: db.serverDate(),
        },
      });
    }

    // 获取 Top 10 排行返回
    const topList = await db.collection('rankings')
      .orderBy('maxLevel', 'desc')
      .limit(10)
      .get();

    return {
      success: true,
      rankings: topList.data.map(item => ({
        name: item.name,
        maxLevel: item.maxLevel,
      })),
    };
  } catch (err) {
    return { success: false, message: err.message };
  }
};
