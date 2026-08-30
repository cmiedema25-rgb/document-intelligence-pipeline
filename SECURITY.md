# Security policy

## Supported version

Security fixes are applied to the latest release on the `main` branch.

## Reporting

Please do not open a public issue containing private documents, credentials, or
personally identifiable information. Open an issue containing only a minimal,
synthetic reproduction and label it `security`.

## Data handling

The core extractor runs locally and does not transmit document contents. The
HTTP service binds to localhost by default, limits request bodies, rejects
unsupported content types, and returns structured errors. Deployments should
add authentication, TLS, request logging controls, and tenant isolation at the
gateway.

All repository fixtures are synthetic and use reserved `.example` domains and
fictional organizations.
