/**
 * 游戏状态栏功能模块
 * 处理评论跳转和全屏按钮集成（包括iOS专用全屏）
 */
(function() {
    'use strict';

    /**
     * 检测是否为iOS设备
     * @returns {boolean} 如果是iOS设备返回true
     */
    function isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    }

    // 滚动到评论区的函数
    window.scrollToComments = function() {
        const commentsSection = document.querySelector('.comments-section');
        if (commentsSection) {
            // 使用平滑滚动
            commentsSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
            
            // 可选：高亮评论区域（短暂的视觉反馈）
            commentsSection.style.transition = 'background-color 0.3s ease';
            commentsSection.style.backgroundColor = 'rgba(147, 51, 234, 0.05)';
            setTimeout(() => {
                commentsSection.style.backgroundColor = '';
            }, 1000);
        }
    };

    // 重试查找元素的函数
    function waitForElement(selector, maxRetries = 10, interval = 500) {
        return new Promise((resolve, reject) => {
            let retries = 0;
            const check = () => {
                const element = document.getElementById(selector.replace('#', ''));
                if (element) {
                    resolve(element);
                } else if (retries < maxRetries) {
                    retries++;
                    console.log(`Waiting for ${selector}, attempt ${retries}/${maxRetries}`);
                    setTimeout(check, interval);
                } else {
                    reject(new Error(`Element ${selector} not found after ${maxRetries} attempts`));
                }
            };
            check();
        });
    }

    // 初始化游戏状态栏功能
    function initGameStatusBar() {
        const statusPseudoFullscreenBtn = document.getElementById('status-pseudo-fullscreen-btn');
        const statusNativeFullscreenBtn = document.getElementById('status-native-fullscreen-btn');
        const commentsBtn = document.getElementById('comments-btn');
        
        // 根据设备类型初始化相应的全屏功能
        if (isIOS()) {
            console.log('iOS device detected, initializing iOS fullscreen integration');
            initIOSFullscreenIntegration();
            // iOS设备隐藏原生全屏按钮
            if (statusNativeFullscreenBtn) {
                statusNativeFullscreenBtn.style.display = 'none';
            }
        } else {
            console.log('Non-iOS device detected, initializing standard fullscreen integration');
            initPseudoFullscreenIntegration();
            initNativeFullscreenIntegration();
        }

        // 初始化iOS专用全屏按钮集成
        function initIOSFullscreenIntegration() {
            if (!statusPseudoFullscreenBtn) {
                console.warn('Game Status Bar: Pseudo fullscreen button not found for iOS');
                return;
            }

            // 更新按钮文本为iOS专用
            const buttonText = statusPseudoFullscreenBtn.querySelector('span');
            if (buttonText) {
                buttonText.textContent = 'iOS Fullscreen';
            }
            statusPseudoFullscreenBtn.title = 'iOS Fullscreen';

            // 连接到iOS全屏功能
            statusPseudoFullscreenBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // 检查是否有全局的iOS全屏函数
                if (typeof window.isIOS === 'function' && typeof window.enterIOSFullscreen === 'function' && typeof window.exitIOSFullscreen === 'function') {
                    // 检查当前是否在iOS全屏状态
                    const gameSection = document.getElementById('game_section');
                    const isFullscreen = gameSection && gameSection.classList.contains('fullscreen');
                    
                    if (isFullscreen) {
                        // 退出iOS全屏
                        console.log('Triggering exit iOS fullscreen');
                        window.exitIOSFullscreen();
                    } else {
                        // 进入iOS全屏
                        console.log('Triggering enter iOS fullscreen');
                        window.enterIOSFullscreen();
                    }
                } else {
                    console.warn('iOS fullscreen functions not available');
                }
            });

            // 监听全屏状态变化，更新按钮显示
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        updateIOSFullscreenButton();
                    }
                });
            });
            
            const gameSection = document.getElementById('game_section');
            if (gameSection) {
                observer.observe(gameSection, { attributes: true });
            }
            
            // 初始更新按钮状态
            updateIOSFullscreenButton();
        }

        // 初始化伪全屏按钮集成（非iOS设备）
        async function initPseudoFullscreenIntegration() {
            if (!statusPseudoFullscreenBtn) {
                console.warn('Game Status Bar: Pseudo fullscreen button not found');
                return;
            }

            try {
                // 等待原有的伪全屏按钮
                const originalFullscreenBtn = await waitForElement('fullscreen-btn');
                const originalExitFullscreenBtn = await waitForElement('exit-fullscreen-btn');
                
                console.log('Found original pseudo fullscreen buttons:', originalFullscreenBtn, originalExitFullscreenBtn);
                
                // 隐藏原有的伪全屏按钮
                originalFullscreenBtn.style.display = 'none';
                originalExitFullscreenBtn.style.display = 'none';
                
                // 将状态栏的伪全屏按钮连接到原有的伪全屏功能
                statusPseudoFullscreenBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // 检查当前是否在伪全屏状态
                    const gameSection = document.getElementById('game_section');
                    const isFullscreen = gameSection && gameSection.classList.contains('fullscreen');
                    
                    // 确保不在原生全屏状态
                    const isNativeFullscreen = !!(
                        document.fullscreenElement ||
                        document.webkitFullscreenElement ||
                        document.mozFullScreenElement ||
                        document.msFullscreenElement
                    );
                    
                    if (isNativeFullscreen) {
                        console.log('Cannot use pseudo fullscreen while in native fullscreen mode');
                        return;
                    }
                    
                    if (isFullscreen) {
                        // 触发退出伪全屏
                        console.log('Triggering exit pseudo fullscreen');
                        originalExitFullscreenBtn.click();
                    } else {
                        // 触发进入伪全屏
                        console.log('Triggering enter pseudo fullscreen');
                        originalFullscreenBtn.click();
                    }
                });
                
                // 监听伪全屏状态变化，更新按钮文本和图标
                const observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                            updatePseudoFullscreenButton();
                        }
                    });
                });
                
                const gameSection = document.getElementById('game_section');
                if (gameSection) {
                    observer.observe(gameSection, { attributes: true });
                }
                
                // 初始更新按钮状态
                updatePseudoFullscreenButton();
                
            } catch (error) {
                console.error('Failed to initialize pseudo fullscreen integration:', error);
                // 提供降级功能 - 直接操作CSS类
                statusPseudoFullscreenBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const gameSection = document.getElementById('game_section');
                    if (gameSection) {
                        if (gameSection.classList.contains('fullscreen')) {
                            gameSection.classList.remove('fullscreen');
                        } else {
                            gameSection.classList.add('fullscreen');
                        }
                        updatePseudoFullscreenButton();
                    }
                });
            }
        }

        // 初始化原生全屏按钮集成（非iOS设备）
        async function initNativeFullscreenIntegration() {
            if (!statusNativeFullscreenBtn) {
                console.warn('Game Status Bar: Native fullscreen button not found');
                return;
            }

            try {
                // 等待原有的原生全屏按钮
                const originalNativeFullscreenBtn = await waitForElement('native-fullscreen-btn');
                const originalNativeExitFullscreenBtn = await waitForElement('native-exit-fullscreen-btn');
                
                console.log('Found original native fullscreen buttons:', originalNativeFullscreenBtn, originalNativeExitFullscreenBtn);
                
                // 隐藏原有的原生全屏按钮
                originalNativeFullscreenBtn.style.display = 'none';
                originalNativeExitFullscreenBtn.style.display = 'none';
                
                // 将状态栏的原生全屏按钮连接到原有的原生全屏功能
                statusNativeFullscreenBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // 检查当前是否在原生全屏状态
                    const isNativeFullscreen = !!(
                        document.fullscreenElement ||
                        document.webkitFullscreenElement ||
                        document.mozFullScreenElement ||
                        document.msFullscreenElement
                    );
                    
                    if (isNativeFullscreen) {
                        // 触发退出原生全屏
                        console.log('Triggering exit native fullscreen');
                        originalNativeExitFullscreenBtn.click();
                    } else {
                        // 触发进入原生全屏
                        console.log('Triggering enter native fullscreen');
                        originalNativeFullscreenBtn.click();
                    }
                });
                
                // 监听原生全屏状态变化
                document.addEventListener('fullscreenchange', updateNativeFullscreenButton);
                document.addEventListener('webkitfullscreenchange', updateNativeFullscreenButton);
                document.addEventListener('mozfullscreenchange', updateNativeFullscreenButton);
                document.addEventListener('MSFullscreenChange', updateNativeFullscreenButton);
                
                // 初始更新按钮状态
                updateNativeFullscreenButton();
                
            } catch (error) {
                console.error('Failed to initialize native fullscreen integration:', error);
                // 提供降级功能 - 直接调用浏览器全屏API
                statusNativeFullscreenBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const isNativeFullscreen = !!(
                        document.fullscreenElement ||
                        document.webkitFullscreenElement ||
                        document.mozFullScreenElement ||
                        document.msFullscreenElement
                    );
                    
                    if (isNativeFullscreen) {
                        // 退出全屏
                        if (document.exitFullscreen) {
                            document.exitFullscreen();
                        } else if (document.webkitExitFullscreen) {
                            document.webkitExitFullscreen();
                        } else if (document.mozCancelFullScreen) {
                            document.mozCancelFullScreen();
                        } else if (document.msExitFullscreen) {
                            document.msExitFullscreen();
                        }
                    } else {
                        // 进入全屏
                        const gameSection = document.getElementById('game_section');
                        if (gameSection) {
                            if (gameSection.requestFullscreen) {
                                gameSection.requestFullscreen();
                            } else if (gameSection.webkitRequestFullscreen) {
                                gameSection.webkitRequestFullscreen();
                            } else if (gameSection.mozRequestFullScreen) {
                                gameSection.mozRequestFullScreen();
                            } else if (gameSection.msRequestFullscreen) {
                                gameSection.msRequestFullscreen();
                            }
                        }
                    }
                });
            }
        }

        // 更新iOS全屏按钮的显示状态
        function updateIOSFullscreenButton() {
            if (!statusPseudoFullscreenBtn) return;
            
            const gameSection = document.getElementById('game_section');
            const isFullscreen = gameSection && gameSection.classList.contains('fullscreen');
            
            const buttonText = statusPseudoFullscreenBtn.querySelector('span');
            const buttonSvg = statusPseudoFullscreenBtn.querySelector('svg');
            
            if (isFullscreen) {
                // 退出iOS全屏状态
                statusPseudoFullscreenBtn.title = 'Exit iOS Fullscreen';
                if (buttonText) {
                    buttonText.textContent = 'Exit iOS';
                }
                if (buttonSvg) {
                    buttonSvg.innerHTML = `
                        <rect x="5" y="5" width="60" height="60" fill="none" stroke="currentColor" stroke-width="6" rx="3"/>
                        <g fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="square">
                            <path d="M25 15 L25 25 L15 25"/>
                            <path d="M45 15 L45 25 L55 25"/>
                            <path d="M25 55 L25 45 L15 45"/>
                            <path d="M45 55 L45 45 L55 45"/>
                        </g>
                    `;
                }
                statusPseudoFullscreenBtn.style.backgroundColor = '#7c3aed'; // purple-600 (全屏激活状态)
            } else {
                // 进入iOS全屏状态
                statusPseudoFullscreenBtn.title = 'iOS Fullscreen';
                if (buttonText) {
                    buttonText.textContent = 'iOS Fullscreen';
                }
                if (buttonSvg) {
                    buttonSvg.innerHTML = `
                        <rect x="5" y="5" width="60" height="60" fill="none" stroke="currentColor" stroke-width="6" rx="3"/>
                        <g fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="square">
                            <path d="M15 25 L15 15 L25 15"/>
                            <path d="M55 25 L55 15 L45 15"/>
                            <path d="M15 45 L15 55 L25 55"/>
                            <path d="M55 45 L55 55 L45 55"/>
                        </g>
                    `;
                }
                statusPseudoFullscreenBtn.style.backgroundColor = '#a855f7'; // purple-500 (统一主题色)
            }
        }

        // 更新伪全屏按钮的显示状态（非iOS设备）
        function updatePseudoFullscreenButton() {
            if (!statusPseudoFullscreenBtn) return;
            
            const gameSection = document.getElementById('game_section');
            const isFullscreen = gameSection && gameSection.classList.contains('fullscreen');
            const isNativeFullscreen = !!(
                document.fullscreenElement ||
                document.webkitFullscreenElement ||
                document.mozFullScreenElement ||
                document.msFullscreenElement
            );
            
            // 伪全屏状态是指：有fullscreen类但不在原生全屏模式
            const isPseudoFullscreen = isFullscreen && !isNativeFullscreen;
            
            const buttonText = statusPseudoFullscreenBtn.querySelector('span');
            const buttonSvg = statusPseudoFullscreenBtn.querySelector('svg');
            
            if (isPseudoFullscreen) {
                // 退出伪全屏状态
                statusPseudoFullscreenBtn.title = 'Exit Pseudo Fullscreen';
                if (buttonText) {
                    buttonText.textContent = 'Exit Pseudo';
                }
                if (buttonSvg) {
                    buttonSvg.innerHTML = `
                        <rect x="5" y="5" width="60" height="60" fill="none" stroke="currentColor" stroke-width="6" rx="3"/>
                        <g fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="square">
                            <path d="M25 15 L25 25 L15 25"/>
                            <path d="M45 15 L45 25 L55 25"/>
                            <path d="M25 55 L25 45 L15 45"/>
                            <path d="M45 55 L45 45 L55 45"/>
                        </g>
                    `;
                }
                statusPseudoFullscreenBtn.style.backgroundColor = '#7c3aed'; // purple-600 (全屏激活状态)
            } else {
                // 进入伪全屏状态
                statusPseudoFullscreenBtn.title = 'Pseudo Fullscreen';
                if (buttonText) {
                    buttonText.textContent = 'Pseudo Fullscreen';
                }
                if (buttonSvg) {
                    buttonSvg.innerHTML = `
                        <rect x="5" y="5" width="60" height="60" fill="none" stroke="currentColor" stroke-width="6" rx="3"/>
                        <g fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="square">
                            <path d="M15 25 L15 15 L25 15"/>
                            <path d="M55 25 L55 15 L45 15"/>
                            <path d="M15 45 L15 55 L25 55"/>
                            <path d="M55 45 L55 55 L45 55"/>
                        </g>
                    `;
                }
                statusPseudoFullscreenBtn.style.backgroundColor = '#a855f7'; // purple-500 (统一主题色)
            }
        }

        // 更新原生全屏按钮的显示状态
        function updateNativeFullscreenButton() {
            if (!statusNativeFullscreenBtn) return;
            
            const isNativeFullscreen = !!(
                document.fullscreenElement ||
                document.webkitFullscreenElement ||
                document.mozFullScreenElement ||
                document.msFullscreenElement
            );
            
            const buttonText = statusNativeFullscreenBtn.querySelector('span');
            const buttonSvg = statusNativeFullscreenBtn.querySelector('svg');
            
            if (isNativeFullscreen) {
                // 退出原生全屏状态
                statusNativeFullscreenBtn.title = 'Exit Native Fullscreen';
                if (buttonText) {
                    buttonText.textContent = 'Exit Native';
                }
                if (buttonSvg) {
                    buttonSvg.innerHTML = `
                        <g fill="none" stroke="currentColor" stroke-width="12" stroke-linecap="square">
                            <path d="M35 20 L35 35 L20 35"/>
                            <path d="M65 20 L65 35 L80 35"/>
                            <path d="M35 80 L35 65 L20 65"/>
                            <path d="M65 80 L65 65 L80 65"/>
                        </g>
                    `;
                }
                statusNativeFullscreenBtn.style.backgroundColor = '#7c3aed'; // purple-600 (全屏激活状态)
            } else {
                // 进入原生全屏状态
                statusNativeFullscreenBtn.title = 'Native Fullscreen';
                if (buttonText) {
                    buttonText.textContent = 'Native Fullscreen';
                }
                if (buttonSvg) {
                    buttonSvg.innerHTML = `
                        <g fill="none" stroke="currentColor" stroke-width="12" stroke-linecap="square">
                            <path d="M20 35 L20 20 L35 20"/>
                            <path d="M80 35 L80 20 L65 20"/>
                            <path d="M20 65 L20 80 L35 80"/>
                            <path d="M80 65 L80 80 L65 80"/>
                        </g>
                    `;
                }
                statusNativeFullscreenBtn.style.backgroundColor = '#a855f7'; // purple-500 (统一主题色)
            }
        }

        // 添加评论按钮的点击统计（可选）
        if (commentsBtn) {
            commentsBtn.addEventListener('click', function() {
                // 可以在这里添加分析代码
                console.log('Comments button clicked');
            });
        }
    }

    // 立即初始化（如果页面已加载）或在页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGameStatusBar);
    } else {
        initGameStatusBar();
    }
})(); 