export type CurrentDeparture = { route_id: string; bus_identifier: string; status: "scheduled" | "no_further_departures_today"; scheduled_departure_at: string | null };
export type ScheduleEntry = { route_id: string; origin: string; destination: string; direction: "RETURN" | "PICK-UP"; bus_identifiers: string[]; scheduled_departure_at: string };
export type CurrentDeparturesResponse = { service_date: string; published_at: string; departures: CurrentDeparture[] };
export type ScheduleResponse = { service_date: string; service_status: "operating" | "no_service"; published_at: string; entries: ScheduleEntry[] };
export type Announcement = { id: string; title: string; content: string; published_at: string; expires_at: string | null };
export type UrgentBanner = { id: string; announcement_id: string; title: string; content: string; created_at: string };

export type PublicSnapshot = {
  current: CurrentDeparturesResponse;
  schedule: ScheduleResponse;
  announcements: Announcement[];
  lastSuccessfulSync: string;
};

const DATABASE = "uzair-transport-public";
const STORE = "snapshots";
const KEY = "published-data";
const CACHE = "uzair-public-data-v1";
export const MAX_CACHE_AGE_MS = 24 * 60 * 60 * 1000;
export const FRESH_AGE_MS = 5 * 60 * 1000;

function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function readSnapshot(): Promise<PublicSnapshot | null> {
  if (typeof indexedDB === "undefined") return null;
  const db = await database();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE, "readonly");
    const request = transaction.objectStore(STORE).get(KEY);
    request.onsuccess = () => resolve((request.result as PublicSnapshot | undefined) ?? null);
    request.onerror = () => reject(request.error);
    transaction.oncomplete = () => db.close();
  });
}

async function writeSnapshot(snapshot: PublicSnapshot): Promise<void> {
  const db = await database();
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction(STORE, "readwrite");
    transaction.objectStore(STORE).put(snapshot, KEY);
    transaction.oncomplete = () => { db.close(); resolve(); };
    transaction.onerror = () => reject(transaction.error);
  });
}

function isResponseOk(response: Response): boolean { return response.ok; }

export async function fetchSnapshot(apiBaseUrl: string): Promise<PublicSnapshot> {
  const [currentResponse, scheduleResponse, announcementResponse] = await Promise.all([
    // A synchronization must describe the live API state. In particular, a
    // browser's cached error response must not turn an available API into an
    // apparent outage or advance the last-successful-sync timestamp.
    fetch(`${apiBaseUrl}/api/v1/public/transport/current-departures`, { cache: "no-store" }),
    fetch(`${apiBaseUrl}/api/v1/public/transport/schedule`, { cache: "no-store" }),
    fetch(`${apiBaseUrl}/api/v1/public/announcements`, { cache: "no-store" }),
  ]);
  if (![currentResponse, scheduleResponse, announcementResponse].every(isResponseOk)) throw new Error("Published transport information is unavailable");
  const [current, schedule, announcementData] = await Promise.all([
    currentResponse.json() as Promise<CurrentDeparturesResponse>,
    scheduleResponse.json() as Promise<ScheduleResponse>,
    announcementResponse.json() as Promise<{ announcements: Announcement[] }>,
  ]);
  return { current, schedule, announcements: announcementData.announcements, lastSuccessfulSync: new Date().toISOString() };
}

async function persistPayloads(apiBaseUrl: string, snapshot: PublicSnapshot): Promise<void> {
  if (typeof caches === "undefined") return;
  const cache = await caches.open(CACHE);
  await Promise.all([
    cache.put(`${apiBaseUrl}/api/v1/public/transport/current-departures`, new Response(JSON.stringify(snapshot.current), { headers: { "Content-Type": "application/json" } })),
    cache.put(`${apiBaseUrl}/api/v1/public/transport/schedule`, new Response(JSON.stringify(snapshot.schedule), { headers: { "Content-Type": "application/json" } })),
    cache.put(`${apiBaseUrl}/api/v1/public/announcements`, new Response(JSON.stringify({ announcements: snapshot.announcements }), { headers: { "Content-Type": "application/json" } })),
  ]);
}

export async function synchronize(apiBaseUrl: string): Promise<PublicSnapshot> {
  const snapshot = await fetchSnapshot(apiBaseUrl);
  await Promise.all([writeSnapshot(snapshot), persistPayloads(apiBaseUrl, snapshot)]);
  return snapshot;
}

export function cacheIsUsable(snapshot: PublicSnapshot, now = Date.now()): boolean {
  return now - new Date(snapshot.lastSuccessfulSync).getTime() < MAX_CACHE_AGE_MS;
}

export function isStale(snapshot: PublicSnapshot, now = Date.now()): boolean {
  return now - new Date(snapshot.lastSuccessfulSync).getTime() > FRESH_AGE_MS;
}
