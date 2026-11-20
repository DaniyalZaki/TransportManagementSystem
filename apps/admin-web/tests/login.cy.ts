describe("admin web foundation", () => {
  it("shows the privileged sign-in boundary", () => {
    cy.visit("/");
    cy.findByRole("heading", { name: /transport management sign in/i }).should("be.visible");
    cy.contains(/supabase auth/i).should("be.visible");
    cy.findByLabelText(/email address/i).should("have.attr", "type", "email");
    cy.findByLabelText(/^password$/i).should("have.attr", "type", "password");
    cy.findByRole("button", { name: /sign in/i }).should("exist");
  });
});
