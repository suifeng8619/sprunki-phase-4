(function() {
    /**
     * 检测是否为iOS设备
     * @returns {boolean} 如果是iOS设备返回true
     */
    function isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    }

    // 初始化函数
    function initNativeFullscreen() {
        // 如果是iOS设备，跳过原生全屏初始化，因为iOS不支持原生全屏API
        if (isIOS()) {
            console.log('iOS device detected, skipping native fullscreen initialization');
            return;
        }

        // 创建原生全屏按钮并添加到游戏容器中
        const gameContainer = document.querySelector('.game-container');
        if (!gameContainer) {
            console.error('Native Fullscreen: Game container not found.');
            return;
        }

        // 创建原生进入全屏按钮
        const nativeFullscreenBtn = document.createElement('button');
        nativeFullscreenBtn.id = 'native-fullscreen-btn';
        nativeFullscreenBtn.type = 'button';
        nativeFullscreenBtn.title = 'Native Fullscreen';
        nativeFullscreenBtn.className = 'native-fullscreen-button';
        nativeFullscreenBtn.innerHTML = `
            <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <g fill="none" stroke="#fff" stroke-width="12" stroke-linecap="square">
                    <path d="M20 35 L20 20 L35 20"/>
                    <path d="M80 35 L80 20 L65 20"/>
                    <path d="M20 65 L20 80 L35 80"/>
                    <path d="M80 65 L80 80 L65 80"/>
                </g>
            </svg>
        `;
        
        // 创建原生退出全屏按钮
        const nativeExitFullscreenBtn = document.createElement('button');
        nativeExitFullscreenBtn.id = 'native-exit-fullscreen-btn';
        nativeExitFullscreenBtn.type = 'button';
        nativeExitFullscreenBtn.title = 'Exit Native Fullscreen';
        nativeExitFullscreenBtn.className = 'native-exit-fullscreen-button';
        nativeExitFullscreenBtn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
              <g fill="none" stroke="#fff" stroke-width="12" stroke-linecap="square">
                <path d="M35 20 L35 35 L20 35"/>
                <path d="M65 20 L65 35 L80 35"/>
                <path d="M35 80 L35 65 L20 65"/> 
                <path d="M65 80 L65 65 L80 65"/>
              </g>
            </svg>
        `;
        
        // 将按钮添加到游戏容器中
        gameContainer.appendChild(nativeFullscreenBtn);
        gameContainer.appendChild(nativeExitFullscreenBtn);

        // 获取 DOM 元素的引用
        const elements = {
            wrapper: document.getElementById('game_section'),
            container: gameContainer,
            iframe: document.getElementById('game_iframe'),
            nativeFullscreenBtn: nativeFullscreenBtn,
            nativeExitFullscreenBtn: nativeExitFullscreenBtn,
            gameIntro: document.getElementById('game_intro')
        };

        // 检查关键元素是否存在
        for (const key in elements) {
            if (!elements[key]) {
                console.error(`Native Fullscreen: Element '${key}' not found.`);
                return;
            }
        }

        // 状态变量
        let isInNativeFullscreen = false;

        // 检查原生全屏API是否可用
        function isFullscreenAPIAvailable() {
            return !!(
                document.fullscreenEnabled ||
                document.webkitFullscreenEnabled ||
                document.mozFullScreenEnabled ||
                document.msFullscreenEnabled
            );
        }

        // 进入原生全屏
        function enterNativeFullscreen() {
            if (!isFullscreenAPIAvailable()) {
                console.warn('Native fullscreen API is not available in this browser.');
                return false;
            }

            // 确保游戏iframe可见
            elements.gameIntro.classList.add('hidden');
            elements.iframe.classList.remove('hidden');

            // 请求进入全屏
            const targetElement = elements.wrapper;
            if (targetElement.requestFullscreen) {
                targetElement.requestFullscreen();
            } else if (targetElement.webkitRequestFullscreen) {
                targetElement.webkitRequestFullscreen();
            } else if (targetElement.mozRequestFullScreen) {
                targetElement.mozRequestFullScreen();
            } else if (targetElement.msRequestFullscreen) {
                targetElement.msRequestFullscreen();
            } else {
                return false;
            }
            
            // 添加全屏样式类
            elements.wrapper.classList.add('fullscreen');
            
            return true;
        }

        // 退出原生全屏
        function exitNativeFullscreen() {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            
            // 移除全屏样式类
            elements.wrapper.classList.remove('fullscreen');
        }

        // 全屏状态变化处理函数
        function handleFullscreenChange() {
            isInNativeFullscreen = !!(
                document.fullscreenElement ||
                document.webkitFullscreenElement ||
                document.mozFullScreenElement ||
                document.msFullscreenElement
            );
            
            if (isInNativeFullscreen) {
                // 确保添加fullscreen类
                elements.wrapper.classList.add('fullscreen');
            } else {
                // 移除fullscreen类
                elements.wrapper.classList.remove('fullscreen');
                
                // 如果游戏没有启动（处于介绍状态），恢复介绍页面
                if (!window.gameStarted) {
                    elements.gameIntro.classList.remove('hidden');
                    elements.iframe.classList.add('hidden');
                }
            }
        }

        // 添加事件监听器
        elements.nativeFullscreenBtn.addEventListener('click', function(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            enterNativeFullscreen();
        });
        
        elements.nativeFullscreenBtn.addEventListener('touchend', function(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            enterNativeFullscreen();
        }, { passive: false });
        
        elements.nativeExitFullscreenBtn.addEventListener('click', function(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            exitNativeFullscreen();
        });
        
        elements.nativeExitFullscreenBtn.addEventListener('touchend', function(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            exitNativeFullscreen();
        }, { passive: false });

        // 监听全屏状态变化
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.addEventListener('mozfullscreenchange', handleFullscreenChange);
        document.addEventListener('MSFullscreenChange', handleFullscreenChange);

        // 初始隐藏原生全屏按钮，只有在游戏启动时才显示
        nativeFullscreenBtn.style.display = 'none';
        nativeExitFullscreenBtn.style.display = 'none';

        // 监听游戏启动事件
        window.addEventListener('gameStarted', function() {
            nativeFullscreenBtn.style.display = 'flex';
            nativeExitFullscreenBtn.style.display = 'none'; // 确保退出按钮保持隐藏状态
        });

        // 如果浏览器不支持原生全屏API，则隐藏按钮
        if (!isFullscreenAPIAvailable()) {
            nativeFullscreenBtn.style.display = 'none';
            nativeExitFullscreenBtn.style.display = 'none';
        }
    }

    // 初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNativeFullscreen);
    } else {
        initNativeFullscreen();
    }
})(); 