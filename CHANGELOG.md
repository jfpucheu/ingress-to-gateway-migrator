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

## [1.0.2] - 2026-01-18

### Changed
- 🔐 **TLS Certificate Strategy**: TLSRoutes are now **only created for Ingresses with `ssl-passthrough: true` annotation**. All other TLS certificates are expected to be handled at the Gateway level, aligning with modern Gateway API architecture.

### Added
- 🎛️ **Gateway Configuration Options**: New CLI parameters for precise Gateway targeting:
  - `--gateway-name`: Specify Gateway resource name (defaults to gateway-class)
  - `--gateway-namespace`: Specify Gateway namespace (defaults to istio-system)
  - `--gateway-port`: Specify port in parentRef (optional)
  - `--gateway-section`: Specify listener section name (optional)

### Example
```bash
# Old behavior: All TLS configs → TLSRoutes
./migrate.py -i ingresses.yaml -g istio-gateway
# Result: 11 TLSRoutes created

# New behavior: Only ssl-passthrough → TLSRoutes
./migrate.py -i ingresses.yaml -g istio \
  --gateway-name prod-gateway \
  --gateway-namespace gateway-system \
  --gateway-port 443
# Result: 1 TLSRoute created (only for ssl-passthrough)
```

## [1.0.1] - 2026-01-18

### Fixed
- 🐛 **Kubernetes List format support**: Fixed issue where files from `kubectl get ingress -o yaml` (List format) were not properly parsed. The script now correctly handles both:
  - Standard multi-document YAML (with `---` separators)
  - Kubernetes List format (with `kind: List` and `items:` array)

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
