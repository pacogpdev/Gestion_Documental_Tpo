# Delta for Supplier Stats Dashboard

## MODIFIED Requirements

### Requirement: Stats Icon in Suppliers Table — chart action per row

The Suppliers table MUST show an identifiable chart/statistics action for every supplier row to Admin, Approver, and Viewer users. The action MUST be keyboard accessible, have an accessible name, and point to that supplier’s dashboard; it MUST NOT be shown to Clerk users.
(Previously: Displayed the action only to Admin and Approver and hid it from Clerk and Viewer.)

#### Scenario: Icon visible for Admin, Approver, and Viewer
- GIVEN the Suppliers table contains supplier rows
- WHEN an Admin, Approver, or Viewer views the table
- THEN each row displays an accessible statistics action

#### Scenario: Icon hidden for Clerk
- GIVEN a Clerk views supplier rows
- WHEN the table renders
- THEN no statistics action is displayed

### Requirement: Dashboard Page — charts and KPIs

The route `/suppliers/:id/dashboard` MUST display the selected supplier’s name and tax ID, an area chart for the last twelve monthly amounts, a donut chart comparing the supplier percentage with the remainder of suppliers, a horizontal bar chart for the top ten line items, a pie chart for Approved/Rejected/Pending distribution, and KPI cards for annual total, percentage of total, average invoice amount, and invoice count. Values MUST match the stats response. It MUST be available to Admin, Approver, and Viewer users; Clerk MUST NOT access it.
(Previously: Defined dashboard content but its eligible-user scenario named only Admin and Approver.)

#### Scenario: Click opens the supplier dashboard
- GIVEN an Admin, Approver, or Viewer is viewing a supplier row
- WHEN the user activates its stats action
- THEN the application navigates to `/suppliers/{id}/dashboard` for that supplier

#### Scenario: Charts render with data
- GIVEN the dashboard stats response contains monthly, line-item, percentage, and status data
- WHEN the dashboard loads
- THEN all four charts render the corresponding datasets and identify their displayed metric

#### Scenario: KPIs show correct values
- GIVEN the stats response contains annual total 12,000, percentage 40, average 1,200, and 10 invoices
- WHEN the dashboard loads
- THEN the KPI cards display 12,000, 40%, 1,200, and 10 respectively

#### Scenario: Empty statistics render safely
- GIVEN the selected supplier has zero invoices and zero annual total
- WHEN the dashboard loads
- THEN the KPI cards show zero values and the charts show empty or zero distributions without an error
