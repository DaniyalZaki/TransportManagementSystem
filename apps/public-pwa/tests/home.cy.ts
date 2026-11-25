describe("public PWA foundation", () => {
  it("shows the public transport information entry point without authentication", () => {
    cy.visit("/");
    cy.findByRole("heading", { name: /transport service/i }).should("be.visible");
    cy.contains(/published transport information/i).should("be.visible");
  });
});
