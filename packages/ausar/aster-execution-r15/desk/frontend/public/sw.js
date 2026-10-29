self.addEventListener('push', (event) => {
  let payload = {};
  try {
    const parsed = event.data ? event.data.json() : {};
    payload = parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {body: parsed == null ? '' : String(parsed)};
  } catch { payload = {body: event.data ? event.data.text() : ''}; }
  const title = typeof payload.title === 'string' && payload.title ? payload.title : 'Aster Desk';
  const body = typeof payload.body === 'string' ? payload.body : payload.body == null ? '' : JSON.stringify(payload.body);
  event.waitUntil(self.registration.showNotification(title, {
    body, data: {url: '/', eventId: payload.event_id || null},
    tag: payload.event_id ? `aster-${payload.event_id}` : undefined,
  }));
});
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(self.clients.matchAll({type: 'window', includeUncontrolled: true}).then((windows) => {
    const existing = windows.find((window) => window.url.startsWith(self.location.origin));
    if (existing) return existing.focus();
    return self.clients.openWindow('/');
  }));
});
