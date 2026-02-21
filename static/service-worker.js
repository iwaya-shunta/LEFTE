const CACHE_NAME = 'lefte-cache-v5.5.3';
const urlsToCache = [
  '/',
  '/manifest.json',
  '/desktpo.css',
  '/desktpo.js',
  '/icon-192.png', // 🚀 必須：自分のアイコンをリストに入れる
  '/icon-512.png', // 🚀 必須：自分のアイコンをリストに入れる
  'https://cdn.jsdelivr.net/npm/marked/marked.min.js'
  // 🚀 外部の不安定な画像URLはここから削除する
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        // 🚀 外部アイコンは、もしエラーが出てもインストールを止めないように
        // 個別に add するか、リストから外して fetch 時に任せるのが安全だよ
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