/**
 * WriteAgent Service Worker
 *
 * 提供离线支持和缓存策略
 */

const CACHE_NAME = 'writeagent-v1';
const STATIC_CACHE_NAME = 'writeagent-static-v1';
const DYNAMIC_CACHE_NAME = 'writeagent-dynamic-v1';

// 需要预缓存的静态资源
const PRECACHE_URLS = [
  '/',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
];

// API 请求缓存策略
const API_CACHE_THRESHOLD = 100; // 只缓存小于100KB的API响应
const MAX_DYNAMIC_CACHE_ENTRIES = 50; // 动态缓存最大条目数

/**
 * 安装事件 - 预缓存静态资源
 */
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    caches.open(STATIC_CACHE_NAME).then((cache) => {
      console.log('[SW] Precaching static assets');
      return cache.addAll(PRECACHE_URLS);
    })
  );

  // 立即激活新的 Service Worker
  self.skipWaiting();
});

/**
 * 激活事件 - 清理旧缓存
 */
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // 删除旧版本的缓存
          if (
            cacheName !== CACHE_NAME &&
            cacheName !== STATIC_CACHE_NAME &&
            cacheName !== DYNAMIC_CACHE_NAME
          ) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );

  // 立即控制所有客户端
  return self.clients.claim();
});

/**
 * 网络请求拦截 - 缓存策略
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 跳过非 HTTP(S) 请求
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // API 请求 - Network First with Cache Fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // 静态资源 - Cache First with Network Fallback
  if (isStaticAsset(request)) {
    event.respondWith(handleStaticAsset(request));
    return;
  }

  // 其他请求 - Network First with Cache Fallback
  event.respondWith(handleNavigationRequest(request));
});

/**
 * 处理 API 请求（Network First）
 */
async function handleApiRequest(request) {
  try {
    // 尝试从网络获取
    const response = await fetch(request);

    // 如果是 GET 请求且成功，缓存响应
    if (request.method === 'GET' && response.ok && response.clone()) {
      const responseToCache = response.clone();
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      await cache.put(request, responseToCache);
      await enforceDynamicCacheLimit();
    }

    return response;
  } catch (error) {
    // 网络失败，尝试从缓存获取
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] Serving API from cache:', request.url);
      return cachedResponse;
    }

    // 返回离线错误响应
    return new Response(
      JSON.stringify({
        error: 'Network Error',
        message: 'No network connection and no cached data available',
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

/**
 * 处理静态资源（Cache First）
 */
async function handleStaticAsset(request) {
  const cache = await caches.open(STATIC_CACHE_NAME);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // 返回空的占位响应
    return new Response('Resource not available offline', { status: 503 });
  }
}

/**
 * 处理导航请求（Network First）
 */
async function handleNavigationRequest(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      // 缓存成功的导航响应
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, response.clone());
      await enforceDynamicCacheLimit();
    }
    return response;
  } catch (error) {
    // 离线时返回缓存的页面
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // 返回离线页面
    return caches.match('/');
  }
}

/**
 * 判断是否是静态资源请求
 */
function isStaticAsset(request) {
  const url = new URL(request.url);
  const staticExtensions = [
    '.js',
    '.css',
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.svg',
    '.ico',
    '.woff',
    '.woff2',
    '.ttf',
    '.eot',
  ];
  return staticExtensions.some((ext) => url.pathname.endsWith(ext));
}

/**
 * 强制执行动态缓存限制
 * 保留最近的 N 个条目
 */
async function enforceDynamicCacheLimit() {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);
  const keys = await cache.keys();

  if (keys.length > MAX_DYNAMIC_CACHE_ENTRIES) {
    // 删除最旧的条目
    const keysToDelete = keys.slice(0, keys.length - MAX_DYNAMIC_CACHE_ENTRIES);
    await Promise.all(keysToDelete.map((key) => cache.delete(key)));
    console.log('[SW] Cleaned up old cache entries');
  }
}

/**
 * 消息处理 - 用于与客户端通信
 */
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});

/**
 * 后台同步（如果支持）
 */
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  }
});

/**
 * 同步消息的示例实现
 */
async function syncMessages() {
  // 这里可以实现离线消息的同步逻辑
  console.log('[SW] Syncing messages...');
}

/**
 * 推送通知（如果支持）
 */
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : '您有新的消息',
    icon: '/icon-192.png',
    badge: '/icon-96.png',
    vibrate: [200, 100, 200],
    tag: 'writeagent-notification',
    requireInteraction: false,
  };

  event.waitUntil(self.registration.showNotification('WriteAgent', options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients.openWindow('/') || self.clients.focus()
  );
});
