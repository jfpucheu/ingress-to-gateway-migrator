# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Support for rate limiting annotations
- Web interface for migration
- Support for other providers (Nginx Gateway Fabric, Contour)
- Auto-generation of complementary Istio resources

## [1.0.0] - 2026-01-18

### Added
- Initial migration script Ingress → Gateway API
- Support for common Nginx annotations:
  - `rewrite-target` → URLRewrite filter
  - `ssl-redirect` → Metadata
  - `backend-protocol` → Backend metadata
  - `cors-allow-*` → CORS annotations
  - `proxy-*` → Timeout/size settings
- HTTPRoute generation from Ingress rules
- TLSRoute generation from TLS configuration
- Detection and reporting of unsupported annotations
- Comprehensive unit tests
- Complete documentation (README, guides, FAQ)
- Usage examples
- GitHub Actions workflow for CI/CD
- Quick test script

### Documented
- Step-by-step migration guide
- Troubleshooting guide
- Detailed FAQ
- Contribution guide
- Nginx vs Gateway API comparison

### Configuration
- Multi-platform support (Linux, macOS, Windows)
- Python 3.6+ support
- GitHub Actions configuration for automated testing

### Development Note
- 🤖 **AI-Assisted Development**: This initial release was developed with Claude AI assistance to rapidly address urgent migration tooling needs. The tool is fully tested and production-ready.

## Version Format

### [X.Y.Z] - YYYY-MM-DD

- X.0.0 : Breaking changes
- 0.Y.0 : New features (backwards compatible)
- 0.0.Z : Bug fixes (backwards compatible)

### Change Types

- **Added** : New features
- **Changed** : Changes to existing features
- **Deprecated** : Features that will be removed
- **Removed** : Removed features
- **Fixed** : Bug fixes
- **Security** : Security fixes

## Contributing

To contribute to the changelog, follow the [contribution guide](CONTRIBUTING.md).
