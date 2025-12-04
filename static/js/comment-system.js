/**
 * 评论系统前端JS库 (新版)
 * 提供评论的增删改查、点赞、回复等功能
 */

// 防止与旧版系统冲突
if (window.commentSystemLoaded) {
    console.warn('⚠️ Comment system already loaded, skipping...');
} else {
    window.commentSystemLoaded = true;
    console.log('✅ Loading new comment-system.js');
}

class CommentSystem {
    constructor(options = {}) {
        // 检测并禁用旧版评论系统
        if (window.OLD_COMMENT_SYSTEM_DISABLED !== undefined) {
            window.OLD_COMMENT_SYSTEM_DISABLED = true;
            console.log('🔄 Disabling old comment system from new comment-system.js');
        }
        
        this.articleUrl = options.articleUrl || window.location.pathname;
        this.containerId = options.containerId || 'comment-system';
        this.apiBase = options.apiBase || '/api/comments';
        this.perPage = options.perPage || 10;
        this.currentPage = 1;
        this.sortBy = options.sortBy || 'created_at';
        this.enableReply = options.enableReply !== false;
        this.enableLike = options.enableLike !== false;
        this.enableRating = options.enableRating !== false;
        
        // 绑定this上下文
        this.loadComments = this.loadComments.bind(this);
        this.submitComment = this.submitComment.bind(this);
        this.likeComment = this.likeComment.bind(this);
        this.showReplyForm = this.showReplyForm.bind(this);
        this.submitReply = this.submitReply.bind(this);
        
        this.init();
    }
    
    init() {
        this.createContainer();
        this.loadComments();
        this.loadStats();
    }
    
    createContainer() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with id "${this.containerId}" not found`);
            return;
        }
        
        container.innerHTML = `
            <div class="comment-system">
                <div class="comment-stats" id="comment-stats"></div>
                <div class="comment-form-container">
                    <h3>发表评论</h3>
                    <form id="comment-form" class="comment-form">
                        <div class="form-group">
                            <label for="username">Username *</label>
                            <input type="text" id="username" name="username" required maxlength="50">
                        </div>
                        <div class="form-group">
                            <label for="email">邮箱 *</label>
                            <input type="email" id="email" name="email" required maxlength="100">
                        </div>
                        ${this.enableRating ? `
                        <div class="form-group">
                            <label for="rating">评分 *</label>
                            <div class="rating-container">
                                <select id="rating" name="rating" required>
                                    <option value="5" selected>⭐⭐⭐⭐⭐ 非常好</option>
                                    <option value="4">⭐⭐⭐⭐ 很好</option>
                                    <option value="3">⭐⭐⭐ 一般</option>
                                    <option value="2">⭐⭐ 不太好</option>
                                    <option value="1">⭐ 很差</option>
                                </select>
                            </div>
                        </div>
                        ` : ''}
                        <div class="form-group">
                                            <label for="content">Comment Content *</label>
                <textarea id="content" name="content" required minlength="10" maxlength="2000" 
                placeholder="Please enter your comment..."></textarea>
                            <div class="char-counter">
                                <span id="char-count">0</span>/2000
                            </div>
                        </div>
                        <button type="submit" class="submit-btn">提交评论</button>
                    </form>
                </div>
                <div class="comment-section">
                    <div class="comment-header">
                        <h3>评论列表</h3>
                        <div class="comment-controls">
                            <select id="sort-select" class="sort-select">
                                <option value="created_at">最新</option>
                                <option value="likes">最热</option>
                            </select>
                        </div>
                    </div>
                    <div id="comment-list" class="comment-list"></div>
                    <div id="comment-pagination" class="pagination"></div>
                </div>
            </div>
        `;
        
        this.bindEvents();
        this.setDefaultRating();
    }
    
    setDefaultRating() {
        // 设置评分默认为五星
        const ratingSelect = document.getElementById('rating');
        if (ratingSelect) {
            ratingSelect.value = '5';
        }
    }
    
    bindEvents() {
        // 评论表单提交
        const commentForm = document.getElementById('comment-form');
        if (commentForm) {
            commentForm.addEventListener('submit', this.submitComment);
        }
        
        // 字符计数
        const contentTextarea = document.getElementById('content');
        if (contentTextarea) {
            contentTextarea.addEventListener('input', this.updateCharCount);
        }
        
        // 排序选择
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortBy = e.target.value;
                this.currentPage = 1;
                this.loadComments();
            });
        }
    }
    
    updateCharCount() {
        const content = document.getElementById('content').value;
        const charCount = document.getElementById('char-count');
        if (charCount) {
            charCount.textContent = content.length;
            if (content.length > 2000) {
                charCount.style.color = 'red';
            } else {
                charCount.style.color = '#666';
            }
        }
    }
    
    async loadComments() {
        try {
            this.showLoading();
            
            const url = `${this.apiBase}${this.articleUrl}?` +
                       `page=${this.currentPage}&per_page=${this.perPage}&sort_by=${this.sortBy}`;
            
            console.log('🔍 Loading comments from URL:', url);
            
            const response = await fetch(url);
            const result = await response.json();
            
            console.log('📦 API Response:', result);
            
            if (result.success) {
                this.renderComments(result.data);
                this.renderPagination(result.pagination);
            } else {
                this.showError('加载评论失败: ' + result.message);
            }
        } catch (error) {
            console.error('❌ Error loading comments:', error);
            this.showError('Network error, please try again later');
        }
    }
    
    async loadStats() {
        try {
            const url = `${this.apiBase}${this.articleUrl}/stats`;
            console.log('📊 Loading stats from URL:', url);
            
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success) {
                this.renderStats(result.data);
            }
        } catch (error) {
            console.error('Failed to load comment stats:', error);
        }
    }
    
    async submitComment(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const data = {
            username: formData.get('username'),
            email: formData.get('email'),
            content: formData.get('content')
        };
        
        if (this.enableRating) {
            data.rating = parseInt(formData.get('rating'));
        } else {
            data.rating = 5; // 默认评分
        }
        
        // 前端数据验证和调试
        console.log('📤 提交评论数据:', data);
        
        // 前端基础验证
        const validation = this.validateCommentData(data);
        if (!validation.valid) {
            this.showError('Data validation failed: ' + validation.errors.join(', '));
            return;
        }
        
        try {
            const submitUrl = `${this.apiBase}${this.articleUrl}`;
            console.log('📤 Submitting comment to:', submitUrl);
            console.log('📝 Comment data:', data);
            
            const response = await fetch(submitUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            console.log('📥 Response status:', response.status);
            console.log('📥 Response headers:', Object.fromEntries(response.headers));
            
            const result = await response.json();
            console.log('✅ Submit response:', result);
            
            if (result.success) {
                this.showSuccess('评论提交成功！');
                form.reset();
                this.updateCharCount();
                this.loadComments(); // 重新加载评论列表以显示新评论
                this.loadStats(); // 重新加载统计
            } else {
                console.error('❌ 服务器返回错误:', result);
                let errorMessage = result.message || '提交失败';
                if (result.errors && result.errors.length > 0) {
                    errorMessage += ': ' + result.errors.join(', ');
                }
                this.showError(errorMessage);
            }
        } catch (error) {
            console.error('❌ Submit error:', error);
            this.showError('Network error, please try again later');
        }
    }
    
    // 新增：前端数据验证
    validateCommentData(data) {
        const errors = [];
        
        // 检查用户名
        if (!data.username || data.username.trim() === '') {
            errors.push('Username cannot be empty');
        } else if (data.username.length > 50) {
            errors.push('Username cannot exceed 50 characters');
        } else if (!/^[a-zA-Z0-9_\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff\s]+$/.test(data.username)) {
            errors.push('Username can only contain letters, numbers, underscores, Chinese characters, Japanese characters and spaces');
        }
        
        // 检查内容
        if (!data.content || data.content.trim() === '') {
            errors.push('Comment content cannot be empty');
        } else if (data.content.length < 10) {
            errors.push('Comment content must be at least 10 characters');
        } else if (data.content.length > 2000) {
            errors.push('Comment content cannot exceed 2000 characters');
        }
        
        // 检查评分
        if (!data.rating || isNaN(data.rating)) {
            errors.push('请选择评分');
        } else if (data.rating < 1 || data.rating > 5) {
            errors.push('评分必须在1-5之间');
        }
        
        // 检查邮箱（必填）
        if (!data.email || data.email.trim() === '') {
            errors.push('Email is required');
        } else {
            const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            if (!emailRegex.test(data.email)) {
                errors.push('Invalid email format');
            }
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }
    
    async likeComment(commentId, isReply = false, replyId = null) {
        try {
            // 检查是否已经点赞过（使用localStorage记录）
            const likeKey = isReply ? `like_reply_${replyId}` : `like_comment_${commentId}`;
            if (localStorage.getItem(likeKey)) {
                this.showError('您已经点赞过了！');
                return;
            }

            const url = isReply ? 
                `${this.apiBase}/${commentId}/reply/${replyId}/like` :
                `${this.apiBase}/${commentId}/like`;
            
            // 获取点赞按钮并添加加载状态
            const likeBtn = isReply ? 
                document.querySelector(`[data-reply-id="${replyId}"] .like-btn`) :
                document.querySelector(`[data-comment-id="${commentId}"] .like-btn`);
            
            if (likeBtn) {
                likeBtn.disabled = true;
                const originalText = likeBtn.innerHTML;
                likeBtn.innerHTML = '<div class="loading-spinner"></div>';
            }

            const response = await fetch(url, { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                // 记录点赞状态到localStorage
                localStorage.setItem(likeKey, 'true');
                
                // 更新点赞数显示并添加动画效果
                if (likeBtn) {
                    const likeCount = likeBtn.querySelector('.like-count');
                    if (likeCount) {
                        // 添加点赞动画
                        likeBtn.classList.add('liked', 'like-animation');
                        likeCount.textContent = result.data.likes;
                        
                        // 移除动画类
                        setTimeout(() => {
                            likeBtn.classList.remove('like-animation');
                        }, 300);
                    }
                    likeBtn.disabled = true; // 保持禁用状态
                    likeBtn.innerHTML = `👍 <span class="like-count">${result.data.likes}</span>`;
                }
                
                this.showSuccess('点赞成功！');
            } else {
                this.showError('点赞失败: ' + result.message);
                // 恢复按钮状态
                if (likeBtn) {
                    likeBtn.disabled = false;
                    likeBtn.innerHTML = originalText;
                }
            }
        } catch (error) {
            this.showError('Network error, please try again later');
            // 恢复按钮状态
            const likeBtn = isReply ? 
                document.querySelector(`[data-reply-id="${replyId}"] .like-btn`) :
                document.querySelector(`[data-comment-id="${commentId}"] .like-btn`);
            if (likeBtn) {
                likeBtn.disabled = false;
            }
        }
    }
    
    // 新增：检查点赞状态
    checkLikeStatus(commentId, isReply = false, replyId = null) {
        const likeKey = isReply ? `like_reply_${replyId}` : `like_comment_${commentId}`;
        return localStorage.getItem(likeKey) === 'true';
    }
    
    showReplyForm(commentId, level = 0) {
        // 限制回复层级最多3层
        if (level >= 3) {
            this.showError('Reply level too deep, please reply in comment area');
            return;
        }
        
        // 增强的表单查找逻辑：尝试多种查找方式
        let replyForm = document.getElementById(`reply-form-${commentId}`);
        
        // 如果按ID找不到，尝试按class和data属性查找
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
        
        if (replyForm) {
            // 确保表单有正确的ID
            if (!replyForm.id) {
                replyForm.id = `reply-form-${commentId}`;
            }
            
            const isVisible = replyForm.style.display === 'block';
            replyForm.style.display = isVisible ? 'none' : 'block';
            
            // 如果显示表单，自动聚焦到用户名输入框
            if (!isVisible) {
                const usernameInput = replyForm.querySelector('input[name="reply_username"]');
                if (usernameInput) {
                    usernameInput.focus();
                }
                
                // 清除之前的隐藏字段
                const parentReplyInput = replyForm.querySelector('input[name="parent_reply_id"]');
                const replyToUsernameInput = replyForm.querySelector('input[name="reply_to_username"]');
                if (parentReplyInput) parentReplyInput.value = '';
                if (replyToUsernameInput) replyToUsernameInput.value = '';
            }
        } else {
            // 打印调试信息
            console.log(`🔍 Looking for reply form for comment ${commentId}`);
            console.log('Available comment elements:', document.querySelectorAll('[data-comment-id]'));
            console.log('Available reply forms:', document.querySelectorAll('.reply-form'));
            
            // 如果找不到回复表单，延迟500ms后重试一次，如果还是找不到就重新加载评论
            setTimeout(() => {
                const retryReplyForm = document.getElementById(`reply-form-${commentId}`) || 
                                     document.querySelector(`[data-comment-id="${commentId}"] .reply-form`);
                if (retryReplyForm) {
                    console.log(`Retry successful: found reply form reply-form-${commentId}`);
                    this.showReplyForm(commentId, level);
                } else {
                    this.showError('Reply form not found, reloading comments...');
                    console.log(`Reply form reply-form-${commentId} not found, reloading comments`);
                    this.loadComments();
                }
            }, 500);
        }
    }
    
    // 新增：显示回复特定回复的表单
    showReplyToReplyForm(commentId, parentReplyId, parentUsername, level = 0) {
        // 限制回复层级最多3层
        if (level >= 3) {
            this.showError('Reply level too deep, please reply in comment area');
            return;
        }
        
        const replyForm = document.getElementById(`reply-form-${commentId}`);
        if (replyForm) {
            // 显示回复表单
            replyForm.style.display = 'block';
            
            // 设置隐藏字段存储parent_reply_id
            let parentReplyInput = replyForm.querySelector('input[name="parent_reply_id"]');
            if (!parentReplyInput) {
                parentReplyInput = document.createElement('input');
                parentReplyInput.type = 'hidden';
                parentReplyInput.name = 'parent_reply_id';
                replyForm.appendChild(parentReplyInput);
            }
            parentReplyInput.value = parentReplyId;
            
            // 设置隐藏字段存储reply_to_username
            let replyToUsernameInput = replyForm.querySelector('input[name="reply_to_username"]');
            if (!replyToUsernameInput) {
                replyToUsernameInput = document.createElement('input');
                replyToUsernameInput.type = 'hidden';
                replyToUsernameInput.name = 'reply_to_username';
                replyForm.appendChild(replyToUsernameInput);
            }
            replyToUsernameInput.value = parentUsername;
            
            // 获取回复内容输入框
            const contentTextarea = replyForm.querySelector('textarea[name="reply_content"]');
            if (contentTextarea) {
                // 在回复内容中添加@提及
                contentTextarea.value = `@${parentUsername} `;
                contentTextarea.focus();
                // 光标移到末尾
                contentTextarea.selectionStart = contentTextarea.selectionEnd = contentTextarea.value.length;
            }
        } else {
            // 如果找不到回复表单，延迟500ms后重试一次，如果还是找不到就重新加载评论
            setTimeout(() => {
                const retryReplyForm = document.getElementById(`reply-form-${commentId}`);
                if (retryReplyForm) {
                    console.log(`Retry successful: found reply form reply-form-${commentId}`);
                    this.showReplyToReplyForm(commentId, parentReplyId, parentUsername, level);
                } else {
                    this.showError('Reply form not found, reloading comments...');
                    console.log(`Reply form reply-form-${commentId} not found, reloading comments`);
                    this.loadComments();
                }
            }, 500);
        }
    }

    async submitReply(commentId, event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const data = {
            username: formData.get('reply_username'),
            content: formData.get('reply_content')
        };
        
        // 添加父回复信息（如果存在）
        const parentReplyId = formData.get('parent_reply_id');
        const replyToUsername = formData.get('reply_to_username');
        if (parentReplyId) {
            data.parent_reply_id = parentReplyId;
        }
        if (replyToUsername) {
            data.reply_to_username = replyToUsername;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/${commentId}/reply`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('回复提交成功！');
                form.reset();
                form.style.display = 'none';
                // 清除隐藏字段
                const parentReplyInput = form.querySelector('input[name="parent_reply_id"]');
                const replyToUsernameInput = form.querySelector('input[name="reply_to_username"]');
                if (parentReplyInput) parentReplyInput.value = '';
                if (replyToUsernameInput) replyToUsernameInput.value = '';
                
                this.loadComments(); // 重新加载评论以显示新回复
            } else {
                this.showError('回复失败: ' + result.message);
            }
        } catch (error) {
            this.showError('Network error, please try again later');
        }
    }
    
    renderStats(stats) {
        const statsContainer = document.getElementById('comment-stats');
        if (!statsContainer) return;
        
        const ratingStars = '⭐'.repeat(Math.round(stats.average_rating));
        
        statsContainer.innerHTML = `
            <div class="stats-summary">
                <div class="stat-item">
                    <span class="stat-number">${stats.total_comments}</span>
                    <span class="stat-label">评论总数</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${stats.average_rating}</span>
                    <span class="stat-label">平均评分 ${ratingStars}</span>
                </div>
            </div>
            <div class="rating-distribution">
                ${Object.entries(stats.rating_distribution).reverse().map(([rating, count]) => `
                    <div class="rating-bar">
                        <span class="rating-label">${rating}星</span>
                        <div class="rating-progress">
                            <div class="rating-fill" style="width: ${stats.total_comments > 0 ? (count / stats.total_comments * 100) : 0}%"></div>
                        </div>
                        <span class="rating-count">${count}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderComments(comments) {
        const commentList = document.getElementById('comment-list');
        if (!commentList) return;
        
        if (comments.length === 0) {
            commentList.innerHTML = '<div class="no-comments">暂无评论，快来抢沙发！</div>';
            return;
        }
        
        commentList.innerHTML = comments.map(comment => this.renderComment(comment)).join('');
    }
    
    renderComment(comment) {
        const timeAgo = this.timeAgo(comment.created_at);
        const rating = '⭐'.repeat(comment.rating);
        const isLiked = this.checkLikeStatus(comment.comment_id);
        const likedClass = isLiked ? 'liked' : '';
        const disabledAttr = isLiked ? 'disabled' : '';
        
        return `
            <div class="comment-item" data-comment-id="${comment.comment_id}">
                <div class="comment-header">
                    <div class="comment-author">
                        <strong>${this.escapeHtml(comment.username)}</strong>
                        <span class="comment-rating">${rating}</span>
                    </div>
                    <div class="comment-meta">
                        <span class="comment-time">${timeAgo}</span>
                    </div>
                </div>
                <div class="comment-content">
                    ${this.escapeHtml(comment.content)}
                </div>
                <div class="comment-actions">
                    ${this.enableLike ? `
                    <button class="like-btn ${likedClass}" onclick="commentSystem.likeComment('${comment.comment_id}')" ${disabledAttr}>
                        👍 <span class="like-count">${comment.likes}</span>
                    </button>
                    ` : ''}
                    ${this.enableReply ? `
                    <button class="reply-btn" onclick="commentSystem.showReplyForm('${comment.comment_id}')">
                        回复
                    </button>
                    ` : ''}
                </div>
                ${this.enableReply ? `
                <div id="reply-form-${comment.comment_id}" class="reply-form" style="display: none;">
                    <form onsubmit="commentSystem.submitReply('${comment.comment_id}', event)">
                        <div class="form-group">
                            <input type="text" name="reply_username" placeholder="Your username" required maxlength="50">
                        </div>
                        <div class="form-group">
                            <textarea name="reply_content" placeholder="Write your reply..." required maxlength="2000"></textarea>
                        </div>
                        <button type="submit" class="submit-btn">提交回复</button>
                        <button type="button" class="cancel-btn" onclick="commentSystem.showReplyForm('${comment.comment_id}')">取消</button>
                    </form>
                </div>
                ` : ''}
                ${comment.replies.length > 0 ? `
                <div class="replies">
                    ${comment.replies.map(reply => this.renderReply(reply, comment.comment_id)).join('')}
                </div>
                ` : ''}
            </div>
        `;
    }
    
    renderReply(reply, commentId) {
        const timeAgo = this.timeAgo(reply.created_at);
        const isLiked = this.checkLikeStatus(commentId, true, reply.reply_id);
        const likedClass = isLiked ? 'liked' : '';
        const disabledAttr = isLiked ? 'disabled' : '';
        
        // 处理@提及显示
        const replyToContent = reply.reply_to_username ? 
            `<span class="reply-mention">@${this.escapeHtml(reply.reply_to_username)}</span> ${this.escapeHtml(reply.content)}` :
            this.escapeHtml(reply.content);
        
        return `
            <div class="reply-item" data-reply-id="${reply.reply_id}">
                <div class="reply-header">
                    <strong>${this.escapeHtml(reply.username)}</strong>
                    <span class="reply-time">${timeAgo}</span>
                </div>
                <div class="reply-content">
                    ${replyToContent}
                </div>
                <div class="reply-actions">
                    ${this.enableLike ? `
                    <button class="like-btn ${likedClass}" onclick="commentSystem.likeComment('${commentId}', true, '${reply.reply_id}')" ${disabledAttr}>
                        👍 <span class="like-count">${reply.likes}</span>
                    </button>
                    ` : ''}
                    ${this.enableReply ? `
                    <button class="reply-btn" onclick="commentSystem.showReplyToReplyForm('${commentId}', '${reply.reply_id}', '${reply.username}')">
                        回复
                    </button>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    renderPagination(pagination) {
        const paginationContainer = document.getElementById('comment-pagination');
        if (!paginationContainer || pagination.pages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }
        
        let paginationHtml = '<div class="pagination-buttons">';
        
        // 上一页
        if (pagination.page > 1) {
            paginationHtml += `<button class="page-btn" onclick="commentSystem.goToPage(${pagination.page - 1})">上一页</button>`;
        }
        
        // 页码
        for (let i = 1; i <= pagination.pages; i++) {
            if (i === pagination.page) {
                paginationHtml += `<button class="page-btn active">${i}</button>`;
            } else if (i === 1 || i === pagination.pages || Math.abs(i - pagination.page) <= 2) {
                paginationHtml += `<button class="page-btn" onclick="commentSystem.goToPage(${i})">${i}</button>`;
            } else if (i === pagination.page - 3 || i === pagination.page + 3) {
                paginationHtml += `<span class="page-ellipsis">...</span>`;
            }
        }
        
        // 下一页
        if (pagination.page < pagination.pages) {
            paginationHtml += `<button class="page-btn" onclick="commentSystem.goToPage(${pagination.page + 1})">下一页</button>`;
        }
        
        paginationHtml += '</div>';
        paginationContainer.innerHTML = paginationHtml;
    }
    
    goToPage(page) {
        this.currentPage = page;
        this.loadComments();
    }
    
    showLoading() {
        const commentList = document.getElementById('comment-list');
        if (commentList) {
            commentList.innerHTML = '<div class="loading">加载中...</div>';
        }
    }
    
    showError(message) {
        console.error('💥 显示错误:', message);
        this.showMessage(message, 'error');
    }
    
    showSuccess(message) {
        console.log('✅ 显示成功:', message);
        this.showMessage(message, 'success');
    }
    
    showMessage(message, type = 'info') {
        // 创建消息元素
        const messageEl = document.createElement('div');
        messageEl.className = `comment-message ${type}`;
        messageEl.textContent = message;
        
        // 添加到页面
        const container = document.getElementById(this.containerId);
        container.insertBefore(messageEl, container.firstChild);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 3000);
    }
    
    timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffDays > 0) return `${diffDays}天前`;
        if (diffHours > 0) return `${diffHours}小时前`;
        if (diffMins > 0) return `${diffMins}分钟前`;
        return '刚刚';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // 新增：回复特定用户
    replyToUser(username, commentId) {
        const replyForm = document.getElementById(`reply-form-${commentId}`);
        if (replyForm) {
            // 显示回复表单
            replyForm.style.display = 'block';
            
            // 获取回复内容输入框
            const contentTextarea = replyForm.querySelector('textarea[name="reply_content"]');
            if (contentTextarea) {
                // 在回复内容中添加@提及
                contentTextarea.value = `@${username} `;
                contentTextarea.focus();
                // 光标移到末尾
                contentTextarea.selectionStart = contentTextarea.selectionEnd = contentTextarea.value.length;
            }
        }
    }
}

// 全局变量，便于在HTML中调用
let commentSystem;