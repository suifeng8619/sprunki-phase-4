# iOS PWA 安装指南

## 本地测试 HTTPS 访问

服务器现在运行在 HTTPS 模式下：
- 访问地址: https://localhost:9028
- 注意：浏览器会警告证书不受信任，这是正常的（自签名证书）

## 在 iOS 设备上测试

### 方法 1：同一网络访问
1. 确保手机和电脑在同一 WiFi 网络
2. 查找电脑 IP 地址：
   ```bash
   ifconfig | grep "inet "
   ```
3. 在手机 Safari 访问：https://[你的IP]:9028
4. 接受证书警告

### 方法 2：使用 ngrok（推荐）
1. 安装 ngrok:
   ```bash
   brew install ngrok
   ```
2. 暴露本地服务:
   ```bash
   ngrok http https://localhost:9028
   ```
3. 使用 ngrok 提供的 HTTPS URL 访问

## 添加到主屏幕（真正的 PWA 模式）

1. 在 Safari 中打开网站（必须是 HTTPS）
2. 点击分享按钮（底部中间的方形箭头）
3. 向下滑动，找到 "添加到主屏幕"
4. 点击 "添加"
5. 设置应用名称
6. 点击右上角 "添加"

## 验证 PWA 模式

从主屏幕启动后，应该：
- 没有浏览器地址栏
- 全屏显示
- 看到 "Tap to Start Game" 提示
- 点击后音频应该能正常工作

## 音频激活流程

1. PWA 模式检测到后会显示启动覆盖层
2. 用户点击 "Tap to Start Game"
3. 激活音频上下文
4. 游戏以全屏模式运行

## 注意事项

- 必须使用 HTTPS（本地自签名证书也可以）
- iOS 14.5+ 对 PWA 支持更好
- 音频仍然需要用户交互才能播放
- 游戏本身可能需要支持 message 事件监听