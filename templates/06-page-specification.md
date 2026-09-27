# Page Specification — PAGE-###

Repeat for every confirmed page, including relevant dialogs or clearly reference their parent page. Populate every field; use a reasoned N/A when a capability does not apply.

## Page contract

| Field | Specification |
| --- | --- |
| Page ID | PAGE-### |
| Page Name | TBD |
| Purpose | TBD |
| Module / requirement IDs | TBD |
| Allowed Roles | ROLE IDs, action and record-scope conditions |
| Navigation Source | Entry point, menu/parent/link, route if confirmed, back behavior |
| Filters | Complete filter records below |
| Search | Searchable fields, matching rules, trigger, minimum input if any, scope |
| Sort | Sortable fields, default order, tie-break behavior if required |
| Pagination | Mode, default/allowed size, total count behavior; values need confirmation |
| KPIs | KPI IDs, definitions/source, refresh and visibility |
| Charts | Chart IDs, axes/grouping/filter/date/drill-down definitions |
| Tables | Complete table/column records below |
| Buttons | Complete action records below |
| Forms | Complete field records below |
| Status indicators | Entity/status meanings and permitted actions per state |
| Permissions | View/data/action scope; UI and server behavior |
| Exports | Formats, columns, filters, selection/pagination scope, permissions and errors |
| Notifications | Trigger/recipient/channel and NOTIF IDs |
| Empty states | No data vs no matches vs unavailable data; allowed next action |
| Validation | Client/server rules, messages and input preservation |
| Error states | Error records below |
| Loading / in-progress state | Applicable progress, pending action and repeated-submission behavior |
| Responsive / localization requirements | Confirmed NFR references |
| Source / decision evidence | TBD |
| Open questions | Q IDs or None after review |

## Filters and search

| Control | Type | Data source | Operators / matching logic | Default | Dependencies | Apply / reset behavior | Permission scope | Empty / invalid value behavior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Clarify whether filters persist across navigation and whether search applies to the full permitted dataset or only current results. Do not assume persistence or matching behavior.

## Table — repeat for every table

- Table ID / name / purpose: TBD
- Data source / entity / API: TBD
- Row identity and record scope: TBD
- Default filtering / sort / pagination: TBD
- Row selection / row action behavior: TBD or N/A
- Empty / loading / error behavior: TBD

| Column name | Data type | Source | Filterable? | Sortable? | Editable? | Required? | Description |
| --- | --- | --- | --- | --- | --- | --- | --- |

Additional formatting, units, null handling, conditional visibility, aggregation and edit rules: TBD. “Required” means the presence/nullability of the underlying value, not merely whether a column is displayed.

## Form — repeat for every form

- Form ID / name / purpose: TBD
- Create/edit context and entity: TBD
- Submit action / API / permission: TBD
- Save/cancel/unsaved-change behavior: TBD
- Cross-field validation / error summary: TBD

| Field name | Field type | Required? | Default value | Source | Validation | Auto-complete logic | Dependencies | Read-only conditions | Visibility conditions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

For select/reference fields, define permitted options, source ownership, unavailable-option behavior and refresh assumptions. For uploads and calculations, link file-management and RULE requirements. Do not add fields solely because they are common in similar systems.

## Button / Action — repeat for every action

| Field | Action specification |
| --- | --- |
| Action ID / name | TBD |
| Who can use it | ROLE IDs and record-scope conditions |
| Preconditions | Record state, required data and dependencies |
| Confirmation required? | Yes / No / Conditional / TBD; exact decision and rationale |
| Confirmation content if applicable | Entity, consequence and confirm/cancel behavior |
| System action | Ordered behavior and linked API / FR / RULE IDs |
| Status change | Initial → next entity state, or confirmed no change |
| Notification | Recipient, trigger, channel and NOTIF ID, or reasoned N/A |
| Audit log entry | Event, entity and captured values, or reasoned N/A |
| Error behaviour | Permission/validation/state/network failures; data preservation and retry |
| Result / navigation | Observable result, refresh, route/dialog behavior |
| Repeated / concurrent action | Confirmed handling or tracked gap |
| Source / acceptance IDs | TBD |

Do not silently choose confirmation behavior for deletion or other destructive actions. Document the consequence and confirmed decision; surface undefined behavior as an open question and a specification-review finding.

## State and error behavior

| Condition | Visible content / message | Available actions | Disabled / hidden controls and reason | Data retained / refreshed | Recovery / navigation | Permission / rule references |
| --- | --- | --- | --- | --- | --- | --- |

Cover relevant first use/no data, no results, loading, validation failure, insufficient access, missing/deleted record, invalid status and unavailable dependency conditions. Confirm actual expected behavior rather than treating this review list as an implementation prescription.

## Page acceptance and traceability

| FR / RULE IDs | Scenario / role / data scope | AC IDs | TEST IDs | Task IDs after approval |
| --- | --- | --- | --- | --- |
