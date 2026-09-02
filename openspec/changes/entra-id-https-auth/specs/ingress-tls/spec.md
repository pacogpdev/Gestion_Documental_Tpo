# Ingress TLS Specification

## Purpose

Provide trusted production HTTPS without committed identity or certificate secrets.

## Requirements

### Requirement: Cert-Manager HTTPS Enforcement

Production ingress MUST obtain and use a valid Let's Encrypt certificate through cert-manager, enforce HTTPS redirect, and expose certificate readiness before redirect activation. Rendered manifests MUST NOT contain tokens, private keys, or committed certificates.

#### Scenario: Valid certificate enables HTTPS
- GIVEN DNS, ingress-controller, issuer, and cert-manager prerequisites are available
- WHEN the production manifests are applied
- THEN certificate issuance becomes ready and HTTP redirects to trusted HTTPS

#### Scenario: Certificate is not ready
- GIVEN certificate issuance or validation fails
- WHEN rollout validation runs
- THEN HTTPS enforcement is not activated and the failure is observable

### Requirement: Safe Rollout and Rollback

Production enablement MUST wait for strict-TDD gates and a pilot covering HTTPS, sign-in, and all roles. Rollback MUST revert the release slice and preserve a valid certificate path; it MUST NOT re-enable production `DEV_USER`, and controlled maintenance access SHALL be used instead.

#### Scenario: Failed pilot rollback
- GIVEN the pilot or certificate gate fails
- WHEN rollback is initiated
- THEN the prior valid ingress path is restored without enabling a development identity

## Assumptions and External Prerequisites

Platform owners provide cert-manager, a Let's Encrypt issuer, DNS, and ingress-controller support. These are externally owned prerequisites, not implementation tasks.
