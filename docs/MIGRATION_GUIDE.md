# Migration Guide: Nginx Ingress → Gateway API

Complete guide for migrating your Nginx Ingress resources to Gateway API with Istio.

## Prerequisites

- Kubernetes 1.23+
- Istio 1.16+ installed
- Gateway API CRDs installed
- A configured Gateway

## Quick Migration Steps

### 1. Export your Ingresses
```bash
kubectl get ingress -A -o yaml > all-ingresses.yaml
```

### 2. Run the migration
```bash
./migrate.py -i all-ingresses.yaml -g istio-gateway
```

### 3. Review outputs
- Check `httproutes.yaml`
- Check `tlsroutes.yaml`
- Review `failed-ingresses.yaml`

### 4. Apply in test environment
```bash
kubectl apply -f httproutes.yaml -n test
kubectl apply -f tlsroutes.yaml -n test
```

### 5. Test thoroughly
```bash
curl -H "Host: example.com" http://<gateway-ip>/
```

### 6. Apply to production
After successful testing, apply to production.

## Handling Failed Migrations

For Ingresses in `failed-ingresses.yaml`, create appropriate Istio resources:

**Authentication:**
```yaml
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
# ... configuration
```

**Rate Limiting:**
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
# ... configuration
```

See [examples](../examples/) for more details.

## 🤖 AI-Assisted Tool
This migration guide was developed with Claude AI assistance for rapid deployment.

For complete guide, see the full documentation.
