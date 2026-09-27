# API / Integration Contract — API-###

Template only. Populate for actual required interfaces; do not invent endpoints, authentication methods or third-party capabilities.

| Field | Definition |
| --- | --- |
| API ID / name | API-### / TBD |
| Related FR / TR / INT IDs | TBD |
| Purpose / consumer / provider | TBD |
| Contract authority / documentation source / version | TBD |
| Availability and access verification | Verified evidence or explicit dependency / Q ID |
| Direction | TBD |
| Transport / method / path / event | Confirmed value or approved design decision |
| Authentication | Scheme and credential handling reference; no secrets in this document |
| Authorization / record scope | Roles, scopes and ownership constraints |
| Trigger / frequency | TBD |
| Preconditions / state rules | TBD |
| Side effects / data changes | TBD |
| Response / event acknowledgement | TBD |
| Error / failure contract | Error table below |
| Retry / timeout / stopping condition | Confirmed values/behavior or tracked question |
| Idempotency / duplicate / concurrency behavior | Confirmed applicable semantics or reasoned N/A |
| Pagination / filtering / sorting / limits | Confirmed values or reasoned N/A |
| Versioning / compatibility | Confirmed contract or tracked question |
| Logging / audit / sensitive-data exclusions | TBD |
| Environment / owner / support dependency | TBD |
| Acceptance / contract test IDs | TBD |

## Request / outbound payload

| Location / field | Data type | Required? | Source / mapping | Default | Validation / allowed values | Sensitive? | Description |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Response / inbound payload

| Outcome / field | Data type | Required / nullable? | Destination / mapping | Meaning / units | Validation / handling | Sensitive? |
| --- | --- | --- | --- | --- | --- | --- |

## Errors and recovery

| Condition | Protocol status / error code | Message / payload | Side effects / rollback | Retry eligibility | User/system recovery | Logging / notification |
| --- | --- | --- | --- | --- | --- | --- |

## Examples and verification

Provide valid/invalid request and response examples after the contract is established. Example values are labeled test data, never production secrets. Verify third-party facts against actual accessible documentation when developing a project specification; record the version/date and unresolved access limitations.

| Scenario | Input / fixture | Expected output / state | TEST ID | Verification evidence / not yet executed |
| --- | --- | --- | --- | --- |
