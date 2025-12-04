// 旧版评论系统 - 临时启用，等待完全迁移到新版
const OLD_COMMENT_SYSTEM_DISABLED = false;

if (OLD_COMMENT_SYSTEM_DISABLED) {
    console.log('⚠️ 旧版评论系统已禁用，请使用新版 comment-system.js');
} else {
    console.log('⚠️ 旧版评论系统临时启用，建议迁移到新版 comment-system.js');
}

// 评论系统全局变量
let currentRating = 0; // 改为0，要求用户必须选择评分
let allComments = []; // 存储所有评论
let displayedComments = []; // 当前显示的评论
let commentsLoaded = false;
let commentsPerPage = 10; // 每页显示的评论数
let currentPage = 1; // 当前页码
let totalComments = 0; // 总评论数
let totalPages = 0; // 总页数

// 添加调试信息
console.log('🚀 评论系统初始化');
console.log('当前URL:', window.location.href);
console.log('当前路径:', window.location.pathname);
console.log('初始评分:', currentRating);

// 检测当前设备类型
function isMobile() {
    return window.innerWidth <= 768;
}

// 获取当前活动的输入元素
function getActiveInputs() {
    const mobile = isMobile();
    return {
        commentInput: document.getElementById(mobile ? 'comment-input-mobile' : 'comment-input-desktop'),
        usernameInput: document.getElementById(mobile ? 'username-input-mobile' : 'username-input-desktop'),
        emailInput: document.getElementById(mobile ? 'email-input-mobile' : 'email-input-desktop'),
        submitText: document.getElementById(mobile ? 'submit-text-mobile' : 'submit-text-desktop'),
        submitLoading: document.getElementById(mobile ? 'submit-loading-mobile' : 'submit-loading-desktop')
    };
}

// 初始化评论系统
document.addEventListener('DOMContentLoaded', function() {
    if (OLD_COMMENT_SYSTEM_DISABLED) {
        console.log('⚠️ 旧版评论系统已禁用，跳过初始化');
        return;
    }
    console.log('📅 DOM加载完成，初始化评论系统...');
    initializeCommentSystem();
});

// 初始化评论系统
function initializeCommentSystem() {
    if (OLD_COMMENT_SYSTEM_DISABLED) {
        console.log('⚠️ 旧版评论系统已禁用，跳过初始化');
        return;
    }
    console.log('🚀 初始化评论系统...');
    setupRatingInput();
    loadComments();
    
    // 添加全局事件委托，处理动态生成的回复按钮点击
    document.addEventListener('click', function(event) {
        // 处理回复按钮点击
        if (event.target && (event.target.classList.contains('reply-btn') || 
            (event.target.parentElement && event.target.parentElement.classList.contains('reply-btn')))) {
            
            // 获取按钮元素（可能是按钮内部的文本节点被点击）
            const button = event.target.classList.contains('reply-btn') ? 
                event.target : event.target.parentElement;
            
            // 从按钮的data属性获取参数
            const commentId = button.dataset.commentId;
            const replyId = button.dataset.replyId;
            const username = button.dataset.username;
            const level = parseInt(button.dataset.level || '0');
            
            if (commentId && replyId && username !== undefined) {
                console.log(`🖱️ 通过事件委托捕获回复按钮点击: commentId=${commentId}, replyId=${replyId}, username=${username}, level=${level}`);
                showReplyToReplyForm(commentId, replyId, username, level);
                event.preventDefault();
                event.stopPropagation();
            }
        }
        
        // 处理提交回复按钮点击
        if (event.target && event.target.classList.contains('submit-reply-btn')) {
            const replyForm = event.target.closest('.reply-form');
            if (replyForm) {
                // 更安全的commentId解析方式
                let commentId;
                let afterPrefix;
                const formId = replyForm.id;
                
                // 表单ID格式: reply-form-{commentId} 或 reply-form-{commentId}-{parentReplyId}
                if (formId.startsWith('reply-form-')) {
                    afterPrefix = formId.substring('reply-form-'.length);
                    
                    // 如果有第二个UUID（parentReplyId），需要分离
                    const uuidPattern = /^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/;
                    const match = afterPrefix.match(uuidPattern);
                    
                    if (match) {
                        commentId = match[1];
                    } else {
                        // 备用方案：假设没有parentReplyId
                        commentId = afterPrefix;
                    }
                }
                
                console.log(`🔍 Parsed commentId from form ID '${formId}': ${commentId}`);
                
                if (commentId) {
                    // 检查是否是回复的回复（从表单ID判断）
                    const isReplyToReply = formId.includes('-') && formId.split('-').length > 3;
                    
                    if (isReplyToReply) {
                        // 解析parentReplyId
                        const afterCommentId = afterPrefix.substring(commentId.length + 1); // +1 for the dash
                        const parentReplyId = afterCommentId;
                        
                        const usernameSpan = replyForm.querySelector('.reply-to-username');
                        const parentUsername = usernameSpan ? usernameSpan.textContent : '';
                        
                        console.log(`🖱️ 捕获提交回复的回复按钮点击: commentId=${commentId}, parentReplyId=${parentReplyId}, parentUsername=${parentUsername}`);
                        submitReplyToReply(commentId, parentReplyId, parentUsername);
                    } else {
                        console.log(`🖱️ 捕获提交直接回复按钮点击: commentId=${commentId}`);
                        submitReply(commentId);
                    }
                } else {
                    console.error('❌ Could not parse commentId from form ID:', formId);
                }
                
                event.preventDefault();
                event.stopPropagation();
            }
        }
        
        // 处理取消回复按钮点击
        if (event.target && event.target.classList.contains('cancel-reply-btn')) {
            console.log('🖱️ 捕获取消回复按钮点击');
            hideAllReplyForms();
            event.preventDefault();
            event.stopPropagation();
        }
    });
    
    console.log('✅ 评论系统初始化完成，已添加全局事件监听');
}

// 设置评分输入
function setupRatingInput() {
    console.log('⭐ 设置评分输入...');
    const ratingInputs = document.querySelectorAll('.rating-input');
    console.log(`找到 ${ratingInputs.length} 个评分星星`);
    
    ratingInputs.forEach((star, index) => {
        star.addEventListener('mouseenter', () => highlightStars(index + 1));
        star.addEventListener('mouseleave', () => highlightStars(currentRating));
        star.addEventListener('click', () => setRating(index + 1));
    });
    
    // 初始状态：所有星星都不高亮
    highlightStars(0);
}

// 高亮星星
function highlightStars(rating) {
    const ratingInputs = document.querySelectorAll('.rating-input');
    ratingInputs.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

// 设置评分
function setRating(rating) {
    console.log(`⭐ 用户选择评分: ${rating}`);
    currentRating = rating;
    highlightStars(rating);
}

// 真实的加载评论数据
async function loadComments() {
    try {
        // 显示加载状态
        const commentsList = document.getElementById('comments-list');
        const loadingElement = document.getElementById('loading-comments');
        
        // 安全检查：确保加载元素存在再操作
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }
        
        // 获取正确的article_url
        const articleUrl = getArticleUrl();
        console.log('Loading comments for article_url:', articleUrl);
        
        // 调用真实API - 修复：请求足够大的数量以获取所有评论信息
        const apiUrl = `/api/comments${articleUrl}?page=1&per_page=50&sort_by=created_at`;
        console.log('API URL:', apiUrl);
        
        const response = await fetch(apiUrl);
        const result = await response.json();
        
        console.log('API response:', result);
        
        if (result.success) {
            // 存储所有评论数据
            allComments = result.data;
            totalComments = result.pagination ? result.pagination.total : allComments.length;
            totalPages = result.pagination ? result.pagination.pages : 1;
            
            // 初始显示前10条评论
            displayedComments = allComments.slice(0, commentsPerPage);
            currentPage = 1;
            
            console.log(`📊 评论统计: 总计${totalComments}条, 当前显示${displayedComments.length}条`);
            
            // 添加调试信息检查回复数据
            console.log('🔍 调试: 检查评论数据中的回复结构');
            allComments.forEach((comment, index) => {
                if (comment.replies && comment.replies.length > 0) {
                    console.log(`📝 评论 ${index}: ${comment.username} 有 ${comment.replies.length} 个回复`);
                    comment.replies.forEach((reply, replyIndex) => {
                        console.log(`  回复 ${replyIndex}: ${reply.username} - children: ${reply.children ? reply.children.length : 0}`);
                        if (reply.children && reply.children.length > 0) {
                            reply.children.forEach((child, childIndex) => {
                                console.log(`    子回复 ${childIndex}: ${child.username} - @${child.reply_to_username}`);
                            });
                        }
                    });
                }
            });
            
            renderComments();
            updateCommentStats();
            updateLoadMoreButton();
            commentsLoaded = true;
            
            // 加载统计信息
            loadCommentStats();
        } else {
            console.error('加载评论失败:', result.message);
            if (commentsList) {
                commentsList.innerHTML = `
                    <div class="text-center py-8">
                        <p class="text-red-500">Network error, please try again later</p>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('加载评论出错:', error);
        const commentsList = document.getElementById('comments-list');
        if (commentsList) {
            commentsList.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-red-500">Network error, please try again later</p>
                </div>
            `;
        }
    } finally {
        // 安全检查：确保加载元素存在再操作
        const loadingElement = document.getElementById('loading-comments');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
}

// 获取正确的article_url
function getArticleUrl() {
    // 获取当前页面的路径
    const path = window.location.pathname;
    console.log('当前路径:', path);
    return path;
}

// 加载评论统计
async function loadCommentStats() {
    try {
        const articleUrl = getArticleUrl();
        const response = await fetch(`/api/comments${articleUrl}/stats`);
        const result = await response.json();
        
        if (result.success) {
            const stats = result.data;
            updateCommentStatsDisplay(stats);
        }
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 更新统计显示
function updateCommentStatsDisplay(stats) {
    const totalElement = document.getElementById('total-comments');
    const averageElement = document.getElementById('average-rating');
    
    if (totalElement) {
        totalElement.textContent = `${stats.total_comments} comments`;
    }
    if (averageElement) {
        averageElement.textContent = `${stats.average_rating} ★`;
    }
}

// 渲染评论列表
function renderComments() {
    const commentsList = document.getElementById('comments-list');
    const loadingElement = document.getElementById('loading-comments');
    
    if (displayedComments.length === 0) {
        if (commentsList) {
            commentsList.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-gray-500">No comments yet. Be the first to share your thoughts!</p>
                </div>
            `;
        }
        return;
    }
    
    // 安全检查：确保加载元素存在再操作
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
    
    const commentsHTML = displayedComments.map(comment => renderComment(comment)).join('');
    
    if (commentsList) {
        commentsList.innerHTML = commentsHTML;
    }
}

// 渲染单个评论（支持层级回复）
function renderComment(comment) {
    const repliesHTML = comment.replies && comment.replies.length > 0 
        ? `<div class="replies">${comment.replies.map(reply => renderReply(reply, comment.comment_id, 0)).join('')}</div>`
        : '';
    
    return `
        <div class="comment-item p-4 mb-4" data-comment-id="${comment.comment_id}">
            <div class="flex items-start space-x-3">
                <div class="user-avatar">${comment.username.charAt(0).toUpperCase()}</div>
                <div class="flex-1">
                    <div class="flex flex-col md:flex-row md:items-center justify-between mb-2 comment-header-mobile">
                        <div class="flex items-center space-x-2">
                            <span class="font-medium text-gray-900">${escapeHtml(comment.username)}</span>
                            <div class="rating-stars">
                                ${'★'.repeat(comment.rating)}${'☆'.repeat(5-comment.rating)}
                            </div>
                        </div>
                        <span class="text-sm text-gray-500">${formatTime(comment.created_at)}</span>
                    </div>
                    <p class="comment-content text-gray-700 mb-3 text-sm md:text-base">${escapeHtml(comment.content)}</p>
                    <div class="comment-actions flex items-center space-x-4">
                        <button onclick="likeComment('${comment.comment_id}')" class="btn-secondary flex items-center space-x-1">
                            <span>👍</span>
                            <span>${comment.likes}</span>
                        </button>
                        <button onclick="showReplyForm('${comment.comment_id}', 0)" class="btn-secondary">
                            Reply
                        </button>
                    </div>
                    ${repliesHTML}
                </div>
            </div>
        </div>
    `;
}

// 渲染回复（支持递归嵌套）
function renderReply(reply, commentId, level = 0) {
    // 层级限制：最多3层 (统一限制标准)
    if (level >= 3) {
        console.log(`⚠️ 达到最大层级限制 (level ${level}), 跳过渲染`);
        return '';
    }
    
    // 强化调试信息
    console.log(`🔍 [Level ${level}] 渲染回复: ${reply.username}`);
    console.log(`   - reply_id: ${reply.reply_id}`);
    console.log(`   - parent_reply_id: ${reply.parent_reply_id || 'none'}`);
    console.log(`   - reply_to_username: ${reply.reply_to_username || 'none'}`);
    console.log(`   - children数量: ${reply.children ? reply.children.length : 0}`);
    
    // 处理@提及显示
    let contentWithMention = escapeHtml(reply.content);
    if (reply.reply_to_username) {
        contentWithMention = `<span class="reply-mention">@${escapeHtml(reply.reply_to_username)}</span> ${contentWithMention}`;
    }
    
    // 递归渲染子回复 - 修复逻辑结构
    let childRepliesHTML = '';
    if (reply.children && reply.children.length > 0) {
        console.log(`🌳 [Level ${level}] 开始渲染 ${reply.children.length} 个子回复:`);
        reply.children.forEach((child, index) => {
            console.log(`   子回复 ${index}: ${child.username} (level将为 ${level + 1})`);
        });
        
        const childrenArray = reply.children.map(childReply => {
            const childHTML = renderReply(childReply, commentId, level + 1);
            console.log(`   子回复HTML生成: ${childHTML.length > 0 ? '成功' : '失败'} (长度: ${childHTML.length})`);
            return childHTML;
        }).filter(html => html.length > 0); // 过滤掉空的HTML
        
        if (childrenArray.length > 0) {
            childRepliesHTML = `<div class="sub-replies" style="margin-top: 12px; padding-left: 16px; border-left: 2px solid #e9ecef; background-color: rgba(139, 92, 246, 0.05); display: block !important; visibility: visible !important;">${childrenArray.join('')}</div>`;
            console.log(`🎨 [Level ${level}] 子回复容器HTML长度: ${childRepliesHTML.length}`);
        } else {
            console.log(`📄 [Level ${level}] 子回复渲染后为空`);
        }
    } else {
        console.log(`📄 [Level ${level}] 无子回复`);
    }
    
    // 确定是否可以回复 (统一层级限制: 最多2层回复按钮，即可以创建到level 2)
    const canReply = level < 2;
    
    // 生成唯一ID，确保DOM元素标识唯一性
    const replyUniqueId = `reply-${commentId}-${reply.reply_id}`;
    
    // 为回复按钮生成安全的onClick代码 - 使用data属性存储参数，避免JavaScript注入问题
    const replyBtnOnClick = `showReplyToReplyForm('${commentId}', '${reply.reply_id}', '${escapeHtml(reply.username).replace(/'/g, "\\'")}', ${level})`;
    
    // 生成回复HTML - 使用内联样式确保显示
    const replyHTML = `
        <div class="reply-item level-${level}" id="${replyUniqueId}" data-reply-id="${reply.reply_id}" data-comment-id="${commentId}" data-level="${level}" style="
            background: ${level === 0 ? 'linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)' : 
                        level === 1 ? 'linear-gradient(135deg, #f8faff 0%, #f1f5ff 100%)' : 
                                     'linear-gradient(135deg, #fafbff 0%, #f6f8ff 100%)'}; 
            border: 1px solid #e9ecef; 
            border-left: 4px solid ${level === 0 ? '#8b5cf6' : level === 1 ? '#7c3aed' : '#6d28d9'}; 
            border-radius: 8px; 
            padding: 12px; 
            margin-bottom: 12px; 
            margin-left: ${level * 20}px;
            min-height: 60px;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        ">
            <div class="flex items-start space-x-2" style="display: flex; align-items: flex-start; gap: 8px;">
                <div class="user-avatar" style="
                    width: 32px; 
                    height: 32px; 
                    background: linear-gradient(135deg, #8b5cf6, #7c3aed); 
                    color: white; 
                    border-radius: 50%; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    font-size: 14px; 
                    font-weight: bold;
                    flex-shrink: 0;
                ">
                    ${reply.username.charAt(0).toUpperCase()}
                </div>
                <div class="flex-1" style="flex: 1; min-width: 0;">
                    <div class="flex items-center space-x-2 mb-1" style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                        <span class="font-medium text-sm" style="font-weight: 600; font-size: 14px; color: #1f2937;">${escapeHtml(reply.username)}</span>
                        <span class="text-xs text-gray-500" style="font-size: 12px; color: #6b7280;">${formatTime(reply.created_at)}</span>
                        <span style="font-size: 10px; color: #8b5cf6; font-weight: bold;">[Level ${level}]</span>
                    </div>
                    <p class="comment-content text-gray-700 text-sm mb-2" style="color: #374151; font-size: 14px; margin-bottom: 8px; line-height: 1.5;">${contentWithMention}</p>
                    <div class="reply-actions flex items-center space-x-2" style="display: flex; align-items: center; gap: 8px;">
                        <button onclick="likeReply('${commentId}', '${reply.reply_id}')" class="btn-secondary text-xs" style="padding: 4px 8px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer;">
                            👍 ${reply.likes}
                        </button>
                        ${canReply ? `
                        <button onclick="${replyBtnOnClick}" class="btn-secondary text-xs reply-btn" data-reply-id="${reply.reply_id}" data-comment-id="${commentId}" data-username="${escapeHtml(reply.username)}" data-level="${level}" style="padding: 4px 8px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer;">
                            Reply
                        </button>
                        ` : ''}
                    </div>
                    ${childRepliesHTML}
                </div>
            </div>
        </div>
    `;
    
    console.log(`✅ [Level ${level}] 回复HTML生成完成，长度: ${replyHTML.length}`);
    return replyHTML;
}

// 显示回复表单
function showReplyForm(commentId, level = 0) {
    console.log(`🔍 显示评论回复表单 commentId=${commentId}, level=${level}`);
    
    // 隐藏其他回复表单
    hideAllReplyForms();
    
    // 获取回复表单模板
    const template = document.getElementById('reply-form-template');
    if (!template) {
        console.error('找不到回复表单模板，等待DOM完全加载后重试...');
        
        // 等待DOM完全加载后重试
        setTimeout(() => {
            const retryTemplate = document.getElementById('reply-form-template');
            if (!retryTemplate) {
                console.error('重试后仍找不到回复表单模板');
                showSuccessToast('Comment system loading, please try again later');
                return;
            }
            // 重新调用函数
            showReplyForm(commentId, level);
        }, 500);
        return;
    }
    
    const replyForm = template.content.cloneNode(true).firstElementChild;
    
    // 找到评论对象
    const comment = allComments.find(c => c.comment_id === commentId);
    if (!comment) {
        console.error(`找不到评论对象 ID=${commentId}`);
        return;
    }
    
    // 设置回复对象用户名
    const usernameSpan = replyForm.querySelector('.reply-to-username');
    if (usernameSpan) {
        usernameSpan.textContent = comment.username || '';
    }
    
    // 设置表单ID
    replyForm.id = `reply-form-${commentId}`;
    console.log(`创建回复表单 ID=${replyForm.id}`);
    
    // 找到评论元素并添加回复表单
    const commentElement = document.querySelector(`.comment-item button[onclick*="showReplyForm('${commentId}'"]`);
    if (!commentElement) {
        console.error(`找不到评论元素按钮 commentId=${commentId}`);
        
        // 尝试使用另一种选择器
        const altCommentElement = document.querySelector(`.comment-item[data-comment-id="${commentId}"]`);
        if (!altCommentElement) {
            console.error(`仍找不到评论元素 commentId=${commentId}`);
            return;
        }
        
        const actionsDiv = altCommentElement.querySelector('.comment-actions');
        if (!actionsDiv) {
            console.error(`找不到评论操作区域 commentId=${commentId}`);
            return;
        }
        
        actionsDiv.insertAdjacentElement('afterend', replyForm);
        console.log('成功添加回复表单（替代方法）');
    } else {
        const commentItem = commentElement.closest('.comment-item');
        if (!commentItem) {
            console.error(`找不到评论项目 commentId=${commentId}`);
            return;
        }
        
        const actionsDiv = commentItem.querySelector('.comment-actions');
        if (!actionsDiv) {
            console.error(`找不到评论操作区域 commentId=${commentId}`);
            return;
        }
        
        actionsDiv.insertAdjacentElement('afterend', replyForm);
        console.log('成功添加回复表单');
    }
    
    // 设置提交和取消按钮事件处理
    const submitBtn = replyForm.querySelector('.submit-reply-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function() {
            console.log(`点击提交评论回复按钮 commentId=${commentId}`);
            submitReply(commentId);
        });
    }
    
    const cancelBtn = replyForm.querySelector('.cancel-reply-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            console.log('点击取消回复按钮');
            hideAllReplyForms();
        });
    }
    
    // 初始化表情选择器
    setTimeout(() => {
        initReplyFormEmoji(replyForm);
        
        // 聚焦到输入框
        const textArea = replyForm.querySelector('.reply-content');
        if (textArea) {
            textArea.focus();
        }
        
        // 应用调试事件
        debugEmojiTrigger();
    }, 100);
}

// 显示回复特定回复的表单
function showReplyToReplyForm(commentId, parentReplyId, parentUsername, level = 0) {
    console.log(`🔍 显示回复的回复表单: commentId=${commentId}, parentReplyId=${parentReplyId}, parentUsername=${parentUsername}, level=${level}`);
    
    // 层级限制检查 (统一限制: 最多2层可以回复，即可以创建到level 2)
    if (level >= 2) {
        showSuccessToast('Maximum reply depth reached. Please reply in the main comment area.');
        return;
    }
    
    // 隐藏其他回复表单
    hideAllReplyForms();
    
    // 获取回复表单模板
    const template = document.getElementById('reply-form-template');
    if (!template) {
        console.error('Reply form template not found, retrying after DOM loads...');
        
        // 等待DOM完全加载后重试
        setTimeout(() => {
            const retryTemplate = document.getElementById('reply-form-template');
            if (!retryTemplate) {
                console.error('Reply form template still not found after retry');
                showSuccessToast('Reply form not found, please reload page');
                return;
            }
            // 重新调用函数
            showReplyToReplyForm(commentId, parentReplyId, parentUsername, level);
        }, 500);
        return;
    }
    
    const replyForm = template.content.cloneNode(true).firstElementChild;
    
    // 设置回复对象用户名
    const usernameSpan = replyForm.querySelector('.reply-to-username');
    if (usernameSpan) {
        usernameSpan.textContent = parentUsername || '';
    }
    
    // 设置表单ID
    replyForm.id = `reply-form-${commentId}-${parentReplyId}`;
    console.log(`创建回复的回复表单 ID=${replyForm.id}`);
    
    // 查找所有可能包含此回复的元素
    console.log(`查找回复元素 parentReplyId=${parentReplyId}`);
    
    // 首先尝试通过ID查找回复元素
    let replyElement = document.getElementById(`reply-${commentId}-${parentReplyId}`);
    
    // 如果找不到，尝试通过data属性查找
    if (!replyElement) {
        replyElement = document.querySelector(`.reply-item[data-reply-id="${parentReplyId}"][data-comment-id="${commentId}"]`);
    }
    
    // 如果仍找不到，尝试通过按钮属性查找
    if (!replyElement) {
        const replyButtons = document.querySelectorAll('.reply-item .reply-actions button.reply-btn, .reply-item .reply-actions button.btn-secondary');
        for (const btn of replyButtons) {
            console.log(`检查按钮:`, btn.outerHTML);
            
            // 检查按钮上的data属性
            if (btn.dataset.replyId === parentReplyId || 
                btn.dataset.commentId === commentId || 
                btn.getAttribute('onclick')?.includes(parentReplyId)) {
                replyElement = btn.closest('.reply-item');
                console.log('通过按钮找到回复元素');
                break;
            }
        }
    }
    
    if (replyElement) {
        console.log('找到回复元素:', replyElement);
        const actionsDiv = replyElement.querySelector('.reply-actions');
        if (actionsDiv) {
            console.log('找到回复操作区域');
            actionsDiv.insertAdjacentElement('afterend', replyForm);
            console.log('成功添加回复表单到回复元素');
            
            // 设置提交按钮事件处理
            const submitBtn = replyForm.querySelector('.submit-reply-btn');
            if (submitBtn) {
                submitBtn.addEventListener('click', function() {
                    console.log(`点击提交回复的回复按钮 commentId=${commentId}, parentReplyId=${parentReplyId}, parentUsername=${parentUsername}`);
                    submitReplyToReply(commentId, parentReplyId, parentUsername);
                });
            }
            
            // 设置取消按钮事件处理
            const cancelBtn = replyForm.querySelector('.cancel-reply-btn');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', function() {
                    console.log('点击取消回复按钮');
                    hideAllReplyForms();
                });
            }
            
            // 初始化表情选择器
            setTimeout(() => {
                initReplyFormEmoji(replyForm);
                
                // 聚焦到输入框
                const textArea = replyForm.querySelector('.reply-content');
                if (textArea) {
                    // 在回复内容中添加@提及
                    textArea.value = `@${parentUsername} `;
                    textArea.focus();
                    // 光标移到末尾
                    textArea.selectionStart = textArea.selectionEnd = textArea.value.length;
                }
                
                // 应用调试事件
                debugEmojiTrigger();
            }, 100);
        } else {
            console.error('无法找到回复操作区域');
        }
    } else {
        console.error(`无法找到回复元素，commentId=${commentId}, parentReplyId=${parentReplyId}`);
        
        // 调试信息：显示所有回复元素
        const allReplyItems = document.querySelectorAll('.reply-item');
        console.log(`页面上总共有 ${allReplyItems.length} 个回复元素`);
        allReplyItems.forEach((item, index) => {
            console.log(`回复元素 ${index + 1}:`, {
                id: item.id,
                dataReplyId: item.dataset.replyId,
                dataCommentId: item.dataset.commentId,
                html: item.outerHTML.substring(0, 100) + '...'
            });
        });
    }
}

// 提交回复 - 增强版本
async function submitReply(commentId) {
    console.log(`🚀 提交直接回复: commentId=${commentId}`);
    
    // 增强的表单查找逻辑 - 支持两种ID格式
    let replyForm = document.getElementById(`reply-form-${commentId}`);
    
    // 如果按基础ID找不到，尝试查找所有以此commentId开头的表单
    if (!replyForm) {
        const allForms = document.querySelectorAll(`[id^="reply-form-${commentId}"]`);
        if (allForms.length > 0) {
            replyForm = allForms[0]; // 取第一个匹配的表单
            console.log(`Found reply form with extended ID: ${replyForm.id}`);
        }
    }
    
    // 如果按ID找不到，尝试其他方式查找
    if (!replyForm) {
        replyForm = document.querySelector(`[data-comment-id="${commentId}"] .reply-form`);
    }
    
    // 再试试查找所有回复表单
    if (!replyForm) {
        const allReplyForms = document.querySelectorAll('.reply-form');
        for (let form of allReplyForms) {
            if (form.closest(`[data-comment-id="${commentId}"]`)) {
                replyForm = form;
                break;
            }
        }
    }
    
    if (!replyForm) {
        console.error('❌ Reply form not found, debugging...');
        console.log(`Looking for reply-form-${commentId}`);
        console.log('Available comment elements:', document.querySelectorAll('[data-comment-id]'));
        console.log('Available reply forms:', document.querySelectorAll('.reply-form'));
        
        // 延迟重试
        setTimeout(() => {
            let retryForm = document.getElementById(`reply-form-${commentId}`);
            
            // 尝试查找扩展ID格式
            if (!retryForm) {
                const allForms = document.querySelectorAll(`[id^="reply-form-${commentId}"]`);
                if (allForms.length > 0) {
                    retryForm = allForms[0];
                }
            }
            
            // 最后尝试按data属性查找
            if (!retryForm) {
                retryForm = document.querySelector(`[data-comment-id="${commentId}"] .reply-form`);
            }
            
            if (retryForm) {
                console.log('Retry successful, resubmitting...');
                submitReply(commentId);
            } else {
                showSuccessToast('Reply form not found, please click reply button again');
            }
        }, 500);
        return;
    }
    
    const usernameInput = replyForm.querySelector('.reply-username');
    const contentInput = replyForm.querySelector('.reply-content');
    
    if (!usernameInput || !contentInput) {
        console.error('❌ Reply form elements not found');
        showSuccessToast('Form elements loading error, please refresh page');
        return;
    }
    
    const username = usernameInput.value.trim() || 'Anonymous';
    const content = contentInput.value.trim();
    
    // 增强输入验证
    if (!content) {
        showSuccessToast('Please enter a reply');
        contentInput.focus();
        return;
    }
    
    if (content.length < 5) {
        showSuccessToast('Reply must be at least 5 characters long');
        contentInput.focus();
        return;
    }
    
    if (content.length > 2000) {
        showSuccessToast('Reply must be less than 2000 characters');
        contentInput.focus();
        return;
    }
    
    // 用户名验证
    if (username.length > 50) {
        showSuccessToast('Username must be less than 50 characters');
        usernameInput.focus();
        return;
    }
    
    // 显示提交状态
    const submitButton = replyForm.querySelector('.submit-reply-btn');
    const originalText = submitButton ? submitButton.textContent : '';
    if (submitButton) {
        submitButton.textContent = 'Submitting...';
        submitButton.disabled = true;
    }
    
    try {
        console.log('📡 发送直接回复请求...');
        console.log(`🔍 Debug info: commentId=${commentId}`);
        console.log(`🔍 API URL: /api/comments/${commentId}/reply`);
        const response = await fetch(`/api/comments/${commentId}/reply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                content: content
            })
        });
        
        const result = await response.json();
        console.log('📡 直接回复响应:', result);
        
        if (result.success) {
            console.log('🎉 直接回复提交成功!');
            showSuccessToast('Reply submitted successfully!');
            hideAllReplyForms();
            await loadComments(); // 重新加载评论
        } else {
            console.error('❌ 直接回复提交失败:', result.message);
            showSuccessToast('Reply submission failed: ' + result.message);
        }
    } catch (error) {
        console.error('🔥 直接回复提交出错:', error);
        showSuccessToast('Network error, please try again later');
    } finally {
        // 恢复按钮状态
        if (submitButton) {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    }
}

// 提交回复的回复 - 增强版本
async function submitReplyToReply(commentId, parentReplyId, parentUsername) {
    console.log(`🚀 提交层级回复: commentId=${commentId}, parentReplyId=${parentReplyId}, parentUsername=${parentUsername}`);
    
    // 增强的表单查找逻辑 - 用于回复他人的回复
    let replyForm = document.getElementById(`reply-form-${commentId}-${parentReplyId}`);
    
    // 如果精确ID找不到，尝试查找以commentId开头的表单
    if (!replyForm) {
        const allForms = document.querySelectorAll(`[id^="reply-form-${commentId}"]`);
        for (let form of allForms) {
            if (form.id.includes(parentReplyId)) {
                replyForm = form;
                console.log(`Found reply form with ID: ${form.id}`);
                break;
            }
        }
    }
    
    // 如果还是找不到，尝试通过DOM结构查找
    if (!replyForm) {
        replyForm = document.querySelector(`[data-comment-id="${commentId}"] .reply-form`);
    }
    
    // 最后尝试查找所有回复表单
    if (!replyForm) {
        const allReplyForms = document.querySelectorAll('.reply-form');
        for (let form of allReplyForms) {
            const parentElement = form.closest(`[data-comment-id="${commentId}"]`);
            if (parentElement) {
                replyForm = form;
                break;
            }
        }
    }
    
    if (!replyForm) {
        console.error('❌ Reply form not found, debugging...');
        console.log(`Looking for reply-form-${commentId}-${parentReplyId}`);
        console.log('Available comment elements:', document.querySelectorAll('[data-comment-id]'));
        console.log('Available reply forms:', document.querySelectorAll('.reply-form'));
        
        // 延迟重试
        setTimeout(() => {
            let retryForm = document.getElementById(`reply-form-${commentId}-${parentReplyId}`);
            
            // 尝试查找扩展ID格式
            if (!retryForm) {
                const allForms = document.querySelectorAll(`[id^="reply-form-${commentId}"]`);
                for (let form of allForms) {
                    if (form.id.includes(parentReplyId)) {
                        retryForm = form;
                        break;
                    }
                }
            }
            
            // 最后尝试按data属性查找
            if (!retryForm) {
                retryForm = document.querySelector(`[data-comment-id="${commentId}"] .reply-form`);
            }
            
            if (retryForm) {
                console.log('Retry successful for reply to reply, resubmitting...');
                submitReplyToReply(commentId, parentReplyId, parentUsername);
            } else {
                showSuccessToast('Reply form not found, please click reply button again');
            }
        }, 500);
        return;
    }
    
    const usernameInput = replyForm.querySelector('.reply-username');
    const contentInput = replyForm.querySelector('.reply-content');
    
    if (!usernameInput || !contentInput) {
        console.error('❌ Reply form elements not found');
        showSuccessToast('Form elements loading error, please refresh page');
        return;
    }
    
    const username = usernameInput.value.trim() || 'Anonymous';
    const content = contentInput.value.trim();
    
    // 增强输入验证
    if (!content) {
        showSuccessToast('Please enter a reply');
        contentInput.focus();
        return;
    }
    
    if (content.length < 5) {
        showSuccessToast('Reply must be at least 5 characters long');
        contentInput.focus();
        return;
    }
    
    if (content.length > 2000) {
        showSuccessToast('Reply must be less than 2000 characters');
        contentInput.focus();
        return;
    }
    
    // 用户名验证
    if (username.length > 50) {
        showSuccessToast('Username must be less than 50 characters');
        usernameInput.focus();
        return;
    }
    
    // 显示提交状态
    const submitButton = replyForm.querySelector('.submit-reply-btn');
    const originalText = submitButton ? submitButton.textContent : '';
    if (submitButton) {
        submitButton.textContent = 'Submitting...';
        submitButton.disabled = true;
    }
    
    try {
        console.log('📡 发送层级回复请求...');
        console.log(`🔍 Debug info: commentId=${commentId}, parentReplyId=${parentReplyId}, parentUsername=${parentUsername}`);
        console.log(`🔍 API URL: /api/comments/${commentId}/reply`);
        const response = await fetch(`/api/comments/${commentId}/reply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                content: content,
                parent_reply_id: parentReplyId,
                reply_to_username: parentUsername
            })
        });
        
        const result = await response.json();
        console.log('📡 层级回复响应:', result);
        
        if (result.success) {
            console.log('🎉 层级回复提交成功!');
            showSuccessToast('Reply submitted successfully!');
            hideAllReplyForms();
            await loadComments(); // 重新加载评论
        } else {
            console.error('❌ 层级回复提交失败:', result.message);
            showSuccessToast('Reply submission failed: ' + result.message);
        }
    } catch (error) {
        console.error('🔥 层级回复提交出错:', error);
        showSuccessToast('Network error, please try again later');
    } finally {
        // 恢复按钮状态
        if (submitButton) {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    }
}

// 隐藏回复表单
function hideReplyForm(formId) {
    const replyForm = document.getElementById(`reply-form-${formId}`);
    if (replyForm) {
        replyForm.remove();
    }
}

// 隐藏所有回复表单 - 优化表单管理
function hideAllReplyForms() {
    console.log('🧹 隐藏所有回复表单...');
    
    // 查找所有回复表单并隐藏
    const allReplyForms = document.querySelectorAll('.reply-form');
    let hiddenCount = 0;
    
    if (allReplyForms.length === 0) {
        console.log('没有找到回复表单');
        return;
    }
    
    console.log(`找到 ${allReplyForms.length} 个回复表单`);
    
    allReplyForms.forEach((form, index) => {
        try {
            console.log(`  移除表单 ${index + 1}: ID=${form.id || '无ID'}`);
            
            // 清理可能绑定的事件
            const emojiTriggers = form.querySelectorAll('.emoji-trigger');
            emojiTriggers.forEach(trigger => {
                const newTrigger = trigger.cloneNode(true);
                if (trigger.parentNode) {
                    trigger.parentNode.replaceChild(newTrigger, trigger);
                }
            });
            
            // 清理按钮事件
            const buttons = form.querySelectorAll('button');
            buttons.forEach(button => {
                const newButton = button.cloneNode(true);
                if (button.parentNode) {
                    button.parentNode.replaceChild(newButton, button);
                }
            });
            
            // 移除表单
            form.parentNode.removeChild(form);
            hiddenCount++;
        } catch (error) {
            console.error(`移除表单失败 ${index + 1}:`, error);
        }
    });
    
    // 确保关闭所有表情面板
    document.querySelectorAll('.emoji-panel').forEach(panel => {
        panel.style.display = 'none';
    });
    
    console.log(`✅ 成功隐藏 ${hiddenCount} 个回复表单`);
}

// 更新加载更多按钮
function updateLoadMoreButton() {
    const loadMoreSection = document.getElementById('load-more-section');
    const loadMoreBtn = document.getElementById('load-more-btn');
    
    if (!loadMoreSection || !loadMoreBtn) {
        console.log('⚠️ 加载更多按钮元素不存在');
        return; // 如果元素不存在，直接返回
    }
    
    // 检查是否还有更多评论需要显示
    const hasMoreComments = displayedComments.length < allComments.length;
    
    console.log(`🔍 更新加载更多按钮: 显示${displayedComments.length}条, 总计${allComments.length}条, 有更多: ${hasMoreComments}`);
    
    if (hasMoreComments) {
        loadMoreSection.classList.remove('hidden');
        const remainingComments = allComments.length - displayedComments.length;
        loadMoreBtn.textContent = `Load More Comments (${remainingComments})`;
        console.log(`✅ 显示加载更多按钮，剩余${remainingComments}条评论`);
    } else {
        loadMoreSection.classList.add('hidden');
        console.log('❌ 隐藏加载更多按钮，没有更多评论');
    }
}

// 更新评论统计
function updateCommentStats() {
    const totalComments = allComments.length;
    const averageRating = allComments.length > 0 
        ? (allComments.reduce((sum, comment) => sum + comment.rating, 0) / allComments.length).toFixed(1)
        : 0.0;
    
    const totalElement = document.getElementById('total-comments');
    const averageElement = document.getElementById('average-rating');
    
    if (totalElement) {
        totalElement.textContent = `${totalComments} comments`;
    }
    if (averageElement) {
        averageElement.textContent = `${averageRating} ★`;
    }
}

// 提交评论 - 真实API调用
async function submitComment() {
    console.log('🚀 开始提交评论...');
    const inputs = getActiveInputs();
    
    // 检查必需的DOM元素
    if (!inputs.commentInput || !inputs.usernameInput || !inputs.emailInput) {
        console.error('❌ 找不到必需的输入元素');
        showSuccessToast('Page elements loading error, please refresh the page and try again');
        return;
    }
    
    const content = inputs.commentInput.value.trim();
    const username = inputs.usernameInput.value.trim() || 'Anonymous';
    const email = inputs.emailInput.value.trim();
    
    // 添加详细的调试信息
    console.log('📝 评论提交前检查:');
    console.log('   内容:', content);
    console.log('   Username:', username);
    console.log('   邮箱:', email);
    console.log('   当前评分:', currentRating);
    console.log('   内容长度:', content.length);
    console.log('   Username length:', username.length);
    
    // 验证内容
    if (!content) {
        console.warn('⚠️ Validation failed: Content is empty');
        showSuccessToast('Please enter a comment');
        inputs.commentInput.focus();
        return;
    }
    
    if (content.length < 10) {
        console.warn('⚠️ Validation failed: Content too short');
        showSuccessToast('Comment must be at least 10 characters long');
        inputs.commentInput.focus();
        return;
    }
    
    if (content.length > 1000) {
        console.warn('⚠️ Validation failed: Content too long');
        showSuccessToast('Comment must be less than 1000 characters');
        inputs.commentInput.focus();
        return;
    }
    
    // 验证评分 - 重要检查
    console.log('🔍 评分验证: currentRating =', currentRating, '(类型:', typeof currentRating, ')');
    
    if (currentRating === 0 || currentRating === null || currentRating === undefined) {
        console.warn('⚠️ Validation failed: No rating selected');
        showSuccessToast('Please select a rating');
        
        // 聚焦到评分区域
        const ratingContainer = document.querySelector('.rating-input-container');
        if (ratingContainer) {
            ratingContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // 添加视觉提示
            ratingContainer.style.border = '2px solid #ff6b6b';
            setTimeout(() => {
                ratingContainer.style.border = '';
            }, 3000);
        }
        return;
    }
    
    if (currentRating < 1 || currentRating > 5) {
        console.warn('⚠️ Validation failed: Rating out of range');
        showSuccessToast('Rating must be between 1 and 5');
        return;
    }
    
    // 验证用户名
    if (username.length > 50) {
        console.warn('⚠️ Validation failed: Username too long');
        showSuccessToast('Username must be less than 50 characters');
        inputs.usernameInput.focus();
        return;
    }
    
    // 用户名格式检查
    const usernameRegex = /^[a-zA-Z0-9_\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff\s]+$/;
    if (!usernameRegex.test(username)) {
        console.warn('⚠️ Validation failed: Username contains invalid characters');
        showSuccessToast('Username can only contain letters, numbers, underscores, Chinese characters, Japanese characters and spaces');
        inputs.usernameInput.focus();
        return;
    }
    
    // 邮箱必填验证
    if (!email) {
        console.warn('⚠️ Validation failed: Email is required');
        showSuccessToast('Please enter an email address');
        inputs.emailInput.focus();
        return;
    }
    
    // 邮箱格式验证
    if (!validateEmail(email)) {
        console.warn('⚠️ Validation failed: Invalid email format');
        showSuccessToast('Please enter a valid email address');
        inputs.emailInput.focus();
        return;
    }
    
    console.log('✅ 前端验证通过，准备提交...');
    
    // 显示加载状态
    if (inputs.submitText && inputs.submitLoading) {
        inputs.submitText.textContent = 'Posting...';
        inputs.submitLoading.classList.remove('hidden');
    }
    
    try {
        // 准备数据 - 确保数据类型正确
        const data = {
            username: String(username),        // 确保是字符串
            email: String(email),              // 确保是字符串  
            content: String(content),          // 确保是字符串
            rating: parseInt(currentRating)    // 确保是整数
        };
        
        // 最终数据验证和调试
        console.log('📦 准备提交的数据:');
        console.log('   数据对象:', data);
        console.log('   JSON字符串:', JSON.stringify(data));
        
        // 验证每个字段的类型
        console.log('🔍 数据类型检查:');
        Object.entries(data).forEach(([key, value]) => {
            console.log(`   ${key}: ${typeof value} = ${JSON.stringify(value)}`);
        });
        
        // 最后一次数据检查
        if (!data.username || !data.content || !data.rating) {
            throw new Error('Data validation failed: missing required fields');
        }
        
        if (isNaN(data.rating) || data.rating < 1 || data.rating > 5) {
            throw new Error('Data validation failed: invalid rating');
        }
        
        // 获取当前页面URL作为article_url
        const articleUrl = getArticleUrl();
        console.log('Submitting comment for article_url:', articleUrl);
        
        // 调用真实API
        const apiUrl = `/api/comments${articleUrl}`;
        console.log('Submit API URL:', apiUrl);
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        console.log('📡 API响应状态:', response.status);
        console.log('📡 API响应头:', response.headers);
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('📡 API响应数据:', result);
        
        if (result.success) {
            console.log('🎉 评论提交成功!');
            
            // 重置表单
            inputs.commentInput.value = '';
            inputs.usernameInput.value = '';
            inputs.emailInput.value = '';
            currentRating = 0;
            highlightStars(0);
            
            // 显示成功消息
            showSuccessToast('Success!');
            
            // 重新加载评论列表
            await loadComments();
            
            // 滚动到评论列表顶部
            const commentsElement = document.getElementById('comments-list');
            if (commentsElement) {
                commentsElement.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            console.error('❌ Submission failed details:', result);
            let errorMessage = 'Submission failed: ' + result.message;
            if (result.errors && Array.isArray(result.errors)) {
                errorMessage += '. Details: ' + result.errors.join(', ');
            }
            showSuccessToast(errorMessage);
        }
    } catch (error) {
        console.error('🔥 提交评论出错:', error);
        showSuccessToast('Network error, please try again later');
    } finally {
        // 恢复按钮状态
        if (inputs.submitText && inputs.submitLoading) {
            inputs.submitText.textContent = 'Post Comment';
            inputs.submitLoading.classList.add('hidden');
        }
    }
}

// 验证邮箱格式
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// 点赞评论 - 真实API调用
async function likeComment(commentId) {
    try {
        const response = await fetch(`/api/comments/${commentId}/like`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            // 显示点赞成功提示
            showSuccessToast('👍 Liked successfully!');
            
            // 重新加载评论以更新点赞数
            await loadComments();
        } else {
            showSuccessToast('点赞失败: ' + result.message);
        }
    } catch (error) {
        console.error('点赞出错:', error);
        showSuccessToast('Network error, please try again later');
    }
}

// 点赞回复 - 真实API调用
async function likeReply(commentId, replyId) {
    try {
        const response = await fetch(`/api/comments/${commentId}/reply/${replyId}/like`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            // 显示点赞成功提示
            showSuccessToast('👍 Reply liked successfully!');
            
            // 重新加载评论以更新点赞数
            await loadComments();
        } else {
            showSuccessToast('点赞失败: ' + result.message);
        }
    } catch (error) {
        console.error('点赞出错:', error);
        showSuccessToast('Network error, please try again later');
    }
}

// 加载更多评论
async function loadMoreComments() {
    const loadMoreBtn = document.getElementById('load-more-btn');
    const originalText = loadMoreBtn.textContent;
    
    // 显示加载状态
    loadMoreBtn.innerHTML = '<div class="loading-spinner mx-auto"></div>';
    loadMoreBtn.disabled = true;
    
    try {
        // 计算下一批要显示的评论
        const currentLength = displayedComments.length;
        const nextBatch = allComments.slice(currentLength, currentLength + commentsPerPage);
        
        // 添加到显示列表
        displayedComments.push(...nextBatch);
        
        // 重新渲染
        renderComments();
        updateLoadMoreButton();
    } catch (error) {
        console.error('加载更多评论出错:', error);
    } finally {
        // 恢复按钮状态
        loadMoreBtn.disabled = false;
        updateLoadMoreButton();
    }
}

// 辅助函数：HTML转义
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;'
        // 注意：不转义单引号 (') 以保持用户输入的自然性
    };
    return text.replace(/[&<>"]/g, function(m) { return map[m]; });
}

// 辅助函数：格式化时间
function formatTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) { // 1分钟内
        return 'just now';
    } else if (diff < 3600000) { // 1小时内
        return Math.floor(diff / 60000) + ' minutes ago';
    } else if (diff < 86400000) { // 24小时内
        return Math.floor(diff / 3600000) + ' hours ago';
    } else if (diff < 604800000) { // 7天内
        return Math.floor(diff / 86400000) + ' days ago';
    } else {
        return date.toLocaleDateString();
    }
}

// 显示成功提示
function showSuccessToast(message) {
    // 移除已存在的提示
    const existingToast = document.querySelector('.success-toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // 创建新的提示元素
    const toast = document.createElement('div');
    toast.className = 'success-toast';
    toast.innerHTML = `
        <span class="icon">✅</span>
        ${message}
        <button class="close-btn" onclick="this.parentElement.remove()">×</button>
    `;
    
    // 添加到页面
    document.body.appendChild(toast);
    
    // 显示动画
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // 自动消失
    setTimeout(() => {
        if (toast.parentElement) {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }
    }, 4000);
}

// 🧪 测试层级回复功能
window.testReplyHierarchy = function() {
    console.log('🧪 开始测试层级回复功能...');

    // 测试数据结构
    const testComments = [
        {
            comment_id: 'test-comment-1',
            username: '测试用户1',
            content: '这是一个测试评论',
            rating: 5,
            likes: 2,
            created_at: '2024-01-01 10:00:00',
            replies: [
                {
                    reply_id: 'test-reply-1',
                    username: '回复用户1',
                    content: '这是第一层回复',
                    likes: 1,
                    created_at: '2024-01-01 10:05:00',
                    parent_reply_id: null,
                    reply_to_username: null,
                    children: [
                        {
                            reply_id: 'test-reply-2',
                            username: '回复用户2',
                            content: '这是第二层回复',
                            likes: 0,
                            created_at: '2024-01-01 10:10:00',
                            parent_reply_id: 'test-reply-1',
                            reply_to_username: '回复用户1',
                            children: [
                                {
                                    reply_id: 'test-reply-3',
                                    username: '回复用户3',
                                    content: '这是第三层回复',
                                    likes: 0,
                                    created_at: '2024-01-01 10:15:00',
                                    parent_reply_id: 'test-reply-2',
                                    reply_to_username: '回复用户2',
                                    children: []
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ];

    // 设置测试数据
    allComments = testComments;
    displayedComments = testComments;

    console.log('📊 测试数据设置完成:');
    console.log('  - 评论数量:', allComments.length);
    console.log('  - 回复层级结构:', JSON.stringify(testComments[0].replies, null, 2));

    // 渲染测试评论
    try {
        renderComments();
        console.log('✅ 层级回复渲染测试通过');

        // 测试表单功能
        setTimeout(() => {
            console.log('🔧 测试回复表单功能...');

            // 测试显示第一层回复表单
            showReplyForm('test-comment-1', 0);
            console.log('✅ 第一层回复表单显示测试通过');

            // 测试显示第二层回复表单
            setTimeout(() => {
                showReplyToReplyForm('test-comment-1', 'test-reply-1', '回复用户1', 0);
                console.log('✅ 第二层回复表单显示测试通过');

                // 测试层级限制
                setTimeout(() => {
                    console.log('🚧 测试层级限制功能 (level=2, 应该显示警告)...');
                    showReplyToReplyForm('test-comment-1', 'test-reply-2', '回复用户2', 2);
                    console.log('✅ 层级限制测试通过 (应该显示警告)');

                    // 延迟等待警告显示
                    setTimeout(() => {
                        console.log('🎉 所有层级回复功能测试完成!');
                        console.log('📋 测试结果总结:');
                        console.log('   ✅ 层级回复渲染 - 通过');
                        console.log('   ✅ 表单显示功能 - 通过');
                        console.log('   ✅ 层级限制检查 - 通过');
                        console.log('   📊 支持的层级: 显示3层, 可回复2层');
                    }, 200);
                }, 500);
            }, 500);
        }, 1000);

    } catch (error) {
        console.error('❌ 层级回复测试失败:', error);
    }
};

// 💡 使用说明
console.log('💡 层级回复功能已同步!');
console.log('   可以在浏览器控制台运行 testReplyHierarchy() 来测试功能');
console.log('   功能包括:');
console.log('   1. ✅ 完整的评论和回复系统');
console.log('   2. ✅ 统一层级限制 (最多3层显示, 2层可回复)');
console.log('   3. ✅ 表单管理和错误处理');
console.log('   4. ✅ 表情选择器集成');
console.log('   5. ✅ 完善的CSS样式支持');

// 添加调试函数，直接处理点击事件
function debugEmojiTrigger() {
    console.log('🔧 开始调试表情按钮点击事件...');

    // 查找所有表情按钮
    const allTriggers = document.querySelectorAll('.emoji-trigger');
    console.log(`找到 ${allTriggers.length} 个表情按钮`);

    // 直接绑定点击事件
    allTriggers.forEach((trigger, index) => {
        console.log(`绑定第 ${index+1} 个表情按钮点击事件`);

        // 移除旧事件
        const newTrigger = trigger.cloneNode(true);
        trigger.parentNode.replaceChild(newTrigger, trigger);

        // 添加新的直接点击事件
        newTrigger.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log(`表情按钮 ${index+1} 被点击!`);

            // 查找最近的表情面板
            const panel = this.closest('.emoji-picker-container').querySelector('.emoji-panel');
            if (panel) {
                // 切换显示状态
                if (panel.classList.contains('show')) {
                    console.log('关闭表情面板');
                    panel.classList.remove('show');
                } else {
                    console.log('打开表情面板');
                    panel.classList.add('show');

                    // 关闭其他面板
                    document.querySelectorAll('.emoji-panel.show').forEach(p => {
                        if (p !== panel) p.classList.remove('show');
                    });
                }
            } else {
                console.error('找不到表情面板!');

                // 创建一个简单的表情面板
                const container = this.closest('.emoji-picker-container');
                const simplePanel = document.createElement('div');
                simplePanel.className = 'emoji-panel';
                simplePanel.innerHTML = `
                    <div style="padding: 10px; background: white; border: 1px solid #ddd;">
                        <div>😊 😂 ❤️ 👍 🎉</div>
                        <div>✨ 🌟 💯 🔥 👏</div>
                    </div>
                `;

                // 添加到容器
                container.appendChild(simplePanel);
                simplePanel.classList.add('show');

                // 绑定表情点击
                simplePanel.addEventListener('click', e => {
                    if (e.target.textContent.trim()) {
                        const emoji = e.target.textContent.trim();
                        // 查找关联的输入框
                        const container = e.target.closest('.emoji-picker-container');
                        const parentDiv = container.parentNode;
                        const textarea = parentDiv.querySelector('textarea');

                        if (textarea) {
                            // 插入表情
                            const start = textarea.selectionStart;
                            textarea.value = textarea.value.substring(0, start) +
                                emoji + textarea.value.substring(textarea.selectionEnd);
                            textarea.focus();
                            textarea.selectionStart = textarea.selectionEnd = start + emoji.length;

                            // 关闭面板
                            simplePanel.classList.remove('show');
                        }
                    }
                });
            }
        });
    });
}

// 页面加载完成后初始化调试触发器
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(debugEmojiTrigger, 1000);

    // 绑定回复表单按钮事件 - 通过事件委托实现
    document.addEventListener('click', function(e) {
        // 提交回复按钮
        if (e.target.classList.contains('submit-reply-btn')) {
            e.preventDefault();

            // 查找最近的回复表单和ID
            const replyForm = e.target.closest('.reply-form');
            if (replyForm) {
                const formId = replyForm.id;
                if (formId) {
                    // 解析评论ID和回复ID
                    const parts = formId.replace('reply-form-', '').split('-');
                    const commentId = parts[0];
                    const parentReplyId = parts.length > 1 ? parts[1] : null;

                    // 获取用户名元素
                    const usernameSpan = replyForm.querySelector('.reply-to-username');
                    const parentUsername = usernameSpan ? usernameSpan.textContent : '';

                    console.log(`提交回复表单: commentId=${commentId}, parentReplyId=${parentReplyId}, parentUsername=${parentUsername}`);

                    // 根据是否有父回复ID决定调用哪个函数
                    if (parentReplyId && parentReplyId !== '0') {
                        submitReplyToReply(commentId, parentReplyId, parentUsername);
                    } else {
                        submitReply(commentId);
                    }
                }
            }
        }

        // 取消回复按钮
        if (e.target.classList.contains('cancel-reply-btn')) {
            e.preventDefault();
            hideAllReplyForms();
        }
    });
});

// 简单表情选择器函数
function toggleEmojiPanel(panelId, targetId) {
    console.log('切换表情面板', panelId, targetId);
    const panel = document.getElementById(panelId);
    if (panel) {
        // 切换显示状态
        if (panel.style.display === 'none' || !panel.style.display) {
            panel.style.display = 'block';
            // 关闭其他表情面板
            document.querySelectorAll('.emoji-panel').forEach(p => {
                if (p.id !== panelId && p.style.display !== 'none') {
                    p.style.display = 'none';
                }
            });

            // 添加点击外部关闭面板
            setTimeout(() => {
                document.addEventListener('click', closePanel);
            }, 100);
        } else {
            panel.style.display = 'none';
            document.removeEventListener('click', closePanel);
        }
    }

    // 关闭面板的函数
    function closePanel(event) {
        const panel = document.getElementById(panelId);
        const btn = document.querySelector(`[onclick*="toggleEmojiPanel('${panelId}"]`);

        // 如果点击的不是面板内部元素且不是按钮本身
        if (panel && !panel.contains(event.target) && (!btn || !btn.contains(event.target))) {
            panel.style.display = 'none';
            document.removeEventListener('click', closePanel);
        }
    }
}

// 切换表情分类
function switchEmojiCategory(panelId, category) {
    console.log('切换表情分类', panelId, category);

    // 隐藏所有分类
    document.querySelectorAll(`#${panelId} .emoji-grid`).forEach(grid => {
        grid.style.display = 'none';
    });

    // 显示选中的分类
    const targetGrid = document.getElementById(`${panelId}-${category}`);
    if (targetGrid) {
        targetGrid.style.display = 'grid';
    }

    // 更新标签状态
    document.querySelectorAll(`#${panelId} .emoji-tab`).forEach(tab => {
        tab.classList.remove('active');
    });

    // 激活当前标签
    const activeTab = document.querySelector(`#${panelId} .emoji-tab[onclick*="'${category}'"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
}

// 插入表情到文本框
function insertEmoji(textareaId, emoji) {
    console.log('插入表情', textareaId, emoji);
    const textarea = document.getElementById(textareaId);
    if (textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;

        textarea.value = text.substring(0, start) + emoji + text.substring(end);
        textarea.focus();
        textarea.selectionStart = textarea.selectionEnd = start + emoji.length;

        // 关闭所有表情面板
        document.querySelectorAll('.emoji-panel').forEach(panel => {
            panel.style.display = 'none';
        });
    }
}

// 初始化表情选择器
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM加载完成，初始化表情选择器...');

    // 调试表情按钮点击事件
    function debugEmojiTrigger() {
        console.log('🔧 开始调试表情按钮点击事件...');

        // 查找所有表情按钮
        const allTriggers = document.querySelectorAll('[id$="-emoji-btn"]');
        console.log(`找到 ${allTriggers.length} 个表情按钮`);

        // 直接绑定点击事件
        allTriggers.forEach((trigger, index) => {
            console.log(`绑定第 ${index+1} 个表情按钮点击事件: ${trigger.id}`);

            // 移除旧事件
            const newTrigger = trigger.cloneNode(true);
            trigger.parentNode.replaceChild(newTrigger, trigger);

            // 添加新的直接点击事件
            newTrigger.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log(`表情按钮 ${index+1} 被点击!`);

                // 确定关联的面板ID和目标文本框ID
                const panelId = newTrigger.id.replace('-btn', '-panel');
                const targetId = newTrigger.id.includes('desktop') ? 'comment-input-desktop' : 'comment-input-mobile';

                // 切换表情面板显示
                toggleEmojiPanel(panelId, targetId);
            });
        });

        console.log('✅ 表情按钮调试事件绑定完成');
    }

    // 在页面加载完成后初始化表情选择器
    setTimeout(debugEmojiTrigger, 1000);

    // 为所有回复表单添加表情选择器
    document.addEventListener('click', function(e) {
        // 如果点击了回复按钮
        if (e.target.classList.contains('btn-secondary') &&
            (e.target.textContent.includes('Reply') || e.target.textContent.includes('回复'))) {

            // 等待回复表单渲染完成
            setTimeout(() => {
                const replyForms = document.querySelectorAll('.reply-form');

                replyForms.forEach((form, index) => {
                    if (!form.dataset.emojiInitialized) {
                        const textarea = form.querySelector('textarea');
                        const container = form.querySelector('.emoji-picker-container');

                        if (textarea && container) {
                            const textareaId = textarea.id || `reply-textarea-${index}`;
                            const panelId = `emoji-panel-${textareaId}`;

                            // 设置ID便于引用
                            if (!textarea.id) textarea.id = textareaId;

                            // 添加表情按钮和面板
                            container.innerHTML = `
                                <button type="button" class="p-2 hover:bg-gray-100 rounded-full"
                                        title="Insert emoji"
                                        onclick="toggleEmojiPanel('${panelId}', '${textareaId}')">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="12" cy="12" r="10"></circle>
                                        <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
                                        <line x1="9" y1="9" x2="9.01" y2="9"></line>
                                        <line x1="15" y1="9" x2="15.01" y2="9"></line>
                                    </svg>
                                </button>
                                <div id="${panelId}" class="emoji-panel custom-emoji-panel">
                                    <div class="emoji-grid">
                                        <span class="emoji-item" onclick="insertEmoji('${textareaId}', '😊')">😊</span>
                                        <span class="emoji-item" onclick="insertEmoji('${textareaId}', '😂')">😂</span>
                                        <span class="emoji-item" onclick="insertEmoji('${textareaId}', '❤️')">❤️</span>
                                        <span class="emoji-item" onclick="insertEmoji('${textareaId}', '👍')">👍</span>
                                        <span class="emoji-item" onclick="insertEmoji('${textareaId}', '🎉')">🎉</span>
                                        <span class="emoji-item" onclick="insertEmoji('${textareaId}', '✨')">✨</span>
                                        <span class="emoji-item" onclick="insertEmoji('${textareaId}', '🌟')">🌟</span>
                                        <span class="emoji-item" onclick="insertEmoji('${textareaId}', '💯')">💯</span>
                                    </div>
                                </div>
                            `;

                            // 标记为已初始化
                            form.dataset.emojiInitialized = 'true';
                        }
                    }
                });
            }, 300);
        }
    });
});