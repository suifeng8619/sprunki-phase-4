/**
 * Sprunki Phase 4 - 主 JavaScript 入口
 *
 * 功能：
 * - 导航菜单切换
 * - 平滑滚动
 * - 交互动画
 */

// ===============================================
// 导航菜单
// ===============================================

function initNavigation() {
  const navToggle = document.querySelector('.nav-toggle');
  const navMenu = document.querySelector('.nav-menu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
      navToggle.classList.toggle('active');
      navMenu.classList.toggle('active');
    });

    // 点击外部关闭菜单
    document.addEventListener('click', (e) => {
      if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
        navToggle.classList.remove('active');
        navMenu.classList.remove('active');
      }
    });
  }
}

// ===============================================
// 游戏启动
// ===============================================

function initGamePlayer() {
  // 全局 playGame 函数
  window.playGame = function() {
    const gameIntro = document.getElementById('game_intro');
    const gameIframe = document.getElementById('game_iframe');

    if (gameIntro && gameIframe) {
      // 淡出动画
      gameIntro.style.transition = 'opacity 0.3s ease';
      gameIntro.style.opacity = '0';

      setTimeout(() => {
        gameIntro.classList.add('hidden');
        gameIframe.classList.remove('hidden');

        // 淡入动画
        gameIframe.style.opacity = '0';
        gameIframe.style.transition = 'opacity 0.3s ease';
        requestAnimationFrame(() => {
          gameIframe.style.opacity = '1';
        });

        // 触发游戏启动事件
        window.dispatchEvent(new Event('gameStarted'));

        console.log('[Sprunki] Game started');
      }, 300);
    }
  };

  // 带音频激活的游戏启动
  window.playGameWithAudio = function() {
    window.playGame();

    // 激活音频上下文
    setTimeout(() => {
      activateAudioContext();
    }, 500);
  };
}

// ===============================================
// 音频激活
// ===============================================

function activateAudioContext() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      const audioContext = new AudioContext();

      if (audioContext.state === 'suspended') {
        audioContext.resume();
      }

      // 创建静音振荡器激活音频
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      gainNode.gain.value = 0;
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      oscillator.start();
      oscillator.stop(audioContext.currentTime + 0.1);

      console.log('[Sprunki] Audio context activated');
    }
  } catch (e) {
    console.warn('[Sprunki] Audio activation failed:', e);
  }
}

window.activateAudio = activateAudioContext;

// ===============================================
// 滚动功能
// ===============================================

function initScrollFunctions() {
  // 滚动到游戏区域
  window.scrollToGame = function() {
    const gameSection = document.getElementById('game_section');
    if (gameSection) {
      gameSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

      // 视觉反馈
      gameSection.style.transition = 'box-shadow 0.3s ease';
      gameSection.style.boxShadow = '0 0 30px rgba(168, 85, 247, 0.3)';
      setTimeout(() => {
        gameSection.style.boxShadow = '';
      }, 1000);
    }
  };

  // 滚动到评论区
  window.scrollToComments = function() {
    const commentsSection = document.querySelector('.comments-section');
    if (commentsSection) {
      commentsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };
}

// ===============================================
// 返回游戏按钮
// ===============================================

function initBackToGameButton() {
  const backToGameBtn = document.getElementById('backToGameBtn');
  const gameSection = document.getElementById('game_section');
  const commentsSection = document.querySelector('.comments-section');

  if (!backToGameBtn || !gameSection) return;

  let scrollTimeout;

  function toggleButton() {
    const gameSectionRect = gameSection.getBoundingClientRect();
    const commentsRect = commentsSection?.getBoundingClientRect();

    const gameNotVisible = gameSectionRect.bottom < 0;
    const commentsVisible = commentsRect ? commentsRect.top < window.innerHeight : false;

    if (gameNotVisible && commentsVisible) {
      backToGameBtn.classList.add('show');
    } else {
      backToGameBtn.classList.remove('show');
    }
  }

  window.addEventListener('scroll', () => {
    if (scrollTimeout) clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(toggleButton, 16);
  }, { passive: true });

  // 初始检查
  setTimeout(toggleButton, 100);
}

// ===============================================
// 游戏刷新
// ===============================================

window.refreshContentPageGame = function() {
  const gameIframe = document.getElementById('game_iframe');
  if (gameIframe) {
    console.log('[Sprunki] Refreshing game...');
    const currentSrc = gameIframe.src;
    gameIframe.src = '';

    setTimeout(() => {
      gameIframe.src = currentSrc;
      console.log('[Sprunki] Game refreshed');
    }, 100);
  }
};

// ===============================================
// Standalone 模式检测
// ===============================================

function isStandalone() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone ||
         document.referrer.includes('android-app://');
}

window.isStandalone = isStandalone;

// ===============================================
// 初始化
// ===============================================

function init() {
  initNavigation();
  initGamePlayer();
  initScrollFunctions();
  initBackToGameButton();

  console.log('[Sprunki] App initialized', {
    standalone: isStandalone()
  });
}

// DOM 加载完成后初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// 导出供外部使用
export {
  activateAudioContext,
  isStandalone
};
