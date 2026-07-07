/**
 * 音频管理器
 * 音乐：背景音乐（BGM），循环播放
 * 音效：游戏音效（点击、消除、胜利等），单次播放
 */
const audioManager = {
  _bgm: null,
  _sfxCache: {},

  /**
   * 获取 App 实例
   */
  _getApp() {
    return getApp();
  },

  /**
   * 获取 settings 状态
   */
  _getSettings() {
    const gd = this._getApp().globalData.gameData;
    if (!gd.settings) gd.settings = { musicOn: true, soundOn: true };
    return gd.settings;
  },

  /**
   * 初始化背景音乐
   * 音乐来自公共素材，如果没有则静默跳过
   */
  initBgm() {
    const settings = this._getSettings();
    if (this._bgm) {
      this._bgm.destroy();
      this._bgm = null;
    }
    if (!settings.musicOn) return;

    try {
      // 使用微信内置的背景音频，适合长时播放
      this._bgm = wx.createInnerAudioContext();
      this._bgm.src = '/assets/bgm.mp3';
      this._bgm.loop = true;
      this._bgm.volume = 0.3;
      this._bgm.autoplay = false;
      // 静默处理加载失败（音频文件可能不存在）
      this._bgm.onError(() => {
        // 音乐文件不存在，静默跳过
      });
    } catch (e) {
      // 创建失败，静默跳过
    }
  },

  /**
   * 播放背景音乐
   */
  playBgm() {
    const settings = this._getSettings();
    if (!settings.musicOn) return;
    if (!this._bgm) {
      this.initBgm();
    }
    if (this._bgm) {
      this._bgm.play();
    }
  },

  /**
   * 暂停背景音乐
   */
  pauseBgm() {
    if (this._bgm) {
      this._bgm.pause();
    }
  },

  /**
   * 停止并销毁背景音乐
   */
  stopBgm() {
    if (this._bgm) {
      this._bgm.stop();
      this._bgm.destroy();
      this._bgm = null;
    }
  },

  /**
   * 音乐开关切换
   */
  toggleMusic(on) {
    const app = this._getApp();
    const gd = app.globalData.gameData;
    if (!gd.settings) gd.settings = { musicOn: true, soundOn: true };
    gd.settings.musicOn = on;
    app.saveGameData();
    if (on) {
      this.initBgm();
      this.playBgm();
    } else {
      this.pauseBgm();
      this.stopBgm();
    }
  },

  /**
   * 音效开关切换
   */
  toggleSound(on) {
    const app = this._getApp();
    const gd = app.globalData.gameData;
    if (!gd.settings) gd.settings = { musicOn: true, soundOn: true };
    gd.settings.soundOn = on;
    app.saveGameData();
  },

  /**
   * 播放音效
   * @param {'click'|'match'|'win'|'lose'|'tool'|'error'} type 音效类型
   */
  playSfx(type) {
    const settings = this._getSettings();
    if (!settings.soundOn) return;

    const sfxMap = {
      click: '/assets/sfx-click.mp3',
      match: '/assets/sfx-match.mp3',
      win: '/assets/sfx-win.mp3',
      lose: '/assets/sfx-lose.mp3',
      tool: '/assets/sfx-tool.mp3',
      error: '/assets/sfx-error.mp3',
    };

    const src = sfxMap[type];
    if (!src) return;

    try {
      // 复用已缓存的音效实例
      if (!this._sfxCache[type]) {
        this._sfxCache[type] = wx.createInnerAudioContext();
        this._sfxCache[type].src = src;
        this._sfxCache[type].volume = 0.5;
        this._sfxCache[type].onError(() => {
          // 音频文件不存在，静默跳过
        });
      }
      const sfx = this._sfxCache[type];
      // 重置播放位置以支持快速连续播放
      sfx.seek(0);
      sfx.play();
    } catch (e) {
      // 播放失败，静默跳过
    }
  },

  /**
   * 销毁所有音频实例（页面卸载时调用）
   */
  destroy() {
    this.stopBgm();
    Object.values(this._sfxCache).forEach(sfx => {
      try { sfx.destroy(); } catch (e) {}
    });
    this._sfxCache = {};
  },
};

module.exports = audioManager;
