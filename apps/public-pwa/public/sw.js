/* Workbox owns runtime Cache Storage for public, published reads. */
importScripts("https://storage.googleapis.com/workbox-cdn/releases/7.4.0/workbox-sw.js");

if (self.workbox) {
  workbox.core.clientsClaim();
  workbox.core.skipWaiting();
  workbox.routing.registerRoute(
    // The application's synchronizer explicitly requests a live response.
    // Let it bypass this runtime cache so it can accurately report an outage;
    // cached snapshots remain available through IndexedDB/Cache Storage.
    ({ url, request }) => request.method === "GET"
      && request.cache !== "no-store"
      && /^\/api\/v1\/public\/(transport|announcements)/.test(url.pathname),
    new workbox.strategies.NetworkFirst({
      cacheName: "uzair-public-api-v1",
      networkTimeoutSeconds: 5,
      plugins: [new workbox.expiration.ExpirationPlugin({ maxAgeSeconds: 24 * 60 * 60, maxEntries: 12 })],
    }),
  );
}
