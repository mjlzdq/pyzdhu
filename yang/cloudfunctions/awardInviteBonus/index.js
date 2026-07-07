// 云函数：awardInviteBonus - 给邀请人发放积分奖励
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();

exports.main = async (event, context) => {
  const { inviterId, bonus } = event;

  if (!inviterId || typeof bonus !== 'number' || bonus <= 0) {
    return { success: false, message: '参数无效' };
  }

  try {
    // 查找邀请人的记录（通过 userId 字段）
    const userRes = await db.collection('users')
      .where({ userId: inviterId })
      .get();

    if (userRes.data.length === 0) {
      // 邀请人没有在云端创建用户记录，记录待领取奖励
      return { success: false, message: '用户不存在', needLocalFallback: true };
    }

    const user = userRes.data[0];
    const newPoints = (user.points || 0) + bonus;

    // 更新邀请人积分
    await db.collection('users').doc(user._id).update({
      data: {
        points: newPoints,
        updatedAt: db.serverDate(),
      },
    });

    return {
      success: true,
      newPoints: newPoints,
      bonus: bonus,
    };
  } catch (err) {
    return { success: false, message: err.message, needLocalFallback: true };
  }
};
