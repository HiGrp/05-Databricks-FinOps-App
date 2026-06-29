# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 1.0.x   | Yes       |

## Reporting a vulnerability

If you discover a security issue in FinOps Optimizer, please report it responsibly:

1. **Do not** open a public GitHub issue for security-sensitive findings.
2. Email your report to the maintainer listed in your Marketplace provider profile
   (or your internal security contact if this is a private deployment).
3. Include steps to reproduce, affected components, and potential impact.

We aim to acknowledge reports within **5 business days** and provide a remediation
timeline when a fix is confirmed.

## Security practices

- The app uses the **Databricks App service principal** and the SDK — no PATs in code.
- SQL runs against **system tables** in the consumer workspace; no data is sent to third parties.
- Optional environment variables reference **consumer-owned** Delta tables and Unity Catalog volumes only.
- Dependencies are listed in `requirements.txt` for supply-chain review.
