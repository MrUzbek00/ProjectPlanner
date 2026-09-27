# Solution Structure and Module Register

TEST FIXTURE.

## Module register

| MOD ID | Module name | Type | Parent module | Purpose | Security boundary | Data ownership |
| --- | --- | --- | --- | --- | --- | --- |
| MOD-001 | Authentication | User-facing | None | Sign-in, password reset and lockout | Public entry point; account data is private to its holder | ENT-001, ENT-002 |
| MOD-002 | Notifications | Notification | None | Outbound email through the existing notification service | Internal; called only by other modules | None |
