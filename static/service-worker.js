const CACHE_NAME = 'lefte-cache-v5.5.1';
const urlsToCache = [
  '/',
  '/manifest.json',
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
  // APIリクエストや動的なコンテンツはキャッシュしない戦略も検討可能ですが、
  // ここではシンプルにキャッシュ優先、なければネットワークとしています。
  // チャットの履歴(/history)や送信(/chat)はネットワーク必須なので除外を検討すべきですが、
  // POSTリクエストはキャッシュされないため、GETの/historyのみ注意が必要です。

  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
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
