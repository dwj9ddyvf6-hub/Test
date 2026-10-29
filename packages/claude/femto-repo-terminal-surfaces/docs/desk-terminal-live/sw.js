/* Muse Desk service worker — FIXALL T-PWA-01 handoff.
   - The shell cache name is stamped per publish: the publisher
     replaces 732d6bfa57e4 with the shell content hash, so a
     changed index.html can never ride under an old cache name.
   - The app shell is network-first on every fetch: a publish is
     visible on the next load; the cache is the offline fallback
     only. The data feed stays network-first as before. */
var SHELL_BUILD = '732d6bfa57e4';
var SHELL_CACHE = 'muse-desk-shell-' + SHELL_BUILD;
var SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './favicon.svg',
  './favicon-32.png',
  './apple-touch-icon.png',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(function (cache) { return cache.addAll(SHELL); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.map(function (k) {
          return k === SHELL_CACHE ? null : caches.delete(k);
        }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET') return;
  // Network-first for everything this worker serves (feed AND
  // shell): fresh on every load the network answers, the last
  // good cached copy only when it does not.
  event.respondWith(
    fetch(event.request).then(function (response) {
      var copy = response.clone();
      caches.open(SHELL_CACHE).then(function (cache) {
        cache.put(event.request, copy);
      });
      return response;
    }).catch(function () {
      return caches.match(event.request);
    })
  );
});

self.addEventListener('push', function (event) {
  var data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = {}; }
  var title = data.title || 'Muse Desk';
  var options = {
    body: data.body || '',
    icon: './icon-192.png',
    badge: './favicon-32.png',
    data: { url: data.url || './' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var target = (event.notification.data && event.notification.data.url) || './';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(function (list) {
        for (var i = 0; i < list.length; i++) {
          var client = list[i];
          if ('focus' in client) {
            if ('navigate' in client) client.navigate(target);
            return client.focus();
          }
        }
        if (self.clients.openWindow) return self.clients.openWindow(target);
      })
  );
});
