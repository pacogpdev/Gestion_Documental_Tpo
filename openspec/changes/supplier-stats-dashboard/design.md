# Design: Supplier Statistics Dashboard

## Technical Approach

Extend the existing FastAPI suppliers router with a read-only, server-aggregated endpoint. Define one trailing-12-calendar-month window (first day of the month 11 months before today through the first day of next month) and use it for every metric. Add a camelCase Pydantic contract, a role-aware React page, route, table link, and Recharts visualizations. The API remains authoritative for all totals.

## Architecture Decisions

### Decision: Server-side aggregation

**Choice**: Use SQLAlchemy aggregates in `suppliers.py`; do not fetch invoices for frontend aggregation.
**Alternatives considered**: React-side aggregation, rejected because it exposes unnecessary data and duplicates business rules.
**Rationale**: A single contract is faster, consistent, and testable against SQLite.

### Decision: Cross-dialect month grouping

**Choice**: Filter `Invoice.date >= start` and `< end`; group with `extract("year", Invoice.date)` and `extract("month", Invoice.date)`, then pre-fill twelve buckets in Python.
**Alternatives considered**: SQLite-only `strftime`, rejected because production also targets SQL Server.
**Rationale**: The range is index-friendly and always returns ordered zero months.

### Decision: Defense-in-depth role access

**Choice**: `Depends(RoleChecker(["Admin", "Approver"]))`; UI shows links/pages only for `hasRole('Admin') || hasRole('Approver')`.
**Alternatives considered**: UI-only hiding, rejected because direct API access must remain protected.
**Rationale**: Follows existing backend and frontend role patterns while enabling Approvers to use Suppliers.

## Data Flow

    Suppliers row Link → /suppliers/:id/dashboard → GET /api/suppliers/:id/stats
       ↑ role gate                                             ↓
    React cards/charts ← JSON ← SQLAlchemy queries (SQLite/SQL Server)

Verify the supplier first (404). Then run these grouped/scalar queries, all with the same date predicates:

```python
func.coalesce(func.sum(Invoice.total_amount), 0), func.count(Invoice.id), func.avg(Invoice.total_amount)
func.coalesce(func.sum(Invoice.total_amount), 0)  # grand total, no supplier predicate
extract("year", Invoice.date), extract("month", Invoice.date), func.sum(Invoice.total_amount)
LineItem.description, func.sum(LineItem.total_price), func.count(distinct(Invoice.id))
Invoice.status, func.count(Invoice.id)  # status distribution
```

Top items use `JOIN LineItem → Invoice`, group by description, order descending, limit 10. Top invoice orders `total_amount DESC`. Empty aggregates are zero; the top invoice is `null`. All statuses are included, and stored amounts are assumed to share a reporting currency; no conversion is in scope.

Compute `annualPercentage = supplierTotal / grandTotal * 100`, or `0` when `grandTotal` is zero.

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/app/api/endpoints/suppliers.py` | Modify | Endpoint/queries. |
| `backend/app/models/schemas.py` | Modify | Response models. |
| `backend/tests/api/test_supplier_stats.py` | Create | SQLite tests, first. |
| `frontend/src/pages/SupplierDashboard.tsx` | Create | Dashboard page. |
| `frontend/src/pages/SupplierDashboard.test.tsx` | Create | MSW component tests. |
| `frontend/src/pages/SupplierDashboard.handlers.ts` | Create | Fixtures. |
| `frontend/src/pages/Suppliers.tsx` | Modify | Chart link. |
| `frontend/src/routes/index.tsx` | Modify | Dashboard route. |
| `frontend/src/components/Navbar.tsx` | Modify | Approver access. |
| `frontend/package.json`, `frontend/package-lock.json` | Modify | Recharts dependency. |

## Interfaces / Contracts

Implement `MonthlyAmount`, `TopLineItem`, `StatusDistribution`, `TopInvoice`, and `SupplierStatsResponse` Pydantic models with camelCase fields and `response_model=SupplierStatsResponse`.

```json
{
  "supplierName": "Acme", "taxId": "TAX-1", "totalInvoices": 10,
  "annualTotal": 12000.0, "annualPercentage": 40.0, "grandTotal": 30000.0,
  "monthlyAmounts": [{"month": "2026-01", "amount": 3815.70}],
  "topLineItems": [{"description": "Hosting", "totalAmount": 5000.0, "invoiceCount": 4}],
  "statusDistribution": {"Approved": 6, "Rejected": 1, "Pending": 3},
  "averageInvoiceAmount": 1200.0,
  "topInvoice": {"invoiceNumber": "INV-9", "amount": 2500.0}
}
```

`SupplierDashboard` uses `ResponsiveContainer`: `AreaChart` for monthly amounts; `PieChart` + `Pie(innerRadius)` for supplier/rest percentage; horizontal `BarChart` for top items; and `PieChart` for statuses. Use a responsive KPI grid, full-width area chart, two-column donut/status charts, and full-width item chart. Zero data renders labelled empty states. Add headings, `aria-label`s, and `data-testid`s to observable charts/actions.

## Testing Strategy

**RED first.** Backend tests seed inside/outside-window invoices, repeated descriptions, statuses, and a second supplier. Assert twelve buckets/zero fill, totals, average, percentage/grand total, top-10 ordering/counts, top invoice, 404, empty supplier, and Admin/Approver success versus Clerk/Viewer 403. Use the existing SQLite fixture and explicitly enable role enforcement for negative-role tests.

Frontend tests add MSW stats fixtures first and assert Admin/Approver link visibility, dashboard fetch/KPIs/chart labels, empty data, API error, and Back navigation. Extend `Suppliers.test.tsx` for link destination and Viewer exclusion. Add route smoke coverage. Run `cd backend && pytest` and `cd frontend && npm test`.

## Threat Matrix

Routing applies only to UI navigation; other listed boundaries do not exist. Eligible links use the supplier ID; unauthorized users make no stats request; unknown IDs show 404. RED tests cover navigation, Viewer exclusion, and unknown supplier.

| Boundary | Applicability | Design response | Planned RED tests |
|---|---|---|---|
| Documentation-like paths | N/A — no executable classification | None | None |
| Git repository selection | N/A — no Git automation | None | None |
| Commit state | N/A — no commit automation | None | None |
| Push state | N/A — no push automation | None | None |
| PR commands | N/A — no PR automation | None | None |

## Migration / Rollout

No migration required. Install `recharts`, deploy both layers, and run both configured test commands.

## Open Questions

- [ ] Confirm whether invoices can mix currencies; the requested response has no conversion or reporting-currency field.
