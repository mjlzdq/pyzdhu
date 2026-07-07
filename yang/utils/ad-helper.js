/**
 * 广告辅助工具
 *
 * 广告类型说明：
 * 1. 激励视频广告（Rewarded Video Ad）— 用户主动点击获取道具/积分时触发，看完才给奖励
 * 2. 原生模板广告（ad-custom）— 页面底部固定展示，对标 Banner
 * 3. 插屏广告（Interstitial Ad）— 游戏结束返回首页时展示
 *
 * 使用方法：
 *   const adHelper = require('../../utils/ad-helper');
 *
 *   // 激励视频：看广告获取奖励（道具/积分/签到翻倍共用一个广告位）
 *   adHelper.showRewardedVideo({ onRewarded: callback });
 *
 *   // 插屏广告
 *   adHelper.showInterstitialAd(callback);
 *
 *   // 原生模板广告：在 WXML 中使用 <ad-custom unit-id="{{AD_UNITS.CUSTOM_BANNER}}" .../>
 */

// ============================================================
// 广告位 ID 配置
// ============================================================
const AD_UNITS = {
  // 激励视频 - 道具获取 / 积分获取 / 签到翻倍（共用同一广告位）
  REWARDED_VIDEO: 'adunit-2661ef8bf9c18ac9',

  // 原生模板广告 - 页面底部（对标 Banner）
  CUSTOM_BANNER: 'adunit-3a4d661c81f6ed2f',

  // 插屏广告
  INTERSTITIAL: 'adunit-7e601b550bb70ecd',
};

// ============================================================
// 激励视频广告（全局单例，避免重复创建实例）
// ============================================================

let rewardedVideoAd = null;
let rewardedCallbacks = null;

/**
 * 播放激励视频广告
 * @param {object} callbacks
 *   - onRewarded: 广告看完 → 发奖励
 *   - onSkipped: 广告未看完
 *   - onError: 广告加载/播放失败
 */
function showRewardedVideo(callbacks = {}) {
  if (!wx.createRewardedVideoAd) {
    wx.showToast({ title: '当前版本不支持广告', icon: 'none' });
    return;
  }

  rewardedCallbacks = callbacks;
  const { onRewarded, onSkipped, onError } = callbacks;

  // 复用单例，只创建一次
  if (!rewardedVideoAd) {
    rewardedVideoAd = wx.createRewardedVideoAd({
      adUnitId: AD_UNITS.REWARDED_VIDEO,
    });

    rewardedVideoAd.onLoad(() => {
      console.log('[激励视频] 加载成功');
    });

    rewardedVideoAd.onError((err) => {
      console.error('[激励视频] 加载错误:', err);
      if (rewardedCallbacks && rewardedCallbacks.onError) {
        rewardedCallbacks.onError();
      } else {
        wx.showToast({ title: '广告加载失败，请稍后再试', icon: 'none' });
      }
    });

    rewardedVideoAd.onClose((res) => {
      if (res && res.isEnded) {
        if (rewardedCallbacks && rewardedCallbacks.onRewarded) {
          rewardedCallbacks.onRewarded();
        }
      } else {
        if (rewardedCallbacks && rewardedCallbacks.onSkipped) {
          rewardedCallbacks.onSkipped();
        } else {
          wx.showToast({ title: '需要看完广告才能获得奖励哦~', icon: 'none' });
        }
      }
    });
  } else {
    // 更新回调（复用已有实例）
    rewardedCallbacks = callbacks;
  }

  // 显示广告，失败时重试
  rewardedVideoAd.show().catch(() => {
    rewardedVideoAd.load()
      .then(() => rewardedVideoAd.show())
      .catch((err) => {
        console.error('[激励视频] 显示失败:', err);
        if (rewardedCallbacks && rewardedCallbacks.onError) {
          rewardedCallbacks.onError();
        } else {
          wx.showToast({ title: '广告播放失败，请稍后再试', icon: 'none' });
        }
      });
  });
}

// ============================================================
// 插屏广告
// ============================================================

/**
 * 显示插屏广告
 * 适合在游戏结束返回首页、关卡切换等自然停顿场景调用
 * @param {function} onClose - 广告关闭后的回调（无论是否看完）
 */
function showInterstitialAd(onClose) {
  if (!wx.createInterstitialAd) {
    if (onClose) onClose();
    return;
  }

  const interstitialAd = wx.createInterstitialAd({
    adUnitId: AD_UNITS.INTERSTITIAL,
  });

  interstitialAd.onLoad(() => {
    console.log('[插屏广告] 加载成功');
  });

  interstitialAd.onError((err) => {
    console.error('[插屏广告] 加载失败:', err);
    if (onClose) onClose();
  });

  interstitialAd.onClose(() => {
    console.log('[插屏广告] 关闭');
    if (onClose) onClose();
  });

  interstitialAd.show().catch((err) => {
    console.error('[插屏广告] 显示失败:', err);
    if (onClose) onClose();
  });
}

module.exports = {
  AD_UNITS,
  showRewardedVideo,
  showInterstitialAd,
};
