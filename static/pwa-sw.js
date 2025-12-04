// PWA Service Worker for Sprunki Phase 4
const VERSION = '1.0.4'; // 版本号 - 修改此版本号会触发更新
const CACHE_NAME = `sprunki-p4-v${VERSION}`;
const STATIC_CACHE = `sprunki-static-v${VERSION}`;
const DYNAMIC_CACHE = `sprunki-dynamic-v${VERSION}`;

// 静态资源缓存列表
const urlsToCache = [
  '/',
  'static/style/style.css',
  'static/style/language-selector.css',
  'static/style/fullscreen.js',
  'static/style/native-fullscreen.js',
  'static/js/game-status-bar.js',
  'static/manifest.json',
  'static/icon-192.png',
  'static/icon-512.png',
  'static/favicon.ico'
];

// 动态缓存策略：优先网络，失败时使用缓存
const networkFirst = async (request) => {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    return cachedResponse || new Response('Offline', { status: 503 });
  }
};

// 缓存优先策略：用于静态资源
const cacheFirst = async (request) => {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    return new Response('Resource not available', { status: 503 });
  }
};

self.addEventListener('install', event => {
  console.log(`PWA: Service Worker ${VERSION} installing...`);
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('PWA: Caching static files');
        return cache.addAll(urlsToCache);
      })
      .catch(err => console.log('PWA: Cache install failed', err))
  );
  // 强制激活新的 Service Worker
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  console.log(`PWA: Service Worker ${VERSION} activating...`);
  event.waitUntil(
    Promise.all([
      // 清理旧缓存
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('PWA: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // 通知所有客户端更新
      self.clients.matchAll().then(clients => {
        clients.forEach(client => {
          client.postMessage({
            type: 'SW_UPDATED',
            version: VERSION,
            message: 'Service Worker has been updated!'
          });
        });
      })
    ])
  );
  // 立即获取控制权
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // 只处理同源请求
  if (url.origin !== location.origin) {
    return;
  }
  
  // 静态资源使用缓存优先策略
  if (request.url.includes('/static/') || 
      request.url.includes('manifest.json') || 
      request.url.includes('favicon.ico')) {
    event.respondWith(cacheFirst(request));
    return;
  }
  
  // HTML页面使用网络优先策略
  if (request.mode === 'navigate' || 
      request.headers.get('Accept').includes('text/html')) {
    event.respondWith(networkFirst(request));
    return;
  }
  
  // 其他请求使用网络优先策略
  event.respondWith(networkFirst(request));
});

// 监听来自页面的消息
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('PWA: 收到跳过等待指令');
    self.skipWaiting();
  }
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('PWA: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});