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
  });

  it("searches existing drafts without exposing a schedule validation action", () => {
    cy.intercept("GET", "**/auth/session", {
      supabase_user_id: "transport-manager", role: "transport_management", active: true,
    }).as("session");
    cy.intercept("GET", "**/api/v1/admin/transport/change-sets?query=*", {
      change_sets: [{
        id: "2a1bf858-32cc-4cc3-8619-3f2dbe7d0c50", name: "Spring timetable",
        status: "draft", version: 2, expires_at: "2026-12-20T08:00:00Z",
        base_published_change_set_id: null,
      }],
    }).as("draftSearch");
    cy.visit("/", { onBeforeLoad(window) { window.sessionStorage.setItem("uts.access-token", "test-token"); } });
    cy.wait("@session");
    cy.findByRole("button", { name: /search drafts/i }).click();
    cy.wait("@draftSearch");
    cy.contains("Spring timetable").should("be.visible");
    cy.findByRole("button", { name: /^validate$/i }).should("not.exist");
  });
});
