/**
 * 表情选择器 (Emoji Picker) JavaScript 文件
 * 用于在评论系统中提供表情选择功能
 */

// 表情数据 - 定义所有表情分类及其表情
const emojiData = {
    common: {
        name: 'COM',
        emojis: ['😊', '😂', '❤️', '👍', '🎉', '✨', '🌟', '💯', '🔥', '👏', '🙏', '💪', '🤔', '🤣', '😅', '😆']
    },
    faces: {
        name: 'FACE',
        emojis: ['😀', '😃', '😄', '😁', '😅', '😆', '😉', '😊', '😋', '😎', '😍', '😘', '🥰', '😗', '😙', '😚', '🙂', '🤗', '🤩', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '😣', '😖', '😫', '😢', '😭', '😤', '😠']
    },
    gestures: {
        name: 'GEST',
        emojis: ['👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '👊', '✊', '👏', '🙌', '👐', '🤲', '🙏', '💪', '👋', '🤙', '👈', '👉', '👆', '👇', '✋', '🖐', '🖖']
    },
    nature: {
        name: 'NATU',
        emojis: ['🌸', '💮', '🌹', '🌺', '🌻', '🌼', '🌷', '🌱', '🌲', '🌳', '🌴', '🌵', '🌾', '🌿', '🍀', '🍁', '🍂', '🍃', '🍇', '🍈', '🍉', '🍊', '🍋', '🍌']
    },
    symbols: {
        name: 'SYM',
        emojis: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️', '✝️', '☪️', '🔯', '✡️', '🕎', '☸️']
    }
};

// 添加全局变量来跟踪当前活动的输入框
let currentEmojiTargetId = null;

// 立即导出initReplyFormEmoji函数到全局作用域，确保其他脚本可以访问它
window.initReplyFormEmoji = function(replyForm) {
    console.log('🔍 初始化回复表单表情选择器:', replyForm?.id || '未知表单');
    if (!replyForm) return;
    
    // 检查是否已初始化
    if (replyForm.dataset.emojiInitialized === 'true') {
        console.log('⚡ 表单已初始化，跳过');
        return;
    }
    
    const pickerContainer = replyForm.querySelector('.emoji-picker-container');
    if (!pickerContainer) {
        console.log('⚠️ 找不到表情选择器容器');
        return;
    }
    
    const textareaElement = replyForm.querySelector('.reply-content');
    if (!textareaElement) {
        console.log('⚠️ 找不到文本输入区域');
        return;
    }
    
    console.log('🛠️ 为回复表单创建表情选择器元素');
    
    // 创建表情按钮
    const emojiBtn = document.createElement('button');
    emojiBtn.type = 'button';
    emojiBtn.className = 'p-2 hover:bg-gray-100 rounded-full';
    emojiBtn.title = 'Insert emoji';
    emojiBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
            <line x1="9" y1="9" x2="9.01" y2="9"></line>
            <line x1="15" y1="9" x2="15.01" y2="9"></line>
        </svg>
    `;
    
    // 创建表情面板容器
    const emojiPanel = document.createElement('div');
    emojiPanel.className = 'emoji-panel custom-emoji-panel';
    emojiPanel.style.display = 'none';
    
    // 清空并添加新元素
    pickerContainer.innerHTML = '';
    pickerContainer.appendChild(emojiBtn);
    pickerContainer.appendChild(emojiPanel);
    console.log('✓ 添加表情按钮和面板容器');
    
    // 生成唯一ID
    textareaElement.id = textareaElement.id || `reply-textarea-${Math.random().toString(36).substring(2, 9)}`;
    emojiPanel.id = emojiPanel.id || `reply-emoji-panel-${Math.random().toString(36).substring(2, 9)}`;
    
    // 初始化表情面板
    generateEmojiPanel(emojiPanel, textareaElement);
    
    // 绑定按钮点击事件
    emojiBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('点击回复表单表情按钮');
        
        // 检查是否为移动端
        const isMobileView = window.innerWidth <= 768;
        
        if (isMobileView) {
            // 在移动端，使用全局表情面板
            // 首先隐藏所有已打开的表情面板
            document.querySelectorAll('.emoji-panel').forEach(p => {
                p.style.display = 'none';
            });
            
            // 使用移动端全局面板
            const mobilePanel = document.getElementById('mobile-emoji-panel');
            if (mobilePanel) {
                // 确保面板与当前文本框关联
                toggleEmojiPanel('mobile-emoji-panel', textareaElement.id);
            } else {
                // 如果没有全局面板，回退到当前面板
                toggleEmojiPanelElement(emojiPanel, textareaElement);
            }
        } else {
            // 桌面端使用常规逻辑
            toggleEmojiPanelElement(emojiPanel, textareaElement);
        }
    });
    
    // 标记为已初始化
    replyForm.dataset.emojiInitialized = 'true';
    console.log('✅ 回复表单表情选择器初始化完成');
};

/**
 * 动态生成表情选择器面板
 * @param {string|HTMLElement} panel - 表情面板元素或ID
 * @param {string|HTMLElement} targetInput - 目标输入框元素或ID
 * @param {Object} options - 配置选项
 */
function generateEmojiPanel(panel, targetInput, options = {}) {
    // 处理参数，支持DOM元素或ID字符串
    const panelElement = typeof panel === 'string' ? document.getElementById(panel) : panel;
    if (!panelElement) return;

    // 获取或生成唯一ID
    const panelId = panelElement.id || `emoji-panel-${Math.random().toString(36).substring(2, 9)}`;
    if (!panelElement.id) panelElement.id = panelId;
    
    // 确定目标输入框
    let inputElement;
    if (typeof targetInput === 'string') {
        inputElement = document.getElementById(targetInput);
    } else {
        inputElement = targetInput;
    }
    
    if (!inputElement) {
        console.error('目标输入框未找到');
        return;
    }
    
    // 设置面板类名
    if (!panelElement.classList.contains('emoji-panel')) {
        panelElement.classList.add('emoji-panel', 'custom-emoji-panel');
    }

    // 创建表情分类标签
    let tabsHtml = '<div class="emoji-tabs">';
    Object.keys(emojiData).forEach((category, index) => {
        const isActive = index === 0 ? 'active' : '';
        tabsHtml += `<button type="button" class="emoji-tab ${isActive}" data-category="${category}">${emojiData[category].name}</button>`;
    });
    tabsHtml += '</div>';

    // 创建表情网格容器
    let gridsHtml = '';
    Object.keys(emojiData).forEach((category, index) => {
        const display = index === 0 ? '' : 'style="display:none;"';
        gridsHtml += `<div id="${panelId}-${category}" class="emoji-grid" ${display}>`;

        // 添加表情
        emojiData[category].emojis.forEach(emoji => {
            gridsHtml += `<span class="emoji-item" data-emoji="${emoji}">${emoji}</span>`;
        });

        gridsHtml += '</div>';
    });

    // 组合HTML
    panelElement.innerHTML = tabsHtml + gridsHtml;
    
    // 标记面板已初始化
    panelElement.dataset.initialized = 'true';
    
    // 绑定表情点击事件
    panelElement.querySelectorAll('.emoji-item').forEach(item => {
        item.addEventListener('click', function(e) {
            const emoji = this.getAttribute('data-emoji') || this.textContent;
            insertEmojiToElement(inputElement, emoji);
            
            // 隐藏面板
            panelElement.style.display = 'none';
        });
    });
    
    // 绑定分类标签点击事件
    panelElement.querySelectorAll('.emoji-tab').forEach(tab => {
        tab.addEventListener('click', function(e) {
            const category = this.getAttribute('data-category');
            switchEmojiCategoryInPanel(panelElement, category);
        });
    });

    // 返回生成的面板
    return panelElement;
}

/**
 * 将表情插入到指定输入框元素
 * @param {HTMLElement} inputElement - 输入框元素
 * @param {string} emoji - 表情字符
 */
function insertEmojiToElement(inputElement, emoji) {
    if (!inputElement) return;
    
    const start = inputElement.selectionStart;
    const end = inputElement.selectionEnd;
    const text = inputElement.value;
    
    inputElement.value = text.substring(0, start) + emoji + text.substring(end);
    inputElement.focus();
    inputElement.selectionStart = inputElement.selectionEnd = start + emoji.length;
}

/**
 * 切换指定面板内的表情分类
 * @param {HTMLElement} panelElement - 表情面板元素
 * @param {string} category - 分类名称
 */
function switchEmojiCategoryInPanel(panelElement, category) {
    if (!panelElement) return;
    
    // 获取面板ID
    const panelId = panelElement.id;
    
    // 隐藏所有表情网格
    panelElement.querySelectorAll('.emoji-grid').forEach(grid => {
        grid.style.display = 'none';
    });
    
    // 显示选择的分类
    const selectedGrid = document.getElementById(`${panelId}-${category}`);
    if (selectedGrid) {
        selectedGrid.style.display = 'grid';
    }
    
    // 更新标签状态
    panelElement.querySelectorAll('.emoji-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 激活当前标签
    panelElement.querySelectorAll(`.emoji-tab[data-category="${category}"]`).forEach(tab => {
        tab.classList.add('active');
    });
}

// 在页面加载完成后初始化表情选择器
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 emoji-picker.js: DOM加载完成，初始化表情选择器系统...');

    // 初始化主评论表情选择器
    initMainCommentEmojis();
    
    // 初始化已存在的回复表单的表情选择器
    initExistingReplyFormEmojis();
    
    // 监听新回复表单的创建
    setupReplyFormObserver();
    
    console.log('✅ 表情选择器系统初始化完成');
});

/**
 * 初始化主评论表情选择器
 */
function initMainCommentEmojis() {
    // 初始化桌面端表情选择器
    const desktopPanel = document.getElementById('desktop-emoji-panel');
    const desktopInput = document.getElementById('comment-input-desktop');
    if (desktopPanel && desktopInput) {
        generateEmojiPanel(desktopPanel, desktopInput);
        
        // 绑定桌面端表情按钮点击事件
        const desktopBtn = document.getElementById('desktop-emoji-btn');
        if (desktopBtn) {
            desktopBtn.onclick = function(e) {
                e.preventDefault();
                toggleEmojiPanelElement(desktopPanel, desktopInput);
            };
        }
    }
    
    // 初始化移动端表情选择器
    const mobilePanel = document.getElementById('mobile-emoji-panel');
    const mobileInput = document.getElementById('comment-input-mobile');
    if (mobilePanel && mobileInput) {
        generateEmojiPanel(mobilePanel, mobileInput);
        
        // 绑定移动端表情按钮点击事件
        const mobileBtn = document.getElementById('mobile-emoji-btn');
        if (mobileBtn) {
            mobileBtn.onclick = function(e) {
                e.preventDefault();
                toggleEmojiPanelElement(mobilePanel, mobileInput);
            };
        }
    }
}

/**
 * 初始化页面上已存在的回复表单的表情选择器
 */
function initExistingReplyFormEmojis() {
    document.querySelectorAll('.reply-form').forEach(form => {
        if (!form.dataset.emojiInitialized) {
            initReplyFormEmoji(form);
        }
    });
}

/**
 * 设置回复表单观察器，用于监听新添加的回复表单
 */
function setupReplyFormObserver() {
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1 && node.classList.contains('reply-form') && !node.dataset.emojiInitialized) {
                        setTimeout(() => initReplyFormEmoji(node), 50);
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
}

/**
 * 切换表情面板显示/隐藏状态
 * @param {HTMLElement} panel - 表情面板元素
 * @param {HTMLElement} input - 目标输入框元素
 */
function toggleEmojiPanelElement(panel, input) {
    if (!panel) return;
    
    // 如果面板尚未初始化，先初始化它
    if (!panel.dataset.initialized) {
        generateEmojiPanel(panel, input);
    }
    
    // 切换显示状态
    if (panel.style.display === 'none' || !panel.style.display || panel.style.display === '') {
        // 显示面板
        panel.style.display = 'block';
        
        // 关闭其他表情面板
        document.querySelectorAll('.emoji-panel').forEach(p => {
            if (p !== panel && p.style.display !== 'none') {
                p.style.display = 'none';
            }
        });
        
        // 添加点击外部关闭面板
        setTimeout(() => {
            document.addEventListener('click', function closeHandler(event) {
                if (!panel) {
                    document.removeEventListener('click', closeHandler);
                    return;
                }
                
                const container = panel.parentNode;
                
                if (!panel.contains(event.target) && (!container || !container.contains(event.target) || event.target === panel)) {
                    panel.style.display = 'none';
                    document.removeEventListener('click', closeHandler);
                }
            });
        }, 100);
    } else {
        // 隐藏面板
        panel.style.display = 'none';
    }
}

/**
 * 向后兼容的表情面板切换函数
 * @param {string} panelId - 表情面板ID
 * @param {string} textareaId - 目标文本框ID
 */
function toggleEmojiPanel(panelId, textareaId) {
    console.log('切换表情面板', panelId, textareaId);
    const panel = document.getElementById(panelId);
    const input = document.getElementById(textareaId);
    
    if (panel && input) {
        // 保存当前目标输入框ID
        currentEmojiTargetId = textareaId;
        
        // 在移动端，使用全局表情面板时需要更新面板的关联输入框
        if (window.innerWidth <= 768 && panelId === 'mobile-emoji-panel') {
            // 更新面板关联的输入框元素
            panel.dataset.targetInput = textareaId;
            
            // 重新初始化表情项的点击事件，确保它们插入到正确的输入框
            panel.querySelectorAll('.emoji-item').forEach(item => {
                // 移除之前的事件监听器
                const newItem = item.cloneNode(true);
                item.parentNode.replaceChild(newItem, item);
                
                // 添加新的事件监听器，使用当前的目标输入框
                newItem.addEventListener('click', function() {
                    const emoji = this.getAttribute('data-emoji') || this.textContent;
                    // 使用当前保存的输入框ID
                    const targetInput = document.getElementById(currentEmojiTargetId);
                    if (targetInput) {
                        insertEmojiToElement(targetInput, emoji);
                    } else {
                        // 回退到原始输入框
                        insertEmojiToElement(input, emoji);
                    }
                    // 隐藏面板
                    panel.style.display = 'none';
                });
            });
        }
        
        // 调用原有的面板切换函数
        toggleEmojiPanelElement(panel, input);
    }
}

/**
 * 向后兼容的表情分类切换函数
 * @param {string} panelId - 表情面板ID
 * @param {string} category - 分类名称
 */
function switchEmojiCategory(panelId, category) {
    const panel = document.getElementById(panelId);
    if (panel) {
        switchEmojiCategoryInPanel(panel, category);
    }
}

/**
 * 向后兼容的表情插入函数
 * @param {string} textareaId - 文本框ID
 * @param {string} emoji - 表情符号
 */
function insertEmoji(textareaId, emoji) {
    // 首先尝试使用当前活动的输入框
    let textarea = null;
    if (currentEmojiTargetId) {
        textarea = document.getElementById(currentEmojiTargetId);
    }
    
    // 如果没找到，再尝试使用提供的ID
    if (!textarea) {
        textarea = document.getElementById(textareaId);
    }
    
    if (textarea) {
        insertEmojiToElement(textarea, emoji);
    }
}

// 调试表情选择器事件绑定
function debugEmojiTrigger() {
    console.log('🔍 表情按钮调试事件检查开始...');
    
    // 检查所有表情触发按钮
    const emojiTriggers = document.querySelectorAll('.emoji-trigger, [onclick*="toggleEmojiPanel"]');
    console.log(`找到 ${emojiTriggers.length} 个表情按钮`);
    
    emojiTriggers.forEach((trigger, index) => {
        console.log(`按钮 ${index + 1}:`, {
            type: trigger.tagName,
            hasOnclick: !!trigger.getAttribute('onclick'),
            onclick: trigger.getAttribute('onclick'),
            parentElement: trigger.parentElement?.className
        });
        
        // 确保所有按钮都有事件处理，但避免重复绑定
        if (!trigger.getAttribute('onclick') && !trigger._hasDebugEvent && !trigger.classList.contains('emoji-trigger')) {
            console.log(`为按钮 ${index + 1} 添加调试点击事件...`);
            
            trigger._hasDebugEvent = true;
            trigger.addEventListener('click', function(e) {
                e.preventDefault(); // 阻止默认行为
                e.stopPropagation(); // 阻止冒泡
                
                console.log(`调试: 按钮 ${index + 1} 被点击!`);
                
                // 尝试查找按钮所属的面板
                const container = this.parentElement;
                const panel = container ? container.querySelector('.emoji-panel') : null;
                
                console.log('按钮容器:', container);
                console.log('关联面板:', panel);
                
                if (panel) {
                    console.log('尝试切换面板显示状态');
                    if (panel.style.display === 'none' || !panel.style.display) {
                        panel.style.display = 'block';
                        
                        // 关闭其他表情面板
                        document.querySelectorAll('.emoji-panel').forEach(p => {
                            if (p !== panel && p.style.display !== 'none') {
                                p.style.display = 'none';
                            }
                        });
                        
                        // 添加点击外部关闭面板事件
                        setTimeout(() => {
                            document.addEventListener('click', function closeEmojiPanel(evt) {
                                if (!panel.contains(evt.target) && !container.contains(evt.target)) {
                                    panel.style.display = 'none';
                                    document.removeEventListener('click', closeEmojiPanel);
                                }
                            });
                        }, 100);
                    } else {
                        panel.style.display = 'none';
                    }
                }
            });
        }
    });
    
    console.log('✅ 表情按钮调试事件绑定完成');
} 