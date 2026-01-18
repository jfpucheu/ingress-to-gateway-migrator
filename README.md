# 🔄 Ingress to Gateway API Migrator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Gateway API](https://img.shields.io/badge/Gateway%20API-v1-green.svg)](https://gateway-api.sigs.k8s.io/)
[![Istio Compatible](https://img.shields.io/badge/Istio-Compatible-blue.svg)](https://istio.io/)
[![Built with Claude](https://img.shields.io/badge/Built%20with-Claude%20AI-orange.svg)](https://www.anthropic.com/claude)

A Python CLI tool to automatically migrate your Nginx Ingress resources to Gateway API (HTTPRoute/TLSRoute) with Istio as the provider.

> **⚡ Built with AI:** Due to the urgent need for migration tooling, this project was rapidly developed with assistance from Claude AI by Anthropic. While AI-assisted, the code has been tested and is production-ready.

## 🌟 Features

- ✅ **Automatic migration** from Ingress to HTTPRoute and TLSRoute
- ✅ **Multi-rule and multi-host** support
- ✅ **Nginx annotation conversion** to Istio/Gateway API equivalents
- ✅ **Intelligent detection** of unsupported annotations
- ✅ **Detailed reports** on migration successes and failures
- ✅ **Preservation** of labels and metadata
- ✅ **Full TLS support** with secret mapping
- ✅ **Multi-document YAML** support

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Supported Annotations](#-supported-annotations)
- [Examples](#-examples)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Installation

### Prerequisites

- Python 3.6 or higher
- PyYAML

### Install via pip

```bash
pip install -r requirements.txt
```

### Install from source

```bash
git clone https://github.com/jfpucheu/ingress-to-gateway-migrator.git
cd ingress-to-gateway-migrator
pip install -r requirements.txt
chmod +x migrate.py
```

## ⚡ Quick Start

```bash
# Basic migration
./migrate.py -i ingresses.yaml -g istio-gateway

# Or with Python
python3 migrate.py -i ingresses.yaml -g istio-gateway
```

The script automatically generates:
- `httproutes.yaml` - All migrated HTTPRoutes
- `tlsroutes.yaml` - All migrated TLSRoutes
- `failed-ingresses.yaml` - Ingresses that couldn't be migrated with reasons

## 💻 Usage

### Full syntax

```bash
./migrate.py [OPTIONS]
```

### Available options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `-i, --input` | YAML file containing Ingresses | ✅ | - |
| `-g, --gateway-class` | Target Gateway class name | ✅ | - |
| `-o, --http-output` | Output file for HTTPRoutes | ❌ | `httproutes.yaml` |
| `-t, --tls-output` | Output file for TLSRoutes | ❌ | `tlsroutes.yaml` |
| `-f, --failed-output` | File for unmigrated Ingresses | ❌ | `failed-ingresses.yaml` |

### Usage examples

```bash
# Migration with single file
./migrate.py -i my-ingresses.yaml -g istio-gateway

# Migration with custom output filenames
./migrate.py \
  -i ingresses.yaml \
  -g my-gateway \
  -o http-routes.yaml \
  -t tls-routes.yaml \
  -f migration-failures.yaml

# Migration with multiple Ingresses in one file
./migrate.py -i all-ingresses.yaml -g prod-gateway
```

## ✅ Supported Annotations

### Migrated Nginx annotations

| Nginx Annotation | Gateway API / Istio Conversion |
|------------------|--------------------------------|
| `nginx.ingress.kubernetes.io/rewrite-target` | URLRewrite filter |
| `nginx.ingress.kubernetes.io/ssl-redirect` | Metadata annotation |
| `nginx.ingress.kubernetes.io/force-ssl-redirect` | Metadata annotation |
| `nginx.ingress.kubernetes.io/backend-protocol` | Backend metadata |
| `nginx.ingress.kubernetes.io/cors-allow-*` | CORS policy |
| `nginx.ingress.kubernetes.io/proxy-*` | Timeout/Size settings |

### Unsupported annotations

The following annotations require additional Istio resources:

- `nginx.ingress.kubernetes.io/auth-type` → Use `RequestAuthentication`
- `nginx.ingress.kubernetes.io/auth-secret` → Use `AuthorizationPolicy`
- `nginx.ingress.kubernetes.io/configuration-snippet` → Use `EnvoyFilter`
- `nginx.ingress.kubernetes.io/server-snippet` → Use `EnvoyFilter`
- `nginx.ingress.kubernetes.io/limit-rps` → Use `DestinationRule` with rate limiting
- `nginx.ingress.kubernetes.io/limit-rpm` → Use `DestinationRule` with rate limiting

## 📚 Examples

### Migration example

#### Before (Nginx Ingress)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
  namespace: default
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - example.com
    secretName: example-tls
  rules:
  - host: example.com
    http:
      paths:
      - path: /api(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
```

#### After (HTTPRoute)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: example-ingress-example-com
  namespace: default
spec:
  parentRefs:
  - name: istio-gateway
    namespace: istio-system
  hostnames:
  - example.com
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api(/|$)(.*)
    backendRefs:
    - name: api-service
      port: 8080
    filters:
    - type: URLRewrite
      urlRewrite:
        path:
          type: ReplacePrefixMatch
          replacePrefixMatch: /$2
```

More examples in the [`examples/`](examples/) folder.

## 📖 Documentation

- [Complete Migration Guide](docs/MIGRATION_GUIDE.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [Nginx vs Gateway API Comparison](docs/COMPARISON.md)
- [FAQ](docs/FAQ.md)

## 🧪 Testing

```bash
# Run tests
python3 -m pytest tests/

# Test with provided example
./migrate.py -i examples/sample-ingresses.yaml -g istio-gateway
```

## 🤝 Contributing

Contributions are welcome! Here's how to contribute:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## 🐛 Reporting Bugs

Open an [issue](https://github.com/jfpucheu/ingress-to-gateway-migrator/issues) with:
- Problem description
- Example Ingress that fails
- Python version
- Complete error output

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Gateway API SIG](https://gateway-api.sigs.k8s.io/)
- [Istio Project](https://istio.io/)
- [Kubernetes Ingress Nginx](https://kubernetes.github.io/ingress-nginx/)
- [Anthropic Claude AI](https://www.anthropic.com/claude) - for assisting in rapid development

## 🔗 Useful Resources

- [Gateway API Documentation](https://gateway-api.sigs.k8s.io/)
- [Istio Gateway API Tasks](https://istio.io/latest/docs/tasks/traffic-management/ingress/gateway-api/)
- [Nginx Ingress Annotations](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/)

## 📊 Project Status

⭐ If this project helped you, please give it a star!

---

## 🤖 AI-Assisted Development Note

This tool was developed with assistance from Claude AI to rapidly address the urgent need for Ingress to Gateway API migration tooling. The combination of human expertise and AI assistance allowed for:

- **Rapid development** while maintaining code quality
- **Comprehensive documentation** from the start
- **Extensive test coverage** to ensure reliability
- **Best practices** implementation

All generated code has been reviewed, tested, and validated for production use.

**Maintained by:** [your-email@example.com](mailto:your-email@example.com)
