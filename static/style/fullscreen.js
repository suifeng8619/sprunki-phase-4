(function () {
    // 防抖函数：限制一个函数在一定时间内只能触发一次
    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    /**
     * 检测是否为iOS设备
     * @returns {boolean} 如果是iOS设备返回true
     */
    function isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    }

    // 全局变量
    let gameStarted = false; // 标记游戏是否已启动
    let isIOSFullscreen = false; // 记录是否处于iOS全屏状态

    // 主函数：初始化全屏功能
    function initFullscreen() {
        // 创建全屏按钮并添加到游戏容器中
        const gameContainer = document.querySelector('.game-container');
        if (!gameContainer) {
            console.error('Fullscreen: Game container not found.');
            return;
        }

        // 创建进入全屏按钮
        const fullscreenBtn = document.createElement('button');
        fullscreenBtn.id = 'fullscreen-btn';
        fullscreenBtn.type = 'button';
        fullscreenBtn.title = 'Enter Fullscreen';
        fullscreenBtn.className = 'fullscreen-button';
        fullscreenBtn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 70 70" xmlns="http://www.w3.org/2000/svg">
              <rect x="5" y="5" width="60" height="60" fill="none" stroke="#fff" stroke-width="6" rx="3"/>
              <g fill="none" stroke="#fff" stroke-width="4" stroke-linecap="square">
                <path d="M15 25 L15 15 L25 15"/>
                <path d="M55 25 L55 15 L45 15"/>
                <path d="M15 45 L15 55 L25 55"/>
                <path d="M55 45 L55 55 L45 55"/>
              </g>
            </svg>
        `;
        
        // 创建退出全屏按钮
        const exitFullscreenBtn = document.createElement('button');
        exitFullscreenBtn.id = 'exit-fullscreen-btn';
        exitFullscreenBtn.type = 'button';
        exitFullscreenBtn.title = 'Exit Fullscreen';
        exitFullscreenBtn.className = 'exit-fullscreen-button';
        exitFullscreenBtn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 70 70" xmlns="http://www.w3.org/2000/svg">
              <rect x="5" y="5" width="60" height="60" fill="none" stroke="#fff" stroke-width="6" rx="3"/>
              <g fill="none" stroke="#fff" stroke-width="4" stroke-linecap="square">
                <path d="M25 15 L25 25 L15 25"/>
                <path d="M45 15 L45 25 L55 25"/>
                <path d="M25 55 L25 45 L15 45"/>
                <path d="M45 55 L45 45 L55 45"/>
              </g>
            </svg>
        `;

        // 创建iOS全屏遮罩层
        const iosFullscreenLayer = document.createElement('div');
        iosFullscreenLayer.id = 'ios_fullscreen_layer';
        iosFullscreenLayer.style.display = 'none';
        iosFullscreenLayer.className = 'fixed inset-0 z-[9999] bg-black flex items-center justify-center';
        iosFullscreenLayer.setAttribute('aria-label', 'iOS伪全屏');
        iosFullscreenLayer.setAttribute('role', 'dialog');

        // 创建横屏提示图标
        const iosLandscapeTip = document.createElement('div');
        iosLandscapeTip.id = 'ios_landscape_tip';
        iosLandscapeTip.className = 'absolute top-4 left-4 bg-black/50 px-3 py-1 rounded pointer-events-none select-none z-10 flex items-center justify-center';
        iosLandscapeTip.style.cssText = 'max-width: 70vw; display: none; height:40px; width:40px;';
        iosLandscapeTip.innerHTML = `
            <svg width="32" height="32" viewBox="0 0 48 48" fill="none" aria-label="请横屏" focusable="false">
                <rect x="8" y="16" width="32" height="16" rx="3" fill="#fff" fill-opacity="0.8"/>
                <rect x="8" y="16" width="32" height="16" rx="3" stroke="#2563eb" stroke-width="2"/>
                <path d="M16 12v4M32 12v4" stroke="#2563eb" stroke-width="2" stroke-linecap="round"/>
                <path d="M16 36v-4M32 36v-4" stroke="#2563eb" stroke-width="2" stroke-linecap="round"/>
                <path d="M4 24h4M40 24h4" stroke="#2563eb" stroke-width="2" stroke-linecap="round"/>
            </svg>
        `;

        iosFullscreenLayer.appendChild(iosLandscapeTip);
        document.body.appendChild(iosFullscreenLayer);

        // 创建iOS全屏退出按钮
        const iosExitBtn = document.createElement('button');
        iosExitBtn.id = 'ios_fullscreen_exit_btn';
        iosExitBtn.onclick = () => exitIOSFullscreen();
        iosExitBtn.className = 'fixed top-4 right-4 bg-white text-black rounded-full w-12 h-12 shadow-lg z-[10001] items-center justify-center';
        iosExitBtn.setAttribute('aria-label', '退出全屏');
        iosExitBtn.style.cssText = 'font-size: 2rem; line-height: 1; display: none;';
        iosExitBtn.innerHTML = '×';
        document.body.appendChild(iosExitBtn);
        
        // 将按钮添加到游戏容器中
        gameContainer.appendChild(fullscreenBtn);
        gameContainer.appendChild(exitFullscreenBtn);

        // 获取 DOM 元素的引用
        const elements = {
            wrapper: document.getElementById('game_section'),
            container: gameContainer,
            iframe: document.getElementById('game_iframe'),
            fullscreenBtn: fullscreenBtn,
            exitFullscreenBtn: exitFullscreenBtn,
            gameIntro: document.getElementById('game_intro'),
            iosLayer: iosFullscreenLayer,
            iosExitBtn: iosExitBtn,
            iosLandscapeTip: iosLandscapeTip
        };

        // 检查关键元素是否存在
        for (const key in elements) {
            if (!elements[key]) {
                console.error(`Fullscreen: Element '${key}' not found.`);
                return;
            }
        }

        // 状态变量
        let isInFullscreen = false;
        let isTransitioning = false;
        let originalMetaContent = null;
        let originalStyles = null;

        /**
         * 进入iOS全屏模式
         */
        function enterIOSFullscreen() {
            const iframe = elements.iframe;
            const iosLayer = elements.iosLayer;
            const exitBtn = elements.iosExitBtn;
            const gameIntro = elements.gameIntro;

            // 如果游戏未运行，先运行游戏
            if (!gameStarted) {
                runGameIOS();
            }

            // 为iframe添加全屏样式类
            iframe.classList.add('ios-fullscreen');

            // 将iframe移动到iOS全屏层内部，确保它在遮罩层之上
            iosLayer.appendChild(iframe);

            // 显示iOS全屏层和退出按钮
            iosLayer.style.display = 'flex';
            exitBtn.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // 防止页面滚动
            isIOSFullscreen = true;

            // 请求屏幕方向为横屏（如果设备支持）
            if (screen.orientation && screen.orientation.lock) {
                screen.orientation.lock('landscape').catch(e => {
                    console.log('屏幕方向锁定失败:', e);
                });
            }

            // 显示横屏图标提示，3秒后消失
            const tip = elements.iosLandscapeTip;
            tip.style.display = 'flex';
            setTimeout(() => {
                tip.style.display = 'none';
            }, 3000);

            // 添加全屏样式类
            elements.wrapper.classList.add('fullscreen');
        }

        /**
         * 退出iOS全屏模式
         */
        function exitIOSFullscreen() {
            const iframe = elements.iframe;
            const iosLayer = elements.iosLayer;
            const exitBtn = elements.iosExitBtn;

            // 移除全屏样式类
            iframe.classList.remove('ios-fullscreen');

            // 将iframe移回原始容器
            elements.container.appendChild(iframe);

            // 隐藏全屏层和退出按钮
            iosLayer.style.display = 'none';
            exitBtn.style.display = 'none';
            document.body.style.overflow = ''; // 恢复页面滚动
            isIOSFullscreen = false;

            // 解除屏幕方向锁定
            if (screen.orientation && screen.orientation.unlock) {
                screen.orientation.unlock();
            }

            // 移除全屏样式类
            elements.wrapper.classList.remove('fullscreen');

            // 如果游戏没有启动，恢复游戏介绍显示
            if (!gameStarted) {
                elements.gameIntro.classList.remove('hidden');
                elements.iframe.classList.add('hidden');
            }
        }

        /**
         * iOS设备上运行游戏
         */
        function runGameIOS() {
            const iframe = elements.iframe;
            const gameIntro = elements.gameIntro;

            if (!gameStarted) {
                gameStarted = true;
                iframe.classList.remove("hidden");
                gameIntro.classList.add("hidden");
                
                // 触发游戏启动事件
                window.dispatchEvent(new Event('gameStarted'));
                
                // iOS 设备上也需要尝试激活音频
                setTimeout(() => {
                    activateIOSAudio();
                }, 500);
            }
        }
        
        /**
         * iOS 特定的音频激活函数
         */
        function activateIOSAudio() {
            try {
                // 发送消息给 iframe
                const gameIframe = document.getElementById('game_iframe');
                if (gameIframe) {
                    gameIframe.contentWindow.postMessage({
                        type: 'ENABLE_AUDIO',
                        action: 'ios_user_interaction'
                    }, '*');
                }
                
                // 在 iOS 上创建音频上下文
                if (window.webkitAudioContext) {
                    const audioContext = new webkitAudioContext();
                    
                    // 创建一个静音源来激活音频
                    const buffer = audioContext.createBuffer(1, 1, 22050);
                    const source = audioContext.createBufferSource();
                    source.buffer = buffer;
                    source.connect(audioContext.destination);
                    source.start(0);
                    
                    // 如果音频上下文被暂停，恢复它
                    if (audioContext.state === 'suspended') {
                        audioContext.resume();
                    }
                }
                
                console.log('iOS audio activation attempted');
            } catch (e) {
                console.log('iOS audio activation error:', e);
            }
        }

        // 函数：更新 viewport meta 标签
        function updateViewport(isFullscreenMode) {
            const viewport = document.querySelector('meta[name="viewport"]');
            if (!viewport) {
                console.warn("Fullscreen: Viewport meta tag not found.");
                return;
            }

            if (isFullscreenMode) {
                if (originalMetaContent === null) {
                    originalMetaContent = viewport.content;
                }
                viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
            } else if (originalMetaContent !== null) {
                viewport.content = originalMetaContent;
            }
        }

        // 函数：保存元素的原始内联样式
        function saveOriginalStyles() {
            originalStyles = {
                wrapper: {
                    position: elements.wrapper.style.position,
                    width: elements.wrapper.style.width,
                    height: elements.wrapper.style.height,
                    maxWidth: elements.wrapper.style.maxWidth,
                    maxHeight: elements.wrapper.style.maxHeight,
                    zIndex: elements.wrapper.style.zIndex,
                    top: elements.wrapper.style.top,
                    left: elements.wrapper.style.left,
                    padding: elements.wrapper.style.padding,
                    paddingTop: elements.wrapper.style.paddingTop,
                    margin: elements.wrapper.style.margin,
                    backgroundColor: elements.wrapper.style.backgroundColor,
                    borderRadius: elements.wrapper.style.borderRadius,
                    minHeight: elements.wrapper.style.minHeight,
                    display: elements.wrapper.style.display,
                    flexDirection: elements.wrapper.style.flexDirection,
                    justifyContent: elements.wrapper.style.justifyContent,
                    alignItems: elements.wrapper.style.alignItems,
                    animation: elements.wrapper.style.animation,
                    backgroundSize: elements.wrapper.style.backgroundSize,
                },
                container: {
                    position: elements.container.style.position,
                    width: elements.container.style.width,
                    height: elements.container.style.height,
                    maxWidth: elements.container.style.maxWidth,
                    maxHeight: elements.container.style.maxHeight,
                    top: elements.container.style.top,
                    left: elements.container.style.left,
                    margin: elements.container.style.margin,
                    padding: elements.container.style.padding,
                    borderRadius: elements.container.style.borderRadius,
                    aspectRatio: elements.container.style.aspectRatio,
                    minHeight: elements.container.style.minHeight,
                    background: elements.container.style.background,
                },
                iframe: {
                    position: elements.iframe.style.position,
                    width: elements.iframe.style.width,
                    height: elements.iframe.style.height,
                    maxWidth: elements.iframe.style.maxWidth,
                    maxHeight: elements.iframe.style.maxHeight,
                    top: elements.iframe.style.top,
                    left: elements.iframe.style.left,
                    border: elements.iframe.style.border,
                    borderRadius: elements.iframe.style.borderRadius,
                    margin: elements.iframe.style.margin,
                    padding: elements.iframe.style.padding,
                    zIndex: elements.iframe.style.zIndex,
                    display: elements.iframe.style.display,
                },
                body: {
                    overflow: document.body.style.overflow,
                    position: document.body.style.position,
                    width: document.body.style.width,
                    height: document.body.style.height,
                }
            };
        }

        // 函数：应用全屏模式的样式 (伪全屏)
        function applyFullscreenStyles() {
            if (originalStyles === null) {
                saveOriginalStyles();
            }

            updateViewport(true);

            // 隐藏游戏介绍
            elements.gameIntro.classList.add('hidden');
            // 显示游戏iframe
            elements.iframe.classList.remove('hidden');

            // 设置wrapper样式
            Object.assign(elements.wrapper.style, {
                position: 'fixed',
                top: '0',
                left: '0',
                width: '100vw',
                height: '100vh',
                maxWidth: 'none',
                maxHeight: 'none',
                paddingTop: '0',
                padding: '0',
                margin: '0',
                zIndex: '2147483647',
                backgroundColor: '#000',
                borderRadius: '0',
                minHeight: 'unset',
                display: 'block',
                flexDirection: 'unset',
                justifyContent: 'unset',
                alignItems: 'unset',
                animation: 'none',
                backgroundSize: 'unset'
            });

            // 设置container样式
            Object.assign(elements.container.style, {
                position: 'absolute',
                top: '0',
                left: '0',
                width: '100vw',
                height: '100vh',
                maxWidth: 'none',
                maxHeight: 'none',
                margin: '0',
                padding: '0',
                borderRadius: '0',
                aspectRatio: 'unset',
                minHeight: 'unset',
                background: 'black'
            });

            // 设置iframe样式
            Object.assign(elements.iframe.style, {
                position: 'absolute',
                top: '0',
                left: '0',
                width: '100vw',
                height: '100vh',
                maxWidth: 'none',
                maxHeight: 'none',
                border: 'none',
                borderRadius: '0',
                margin: '0',
                padding: '0',
                zIndex: '10000',
                display: 'block'
            });

            // 设置body样式
            Object.assign(document.body.style, {
                overflow: 'hidden',
                position: 'fixed',
                width: '100%',
                height: '100%',
            });
            
            // 添加全屏样式类
            elements.wrapper.classList.add('fullscreen');

            if (screen.orientation && screen.orientation.lock) {
                screen.orientation.lock('landscape').catch((err) => {
                    console.warn('Screen orientation lock failed:', err.message);
                });
            }
        }

        // 函数：退出全屏时恢复原始样式
        function restoreOriginalStyles() {
            if (!originalStyles) return;

            updateViewport(false);

            // 检查是否在原生全屏模式
            const isNativeFullscreen = !!(
                document.fullscreenElement ||
                document.webkitFullscreenElement ||
                document.mozFullScreenElement ||
                document.msFullscreenElement
            );

            // 只有在非原生全屏状态下才恢复游戏介绍显示
            if (!isNativeFullscreen && !gameStarted) {
                elements.gameIntro.classList.remove('hidden');
                elements.iframe.classList.add('hidden');
            }

            // 恢复wrapper样式
            Object.assign(elements.wrapper.style, originalStyles.wrapper);
            
            // 清除可能的内联样式
            elements.wrapper.style.maxWidth = originalStyles.wrapper.maxWidth || '';
            elements.wrapper.style.maxHeight = originalStyles.wrapper.maxHeight || '';
            elements.wrapper.style.padding = originalStyles.wrapper.padding || '';
            elements.wrapper.style.margin = originalStyles.wrapper.margin || '';
            elements.wrapper.style.borderRadius = originalStyles.wrapper.borderRadius || '';
            elements.wrapper.style.minHeight = originalStyles.wrapper.minHeight || '';
            elements.wrapper.style.display = originalStyles.wrapper.display || '';
            elements.wrapper.style.flexDirection = originalStyles.wrapper.flexDirection || '';
            elements.wrapper.style.justifyContent = originalStyles.wrapper.justifyContent || '';
            elements.wrapper.style.alignItems = originalStyles.wrapper.alignItems || '';
            elements.wrapper.style.animation = originalStyles.wrapper.animation || '';
            elements.wrapper.style.backgroundSize = originalStyles.wrapper.backgroundSize || '';

            // 恢复container样式
            Object.assign(elements.container.style, originalStyles.container);
            
            // 清除container的内联样式
            elements.container.style.maxWidth = originalStyles.container.maxWidth || '';
            elements.container.style.maxHeight = originalStyles.container.maxHeight || '';
            elements.container.style.margin = originalStyles.container.margin || '';
            elements.container.style.padding = originalStyles.container.padding || '';
            elements.container.style.borderRadius = originalStyles.container.borderRadius || '';
            elements.container.style.aspectRatio = originalStyles.container.aspectRatio || '';
            elements.container.style.minHeight = originalStyles.container.minHeight || '';
            elements.container.style.background = originalStyles.container.background || '';

            // 恢复iframe样式
            elements.iframe.style.maxWidth = originalStyles.iframe?.maxWidth || '';
            elements.iframe.style.maxHeight = originalStyles.iframe?.maxHeight || '';
            elements.iframe.style.border = originalStyles.iframe?.border || '';
            elements.iframe.style.borderRadius = originalStyles.iframe?.borderRadius || '';
            elements.iframe.style.margin = originalStyles.iframe?.margin || '';
            elements.iframe.style.padding = originalStyles.iframe?.padding || '';
            elements.iframe.style.zIndex = originalStyles.iframe?.zIndex || '';
            elements.iframe.style.display = originalStyles.iframe?.display || '';

            // 恢复body样式
            Object.assign(document.body.style, originalStyles.body);
            
            // 移除全屏样式类
            elements.wrapper.classList.remove('fullscreen');

            if (screen.orientation && screen.orientation.unlock) {
                screen.orientation.unlock();
            }
        }

        /**
         * 切换全屏模式（智能判断设备类型）
         */
        function toggleFullscreen() {
            if (isIOS()) {
                // iOS设备使用自定义全屏模式
                if (isIOSFullscreen) {
                    exitIOSFullscreen();
                } else {
                    enterIOSFullscreen();
                }
            } else {
                // 其他设备使用标准伪全屏
                if (isInFullscreen) {
                    exitFullscreen();
                } else {
                    enterFullscreen();
                }
            }
        }

        // 进入全屏（非iOS设备）
        const enterFullscreen = debounce(function (e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }

            if (isTransitioning || isInFullscreen) return;
            isTransitioning = true;

            try {
                applyFullscreenStyles();
                isInFullscreen = true;
            } catch (error) {
                console.error('Fullscreen enter error:', error);
            } finally {
                // 短暂延迟后重置过渡标志
                setTimeout(() => { isTransitioning = false; }, 50);
            }
        }, 250);
        
        // 退出全屏（非iOS设备）
        const exitFullscreen = debounce(function (e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }

            if (isTransitioning || !isInFullscreen) return;
            isTransitioning = true;

            try {
                restoreOriginalStyles();
                isInFullscreen = false;
            } catch (error) {
                console.error('Fullscreen exit error:', error);
            } finally {
                // 短暂延迟后重置过渡标志
                setTimeout(() => { isTransitioning = false; }, 50);
            }
        }, 250);

        // 事件监听
        elements.fullscreenBtn.addEventListener('click', toggleFullscreen);
        elements.fullscreenBtn.addEventListener('touchend', toggleFullscreen, { passive: false });
        
        elements.exitFullscreenBtn.addEventListener('click', toggleFullscreen);
        elements.exitFullscreenBtn.addEventListener('touchend', toggleFullscreen, { passive: false });

        window.addEventListener('orientationchange', debounce(() => {
            if (isIOSFullscreen) {
                // iOS设备方向变化时重新调整全屏
                setTimeout(() => {
                    if (isIOSFullscreen) {
                        enterIOSFullscreen();
                    }
                }, 150);
            } else if (isInFullscreen) {
                setTimeout(applyFullscreenStyles, 150);
            }
        }, 250));

        window.addEventListener('popstate', () => {
            if (isIOSFullscreen) {
                exitIOSFullscreen();
            } else if (isInFullscreen) {
                exitFullscreen();
            }
        });

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                if (isIOSFullscreen) {
                    exitIOSFullscreen();
                } else if (isInFullscreen) {
                    exitFullscreen();
                }
            }
        });

        // 监听全屏状态变化
        document.addEventListener('fullscreenchange', () => {
            // 检查如果退出了原生全屏但在伪全屏状态，需要保持伪全屏
            if (isInFullscreen && !document.fullscreenElement && !isIOS()) {
                applyFullscreenStyles();
            }
        });

        // 初始隐藏全屏按钮，只有在游戏启动时才显示
        fullscreenBtn.style.display = 'none';
        exitFullscreenBtn.style.display = 'none';

        // 监听游戏启动事件
        window.addEventListener('gameStarted', function() {
            fullscreenBtn.style.display = 'flex';
            exitFullscreenBtn.style.display = 'none';
            gameStarted = true;
        });

        // 全局公开游戏启动函数
        window.playGame = function() {
            const gameIntro = document.getElementById('game_intro');
            const gameIframe = document.getElementById('game_iframe');
            
            if (gameIntro && gameIframe) {
                if (isIOS()) {
                    runGameIOS();
                } else {
                    // 显示游戏界面
                    gameIntro.classList.add('hidden');
                    gameIframe.classList.remove('hidden');
                    fullscreenBtn.style.display = 'flex';
                    
                    // 标记游戏已启动
                    gameStarted = true;
                    
                    // 触发游戏启动事件
                    window.dispatchEvent(new Event('gameStarted'));
                    
                    // 尝试激活 iframe 中的音频上下文
                    // 这需要用户交互，所以在 playGame 被点击时执行
                    try {
                        // 发送消息给 iframe，通知它可以启动音频
                        gameIframe.contentWindow.postMessage({
                            type: 'ENABLE_AUDIO',
                            action: 'user_interaction'
                        }, '*');
                        
                        // 某些游戏可能需要模拟点击来激活音频
                        // 延迟一小段时间确保 iframe 完全加载
                        setTimeout(() => {
                            try {
                                // 尝试在 iframe 内部创建一个临时的音频上下文来激活音频
                                const iframeDoc = gameIframe.contentDocument || gameIframe.contentWindow.document;
                                if (iframeDoc) {
                                    // 创建并立即播放一个静音的音频来激活音频上下文
                                    const silentAudio = iframeDoc.createElement('audio');
                                    silentAudio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE';
                                    silentAudio.volume = 0.1;
                                    silentAudio.play().catch(() => {
                                        // 静音播放失败是正常的，不需要处理
                                    });
                                }
                            } catch (e) {
                                // iframe 跨域访问限制，这是正常的
                                console.log('Audio activation attempted via postMessage');
                            }
                        }, 500);
                    } catch (e) {
                        console.log('Audio activation failed:', e);
                    }
                }
            }
        };

        // 全局暴露iOS全屏函数供外部调用
        window.enterIOSFullscreen = enterIOSFullscreen;
        window.exitIOSFullscreen = exitIOSFullscreen;
        window.isIOS = isIOS;
    }

    // 添加iOS全屏的CSS样式
    const iosStyles = document.createElement('style');
    iosStyles.textContent = `
        /* iOS全屏遮罩层样式 */
        #ios_fullscreen_layer {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background-color: black !important;
            z-index: 9999 !important;
        }

        /* iOS 全屏模式下的iframe基础样式 */
        #game_iframe.ios-fullscreen {
            position: absolute !important;
            z-index: 10001 !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
            background-color: black !important;
        }

        /* 横屏设备样式 */
        @media (orientation: landscape) {
            #game_iframe.ios-fullscreen {
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                transform: none !important;
            }
        }

        /* 竖屏设备样式 */
        @media (orientation: portrait) {
            #game_iframe.ios-fullscreen {
                /* 在屏幕中心旋转90度 */
                top: 50% !important;
                left: 50% !important;
                width: 100vh !important; /* 使用视口高度作为宽度 */
                height: 100vw !important; /* 使用视口宽度作为高度 */
                transform: translate(-50%, -50%) rotate(90deg) !important;
                transform-origin: center center !important;
            }

            /* 竖屏模式下确保关闭按钮在正确位置 */
            #ios_fullscreen_exit_btn {
                top: 20px !important;
                right: 20px !important;
                z-index: 10002 !important;
            }
        }
    `;
    document.head.appendChild(iosStyles);

    // 初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFullscreen);
    } else {
        initFullscreen();
    }
})(); 