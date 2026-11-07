# Security policy

## Reporting a vulnerability

Please report security issues privately through GitHub's
[private vulnerability reporting](https://github.com/kirtanbhatt10/trustgate/security/advisories/new)
rather than a public issue. You should get a reply within 7 days.

Useful things to include:

- the trustgate version (`trustgate --version`) and Python version
- a minimal set of files that reproduces the problem
- what you expected to happen and what happened

## What counts as a vulnerability

- trustgate executing, importing or following anything from the scanned repository
- a crafted repository that crashes or hangs the scanner, or makes it skip files it should read
- a way for repository content to suppress or hide findings

A missed auto-run location or a false positive is a normal bug: open an issue for those.

## Supported versions

Only the latest release receives fixes.
