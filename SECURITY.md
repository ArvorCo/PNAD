# Security Policy

## Supported Use

This repository is intended for public-data workflows and local analytics.

## Please Report Privately If You Find

- credential exposure
- command-injection paths
- unsafe SQL or file-write behavior in LLM-facing flows
- path traversal issues in sync or extraction logic
- anything that could cause data loss or accidental exfiltration

## Not In Scope

- mistakes in public-source datasets upstream
- expected behavior of read-only analytics commands
- issues caused by local private data committed outside this repository

## Reporting

Use GitHub Security Advisories if enabled for the repository. If that is not
available, contact the maintainers privately before publishing details.

Include:

- affected command or file
- minimal reproduction
- impact
- proposed mitigation if you have one
