# Contributing

1. Create a focused branch.
2. Add or update synthetic fixtures for extraction changes.
3. Run `ruff check .` and `pytest -q`.
4. Run `npm test` inside `sdk/` for contract changes.
5. Explain accuracy or schema effects in the pull request.

Never commit real invoices, private documents, credentials, or personal data.
Use fictional organizations, reserved domains, and synthetic identifiers.

Changes to the JSON contract require a schema-version decision and matching
updates to the Python serializer, TypeScript types, runtime validator, tests,
examples, and changelog.
