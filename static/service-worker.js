const CACHE_NAME = 'fisica-web-shell-v1';
const STATIC_ASSETS = [
  '/static/manifest.webmanifest',
  '/static/img/logo.png',
  '/static/accessibility-report.js',
  '/static/acquisition-layer.js',
  '/static/experiment-focus.js',
  '/static/experiment-montage.js',
  '/static/scientific-analysis.js',
  '/static/offline.html'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  // Não armazena páginas dinâmicas, grupo_id, relatórios, APIs ou dados experimentais.
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/static/offline.html')));
    return;
  }

  if (url.origin === self.location.origin && url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => cached || fetch(request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      }))
    );
  }
});
