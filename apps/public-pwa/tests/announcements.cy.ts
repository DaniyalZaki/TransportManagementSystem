describe("public announcements", () => {
  it("shows announcements and independent active urgent banners newest first", () => {
    cy.intercept("GET", "**/api/v1/public/announcements", { announcements: [{ id: "a-2", title: "New notice", content: "Service update", published_at: "2026-11-22T09:00:00+05:00", expires_at: null }, { id: "a-1", title: "Older notice", content: "Earlier update", published_at: "2026-11-22T08:00:00+05:00", expires_at: null }] }).as("announcements");
    cy.intercept("GET", "**/api/v1/public/urgent-banners", { banners: [{ id: "b-1", announcement_id: "a-2", title: "New notice", content: "Service update", created_at: "2026-11-22T09:00:00+05:00" }] }).as("banners");
    cy.intercept("GET", "**/api/v1/public/transport/**", { statusCode: 503, body: { detail: "unavailable" } });

    cy.visit("/");
    cy.wait(["@announcements", "@banners"]);
    cy.findByRole("heading", { name: /urgent notices/i }).should("be.visible");
    cy.findByRole("heading", { name: /announcements/i }).should("be.visible");
    cy.get(".announcement-list > li").first().should("contain.text", "New notice");
  });
});
