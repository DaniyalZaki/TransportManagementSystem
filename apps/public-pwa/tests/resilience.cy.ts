import { FRESH_AGE_MS, MAX_CACHE_AGE_MS, cacheIsUsable, isStale, type PublicSnapshot } from "../src/lib/public-data";

const current = { service_date: "2026-11-23", published_at: "2026-11-23T08:00:00Z", departures: [{ route_id: "R-01", bus_identifier: "C-12", status: "scheduled", scheduled_departure_at: "2026-11-23T14:00:00+05:00" }] };
const schedule = { service_date: "2026-11-23", service_status: "operating", published_at: "2026-11-23T08:00:00Z", entries: [{ route_id: "R-01", origin: "Lahore", destination: "Campus", direction: "PICK-UP", bus_identifiers: ["C-12"], scheduled_departure_at: "2026-11-23T14:00:00+05:00" }] };
const announcements = { announcements: [{ id: "a-1", title: "Published notice", content: "Normal service", published_at: "2026-11-23T08:00:00+05:00", expires_at: null }] };

function interceptPublished() {
  cy.intercept("GET", "**/api/v1/public/transport/current-departures*", current).as("current");
  cy.intercept("GET", "**/api/v1/public/transport/schedule*", schedule).as("schedule");
  cy.intercept("GET", "**/api/v1/public/announcements", announcements).as("announcements");
  cy.intercept("GET", "**/api/v1/public/urgent-banners", { banners: [{ id: "b-1", announcement_id: "a-1", title: "Network-only banner", content: "Road closure", created_at: "2026-11-23T08:00:00+05:00" }] }).as("banners");
}

function interceptUnavailable() {
  cy.intercept("GET", "**/api/v1/public/transport/**", { statusCode: 503, body: { detail: "unavailable" } });
  cy.intercept("GET", "**/api/v1/public/announcements", { statusCode: 503, body: { detail: "unavailable" } });
}

describe("public PWA resilience", () => {
  beforeEach(() => {
    cy.visit("/", { onBeforeLoad(window) { window.indexedDB.deleteDatabase("uzair-transport-public"); void window.caches.delete("uzair-public-data-v1"); } });
  });

  it("keeps exactly-five-minute data fresh and expires a snapshot at exactly 24 hours", () => {
    const now = Date.parse("2026-11-23T08:00:00Z");
    const snapshot = { current, schedule, announcements: announcements.announcements, lastSuccessfulSync: new Date(now - FRESH_AGE_MS).toISOString() } as PublicSnapshot;
    expect(isStale(snapshot, now)).to.equal(false);
    expect(isStale(snapshot, now + 1)).to.equal(true);
    snapshot.lastSuccessfulSync = new Date(now - MAX_CACHE_AGE_MS + 1).toISOString();
    expect(cacheIsUsable(snapshot, now)).to.equal(true);
    snapshot.lastSuccessfulSync = new Date(now - MAX_CACHE_AGE_MS).toISOString();
    expect(cacheIsUsable(snapshot, now)).to.equal(false);
  });

  it("persists one PKT last-successful-sync timestamp for a complete successful snapshot", () => {
    interceptPublished(); cy.visit("/"); cy.wait(["@current", "@schedule", "@announcements", "@banners"]);
    cy.contains(/last synced:/i).should("contain.text", "PKT");
    cy.contains(/information may be outdated/i).should("not.exist");
    cy.contains("Network-only banner").should("be.visible");
  });

  it("bypasses browser and service-worker response caches during synchronization", () => {
    cy.intercept("GET", "**/api/v1/public/transport/current-departures*", (request) => {
      expect(request.headers["cache-control"]).to.include("no-cache");
      request.reply(current);
    }).as("uncachedCurrent");
    cy.intercept("GET", "**/api/v1/public/transport/schedule*", schedule);
    cy.intercept("GET", "**/api/v1/public/announcements", announcements);
    cy.intercept("GET", "**/api/v1/public/urgent-banners", { banners: [] });
    cy.visit("/");
    cy.wait("@uncachedCurrent");
  });

  it("retains cached content and its original timestamp when an online refresh fails", () => {
    interceptPublished(); cy.visit("/"); cy.wait(["@current", "@schedule", "@announcements"]);
    cy.get(".sync-time").invoke("text").then((original) => {
      interceptUnavailable(); cy.findByRole("button", { name: /refresh/i }).click();
      cy.findByRole("heading", { name: /service\/data outage/i }).should("be.visible");
      cy.contains("R-01").should("be.visible"); cy.get(".sync-time").should("have.text", original);
    });
  });

  it("shows a pending state while manual refresh is in progress", () => {
    interceptPublished(); cy.visit("/"); cy.wait(["@current", "@schedule", "@announcements"]);
    cy.intercept("GET", "**/api/v1/public/transport/current-departures*", { delay: 500, body: current }).as("slowRefresh");
    cy.findByRole("button", { name: /^refresh$/i }).click();
    cy.findByRole("button", { name: /refreshing/i }).should("be.disabled").and("have.attr", "aria-busy", "true");
    cy.wait("@slowRefresh");
    cy.findByRole("button", { name: /^refresh$/i }).should("be.disabled");
  });

  it("enforces a five-second cooldown after a manual refresh", () => {
    cy.clock(new Date("2026-11-23T08:00:00Z"), ["Date", "setTimeout", "clearTimeout"]);
    interceptPublished(); cy.visit("/"); cy.wait(["@current", "@schedule", "@announcements"]);
    cy.findByRole("button", { name: /^refresh$/i }).click();
    cy.findByRole("button", { name: /^refresh$/i }).should("be.disabled");
    cy.tick(4_999);
    cy.findByRole("button", { name: /^refresh$/i }).should("be.disabled");
    cy.tick(1);
    cy.findByRole("button", { name: /^refresh$/i }).should("be.enabled");
  });

  it("shows unavailable instead of fabricated data on first use during an outage", () => {
    interceptUnavailable(); cy.visit("/");
    cy.findByRole("heading", { name: /transport information unavailable/i }).should("be.visible");
    cy.findByRole("heading", { name: /today's schedule/i }).should("not.exist");
  });

  it("does not persist urgent banners with the offline snapshot", () => {
    interceptPublished(); cy.visit("/"); cy.wait(["@current", "@schedule", "@announcements", "@banners"]);
    interceptUnavailable(); cy.findByRole("button", { name: /refresh/i }).click();
    cy.contains("Network-only banner").should("not.exist");
    cy.get(".announcement-list").contains("strong", "Published notice").should("be.visible");
  });

  it("labels a valid snapshot offline and removes network-only urgent banners", () => {
    interceptPublished(); cy.visit("/"); cy.wait(["@current", "@schedule", "@announcements", "@banners"]);
    cy.window().then((window) => Object.defineProperty(window.navigator, "onLine", { configurable: true, value: false }));
    cy.findByRole("button", { name: /^refresh$/i }).click();
    cy.findByRole("heading", { name: /^offline$/i }).should("be.visible");
    cy.get(".announcement-list").contains("strong", "Published notice").should("be.visible"); cy.contains("Network-only banner").should("not.exist");
  });

  it("reconnects by replacing cached data only after a successful synchronization", () => {
    interceptPublished(); cy.visit("/"); cy.wait(["@current", "@schedule", "@announcements"]);
    cy.intercept("GET", "**/api/v1/public/transport/current-departures*", { ...current, departures: [{ ...current.departures[0], route_id: "R-02" }] }).as("reconnectedCurrent");
    cy.intercept("GET", "**/api/v1/public/transport/schedule*", schedule); cy.intercept("GET", "**/api/v1/public/announcements", announcements); cy.intercept("GET", "**/api/v1/public/urgent-banners", { banners: [] });
    cy.window().then((window) => window.dispatchEvent(new Event("online"))); cy.wait("@reconnectedCurrent");
    cy.contains("R-02").should("be.visible"); cy.findByRole("heading", { name: /^offline$/i }).should("not.exist");
  });

  it("attempts automatic synchronization every minute without advancing the timestamp on failure", () => {
    cy.clock(new Date("2026-11-23T08:00:00Z"), ["Date", "setInterval", "clearInterval"]); interceptPublished(); cy.visit("/"); cy.wait(["@current", "@schedule", "@announcements"]);
    cy.get(".sync-time").invoke("text").then((original) => {
      cy.intercept("GET", "**/api/v1/public/transport/current-departures*", { statusCode: 503, body: { detail: "unavailable" } }).as("periodicRefresh");
      cy.intercept("GET", "**/api/v1/public/transport/schedule*", { statusCode: 503, body: { detail: "unavailable" } });
      cy.intercept("GET", "**/api/v1/public/announcements", { statusCode: 503, body: { detail: "unavailable" } });
      cy.then(() => cy.tick(60_000)); cy.wait("@periodicRefresh");
      cy.findByRole("heading", { name: /service\/data outage/i }).should("be.visible"); cy.get(".sync-time").should("have.text", original);
    });
  });
});
