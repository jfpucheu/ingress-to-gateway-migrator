# Troubleshooting Guide

## Common Issues

### Script fails with "No module named 'yaml'"
```bash
pip install pyyaml
```

### All Ingresses in failed-ingresses.yaml
Check the reasons in the file. Common causes:
- Unsupported annotations
- Invalid Ingress format
- Missing rules

### HTTPRoute created but no traffic
Check:
- Gateway exists: `kubectl get gateway -A`
- Correct namespace in parentRef
- Service backend exists
- Hostname matches request

### 404 Not Found
Verify:
- Hostname in HTTPRoute matches request Host header
- Path match is correct
- Service endpoints are ready

### 503 Service Unavailable
Check:
- Backend pods are running
- Service selector matches pod labels
- Correct port configuration

## Debug Commands

```bash
# Check routes
kubectl get httproute -A

# Describe route
kubectl describe httproute <name>

# Check Istio logs
kubectl logs -n istio-system -l istio=ingressgateway

# Verify with istioctl
istioctl analyze -A
```

## 🤖 AI-Generated Troubleshooting
This guide was created with Claude AI assistance. For more help, open an [issue](https://github.com/your-username/ingress-to-gateway-migrator/issues).
