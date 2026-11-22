describe("public feedback", () => {
  beforeEach(() => {
    cy.intercept("GET", "**/api/v1/public/transport/**", { statusCode: 503, body: { detail: "unavailable" } });
    cy.intercept("GET", "**/api/v1/public/announcements", { announcements: [] });
    cy.intercept("GET", "**/api/v1/public/urgent-banners", { banners: [] });
  });

  it("submits anonymous feedback and shows a receipt", () => {
    cy.intercept("POST", "**/api/v1/public/feedback", { statusCode: 201, body: { message: "Feedback received. Thank you." } }).as("submitFeedback");
    cy.visit("/");
    cy.findByRole("textbox", { name: /feedback/i }).type("The 08:00 departure was late.");
    cy.findByRole("button", { name: /send feedback/i }).click();
    cy.wait("@submitFeedback").its("request.body").should("deep.include", { content: "The 08:00 departure was late.", honeypot: "" });
    cy.findByRole("status").should("contain.text", "Feedback received");
  });

  it("shows an immediate delivery error without offering status tracking", () => {
    cy.intercept("POST", "**/api/v1/public/feedback", { statusCode: 503, body: { message: "Feedback could not be delivered now. Please try again later." } });
    cy.visit("/");
    cy.findByRole("textbox", { name: /feedback/i }).type("The 08:00 departure was late.");
    cy.findByRole("button", { name: /send feedback/i }).click();
    cy.findByRole("alert").should("contain.text", "could not be delivered");
    cy.contains(/track|status/i).should("not.exist");
  });
});
