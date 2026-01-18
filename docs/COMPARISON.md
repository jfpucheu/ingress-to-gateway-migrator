# Comparison: Nginx Ingress vs Gateway API

## Quick Comparison

| Feature | Nginx Ingress | Gateway API | Gateway API Advantage |
|---------|---------------|-------------|----------------------|
| **Standard** | Provider-specific | Kubernetes standard | ✅ Multi-vendor portability |
| **Role separation** | No | Yes (Infra/Apps) | ✅ Better organization |
| **Advanced routing** | Limited | Native | ✅ More flexibility |
| **Protocols** | HTTP(S) | HTTP(S), TCP, TLS, gRPC | ✅ Extended support |
| **Extensibility** | Annotations | CRDs | ✅ Type-safe, validated |
| **Observability** | Basic | Advanced (with Istio) | ✅ Metrics, traces, logs |

## Migration Examples

### Simple HTTP

**Before (Nginx):**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: simple-app
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
```

**After (Gateway API):**
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: simple-app
spec:
  parentRefs:
  - name: istio-gateway
    namespace: istio-system
  hostnames:
  - app.example.com
  rules:
  - backendRefs:
    - name: app-service
      port: 80
```

## When to Migrate

### Migrate now if:
- ✅ Starting a new project
- ✅ Need advanced routing
- ✅ Want better role separation
- ✅ Already using Istio

### Wait if:
- ⏸️ Stable infrastructure with no change needs
- ⏸️ Team not yet trained on Gateway API
- ⏸️ Critical dependencies on specific Nginx annotations

## 🤖 AI-Assisted Documentation
This comparison was created with Claude AI assistance to provide rapid, comprehensive guidance.

For more details, see [Gateway API docs](https://gateway-api.sigs.k8s.io/).
