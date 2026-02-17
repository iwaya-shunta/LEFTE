const CACHE_NAME = 'lefte-cache-v5.5.1';
const urlsToCache = [
  '/',
  '/manifest.json',
  '/static/desktpo.css', // 🚀 ローカルのCSSもキャッシュに追加
  '/static/desktpo.js',  // 🚀 ローカルのJSもキャッシュに追加
  'https://cdn.jsdelivr.net/npm/marked/marked.min.js',
  'https://cdn-icons-png.flaticon.com/512/1698/1698535.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // 🚀 Socket.IO, POSTリクエスト, そして「履歴API(/history)」はキャッシュさせない
  // これにより、リロードした時に常に最新の履歴がDBから読み込まれます
  if (
    url.pathname.startsWith('/socket.io') || 
    url.pathname.startsWith('/history') || 
    event.request.method !== 'GET'
  ) {
    return; // 何もしない（通常のネットワーク通信に任せる）
  }

  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});

self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});