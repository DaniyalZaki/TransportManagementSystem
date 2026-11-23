describe("announcement administration", () => {
  it("loads current announcements and banners into a separate lifecycle card", () => {
    cy.intercept("GET", "**/auth/session", { supabase_user_id: "admin", role: "designated_administrator", active: true }).as("session");
    cy.intercept("GET", "**/api/v1/admin/announcements/current", {
      announcements: [{ id: "a-1", title: "Diversion", content: "Use gate B", published_at: "2026-11-22T09:00:00+05:00", expires_at: null }],
      banners: [{ id: "b-1", announcement_id: "a-1", title: "Diversion", content: "Use gate B", created_at: "2026-11-22T09:00:00+05:00" }],
    }).as("currentItems");
    cy.visit("/", { onBeforeLoad(window) { window.sessionStorage.setItem("uts.access-token", "test-token"); } });
    cy.wait("@session");
    cy.findByRole("button", { name: /load current items/i }).click();
    cy.wait("@currentItems");
    cy.findByRole("heading", { name: /current announcements and banners/i }).should("be.visible");
    cy.get("#announcement-lifecycle-content").findByRole("heading", { name: /^announcements$/i }).should("be.visible");
    cy.get("#announcement-lifecycle-content").contains("Diversion").should("be.visible");
    cy.findByRole("button", { name: /resolve banner/i }).should("be.visible");
  });

  it("publishes an urgent confirmed operational change directly", () => {
    cy.intercept("GET", "**/auth/session", { supabase_user_id: "admin", role: "designated_administrator", active: true }).as("session");
    cy.intercept("POST", "**/api/v1/admin/announcements", (request) => {
      expect(request.body).to.include({ title: "Diversion", content: "Use gate B", urgent: true, operational: true });
      request.reply({ announcement: { id: "a-1", title: "Diversion", content: "Use gate B", published_at: "2026-11-22T09:00:00+05:00", expires_at: null }, banner: { id: "b-1" } });
    }).as("publishAnnouncement");
    cy.visit("/", { onBeforeLoad(window) { window.sessionStorage.setItem("uts.access-token", "test-token"); } });
    cy.wait("@session");
    cy.findByRole("button", { name: /announcement/i }).click();
    cy.findByLabelText(/title/i).type("Diversion");
    cy.findByLabelText(/message/i).type("Use gate B");
    cy.findByLabelText(/expiry in pkt/i).type("2026-11-22T11:00");
    cy.findByLabelText(/urgent/i).check();
    cy.findByLabelText(/operational change/i).check();
    cy.findByLabelText(/confirmed/i).check();
    cy.findByRole("button", { name: /publish announcement/i }).click();
    cy.wait("@publishAnnouncement");
    cy.findByRole("status").should("contain.text", "published");
    cy.findByRole("button", { name: /remove announcement/i }).should("be.visible");
    cy.findByRole("button", { name: /remove banner/i }).should("be.visible");
    cy.findByRole("button", { name: /resolve banner/i }).should("be.visible");
  });
});
