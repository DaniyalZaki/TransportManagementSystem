describe("published transport information", () => {
  it("shows public current departures and today's published schedule", () => {
    cy.intercept("GET", "**/api/v1/public/transport/current-departures*", {
      service_date: "2026-11-18",
      published_at: "2026-11-18T08:00:00Z",
      departures: [
        {
          route_id: "R-01",
          bus_identifier: "C-12",
          status: "scheduled",
          scheduled_departure_at: "2026-11-18T14:00:00+05:00",
        },
        {
          route_id: "R-02",
          bus_identifier: "C-08",
          status: "no_further_departures_today",
          scheduled_departure_at: null,
        },
      ],
    }).as("currentDepartures");
    cy.intercept("GET", "**/api/v1/public/transport/schedule*", {
      service_date: "2026-11-18",
      service_status: "operating",
      published_at: "2026-11-18T08:00:00Z",
      entries: [
        {
          route_id: "R-01",
          origin: "Lahore",
          destination: "Campus",
          direction: "Inbound",
          bus_identifier: "C-12",
          scheduled_departure_at: "2026-11-18T14:00:00+05:00",
        },
      ],
    }).as("schedule");

    cy.visit("/");
    cy.wait(["@currentDepartures", "@schedule"]);

    cy.findByRole("heading", { name: /next departures/i }).should("be.visible");
    cy.contains("R-01").should("be.visible");
    cy.contains("C-12").should("be.visible");
    cy.contains("No further departures today").should("be.visible");
    cy.findByRole("heading", { name: /today's schedule/i }).should("be.visible");
    cy.contains("Lahore → Campus").should("be.visible");
    cy.contains("Inbound").should("be.visible");
    cy.findByRole("link", { name: /sign in/i }).should("not.exist");
  });
});
