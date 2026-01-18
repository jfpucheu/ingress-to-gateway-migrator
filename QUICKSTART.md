# 🚀 Quick Start - Ingress to Gateway API Migrator

## Installation in 2 Minutes

### 1. Download the project

```bash
# Option A: Clone from GitHub
git clone https://github.com/your-username/ingress-to-gateway-migrator.git
cd ingress-to-gateway-migrator

# Option B: Extract the ZIP archive
unzip ingress-to-gateway-migrator.zip
cd ingress-to-gateway-migrator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Test the installation

```bash
./test.sh
```

## Basic Usage

### Export your current Ingresses

```bash
# All namespaces
kubectl get ingress -A -o yaml > all-ingresses.yaml

# Specific namespace
kubectl get ingress -n production -o yaml > prod-ingresses.yaml
```

### Run the migration

```bash
./migrate.py -i all-ingresses.yaml -g istio-gateway
```

### Generated files

- `httproutes.yaml` - Migrated HTTP routes
- `tlsroutes.yaml` - Migrated TLS routes
- `failed-ingresses.yaml` - Unmigrated Ingresses with reasons

### Apply the routes (after verification!)

```bash
# Check generated files
cat httproutes.yaml
cat tlsroutes.yaml

# Apply in test first
kubectl apply -f httproutes.yaml -n test
kubectl apply -f tlsroutes.yaml -n test

# Then in production
kubectl apply -f httproutes.yaml
kubectl apply -f tlsroutes.yaml
```

## Next Steps

1. 📖 Read the [Migration Guide](docs/MIGRATION_GUIDE.md)
2. 🔍 Check out the [Examples](examples/)
3. ❓ FAQ in [docs/FAQ.md](docs/FAQ.md)
4. 🐛 Issues? See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Quick Help

```bash
# Show help
./migrate.py --help

# Migration with custom options
./migrate.py \
  -i ingresses.yaml \
  -g my-gateway \
  -o custom-http.yaml \
  -t custom-tls.yaml \
  -f custom-failed.yaml
```

## Kubernetes Prerequisites

Before applying routes, make sure you have:

1. ✅ Istio 1.16+ installed
2. ✅ Gateway API CRDs installed
3. ✅ A Gateway configured

```bash
# Check Istio
istioctl version

# Check Gateway API
kubectl get crd | grep gateway

# Check your Gateway
kubectl get gateway -A
```

## Need Help?

- 📚 [Complete documentation](README.md)
- 💬 [Open an issue](https://github.com/your-username/ingress-to-gateway-migrator/issues)
- 🤝 [Contribution guide](CONTRIBUTING.md)

---

**Good luck with your migration! 🎉**

## 🤖 AI-Assisted Tool

This migration tool was developed with Claude AI assistance to quickly address urgent migration needs. The tool is fully tested and production-ready.
