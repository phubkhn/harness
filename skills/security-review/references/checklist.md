# Checklist security-review

Read this file before you write a finding.

1. Authentication/authorization on every new or changed endpoint/handler.
2. Input validation and injection checks (SQL, command, path traversal, SSRF) on untrusted input.
3. No hardcoded secrets, and no logging of sensitive data.
4. Sensitive data (PII, payment data): encrypted at rest/in transit, with least-privilege access.
5. If the diff touches `escalate_paths` in `rules/protected-paths.yaml`, confirm there is clear approval before you mark it as `approve`.
