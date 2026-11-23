describe("admin web foundation", () => {
  it("shows the privileged sign-in boundary", () => {
    cy.visit("/");
    cy.findByRole("heading", { name: /transport management sign in/i }).should("be.visible");
    cy.contains(/supabase auth/i).should("be.visible");
    cy.findByLabelText(/email address/i).should("have.attr", "type", "email");
    cy.findByLabelText(/^password$/i).should("have.attr", "type", "password");
    cy.findByRole("button", { name: /sign in/i }).should("exist");
  });

  it("loads publication history through the authenticated admin API", () => {
    cy.intercept("GET", "**/auth/session", {
      supabase_user_id: "transport-manager",
      role: "transport_management",
      active: true,
    }).as("session");
    cy.intercept("GET", "**/api/v1/admin/transport/publications", {
      publications: [{
        change_set_id: "2a1bf858-32cc-4cc3-8619-3f2dbe7d0c50",
        publisher: "transport-manager",
        published_at: "2026-11-20T08:00:00Z",
      }],
    }).as("history");
    cy.visit("/", {
      onBeforeLoad(window) {
        window.sessionStorage.setItem("uts.access-token", "test-token");
      },
    });

    cy.wait("@session");
    cy.findByRole("button", { name: /load history/i }).click();
    cy.wait("@history");
    cy.contains("transport-manager").should("be.visible");
    cy.findByRole("button", { name: /hide history/i }).click();
    cy.contains("transport-manager").should("not.exist");
  });

  it("opens the single shared draft without create or search controls", () => {
    cy.intercept("GET", "**/auth/session", {
      supabase_user_id: "transport-manager", role: "transport_management", active: true,
    }).as("session");
    cy.intercept("GET", "**/api/v1/admin/transport/draft", {
      id: "2a1bf858-32cc-4cc3-8619-3f2dbe7d0c50", name: "Working draft", status: "draft", version: 2,
      base_published_change_set_id: null, has_published_changes: false, snapshot: { routes: [], buses: [], assignments: [], weekly_departures: [], overrides: [] },
    }).as("openDraft");
    cy.visit("/", { onBeforeLoad(window) { window.sessionStorage.setItem("uts.access-token", "test-token"); } });
    cy.wait("@session");
    cy.findByRole("button", { name: /open draft/i }).click();
    cy.wait("@openDraft");
    cy.findByRole("heading", { name: /working draft/i }).should("be.visible");
    cy.findByRole("heading", { name: /shared draft/i }).should("not.exist");
    cy.findByRole("button", { name: /create draft|search drafts/i }).should("not.exist");
  });

  it("keeps a save error visible in the open draft editor", () => {
    cy.intercept("GET", "**/auth/session", {
      supabase_user_id: "transport-manager", role: "transport_management", active: true,
    }).as("session");
    cy.intercept("GET", "**/api/v1/admin/transport/draft", {
      id: "2a1bf858-32cc-4cc3-8619-3f2dbe7d0c50", name: "Working draft", status: "draft", version: 2,
      base_published_change_set_id: null, has_published_changes: false, snapshot: { routes: [], buses: [], assignments: [], weekly_departures: [], overrides: [] },
    }).as("openDraft");
    cy.intercept("PATCH", "**/api/v1/admin/transport/draft", {
      statusCode: 409, body: { detail: "The draft changed. Reload before saving." },
    }).as("saveDraft");
    cy.visit("/", { onBeforeLoad(window) { window.sessionStorage.setItem("uts.access-token", "test-token"); } });
    cy.wait("@session");
    cy.findByRole("button", { name: /open draft/i }).click();
    cy.wait("@openDraft");
    cy.findByRole("button", { name: /save draft/i }).click();
    cy.wait("@saveDraft");
    cy.findByRole("status").should("contain.text", "The draft changed. Reload before saving.");
  });

  it("disables Publish until a changed draft has been saved and when it matches published data", () => {
    cy.intercept("GET", "**/auth/session", { supabase_user_id: "transport-manager", role: "transport_management", active: true }).as("session");
    cy.intercept("GET", "**/api/v1/admin/transport/draft", {
      id: "2a1bf858-32cc-4cc3-8619-3f2dbe7d0c50", name: "Working draft", status: "draft", version: 2,
      base_published_change_set_id: null, has_published_changes: false, snapshot: { routes: [], buses: [], assignments: [], weekly_departures: [], overrides: [] },
    }).as("openDraft");
    cy.visit("/", { onBeforeLoad(window) { window.sessionStorage.setItem("uts.access-token", "test-token"); } });
    cy.wait("@session");
    cy.findByRole("button", { name: /open draft/i }).click();
    cy.wait("@openDraft");
    cy.findByRole("button", { name: /^publish$/i }).should("be.disabled").and("have.attr", "title", "The draft matches the published transport data.");
    cy.findByRole("tab", { name: /buses/i }).click();
    cy.findByLabelText(/bus identifier/i).type("C-01");
    cy.findByRole("button", { name: /add bus/i }).click();
    cy.findByRole("button", { name: /^publish$/i }).should("be.disabled");
  });

  it("collapses and re-expands the open draft editor", () => {
    cy.intercept("GET", "**/auth/session", { supabase_user_id: "transport-manager", role: "transport_management", active: true });
    cy.intercept("GET", "**/api/v1/admin/transport/draft", { id: "2a1bf858-32cc-4cc3-8619-3f2dbe7d0c50", name: "Working draft", status: "draft", version: 2, base_published_change_set_id: null, has_published_changes: false, snapshot: { routes: [], buses: [], assignments: [], weekly_departures: [], overrides: [] } });
    cy.visit("/", { onBeforeLoad(window) { window.sessionStorage.setItem("uts.access-token", "test-token"); } });
    cy.findByRole("button", { name: /open draft/i }).click();
    cy.findByRole("button", { name: /collapse draft/i }).click();
    cy.findByRole("tab", { name: /routes/i }).should("not.exist");
    cy.findByRole("button", { name: /expand draft/i }).click();
    cy.findByRole("tab", { name: /routes/i }).should("be.visible");
  });
});
