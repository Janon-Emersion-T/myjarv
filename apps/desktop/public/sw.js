self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open("jarvis-shell-v1").then((cache) =>
      cache.addAll(["/", "/manifest.webmanifest", "/jarvis-icon.svg"]),
    ),
  );
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  const { request } = event;
  const accept = request.headers.get("accept") || "";
  const isNavigation = request.mode === "navigate" || accept.includes("text/html");
  const sameOrigin = new URL(request.url).origin === self.location.origin;

  if (isNavigation) {
    event.respondWith(
      fetch(request).catch(async () => {
        const cached = await caches.match("/");
        return cached || Response.error();
      }),
    );
    return;
  }

  if (!sameOrigin) {
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(request).then((response) => {
        if (!response || response.status !== 200) {
          return response;
        }
        const clone = response.clone();
        void caches.open("jarvis-shell-v1").then((cache) => cache.put(request, clone));
        return response;
      });
    }),
  );
});
