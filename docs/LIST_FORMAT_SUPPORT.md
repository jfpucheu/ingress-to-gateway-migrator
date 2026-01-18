# Kubernetes List Format Support

## The Problem

When you export Ingresses using `kubectl get ingress -o yaml`, Kubernetes returns a **List** format:

```yaml
apiVersion: v1
kind: List
metadata:
  resourceVersion: ""
items:
- apiVersion: networking.k8s.io/v1
  kind: Ingress
  metadata:
    name: ingress1
  spec:
    # ...
- apiVersion: networking.k8s.io/v1
  kind: Ingress
  metadata:
    name: ingress2
  spec:
    # ...
```

This is **different** from multi-document YAML format:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress1
spec:
  # ...
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress2
spec:
  # ...
```

## The Solution

The migration script (v1.0.1+) now **automatically detects and handles both formats**:

```python
def load_ingresses(self, filename: str) -> List[Dict]:
    """Load Ingresses from a YAML file (supports both multi-doc and List formats)"""
    try:
        with open(filename, 'r') as f:
            content = f.read()
            docs = list(yaml.safe_load_all(content))
            ingresses = []
            
            for doc in docs:
                if not doc:
                    continue
                
                # Handle Kubernetes List format (kubectl get -o yaml)
                if doc.get('kind') == 'List' and 'items' in doc:
                    list_items = doc['items']
                    ingresses.extend([item for item in list_items if item.get('kind') == 'Ingress'])
                # Handle standard Ingress documents
                elif doc.get('kind') == 'Ingress':
                    ingresses.append(doc)
            
            return ingresses
    except Exception as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        sys.exit(1)
```

## Usage

Both export methods now work seamlessly:

```bash
# Method 1: kubectl export (List format) - ✅ WORKS
kubectl get ingress -A -o yaml > all-ingresses.yaml
./migrate.py -i all-ingresses.yaml -g istio-gateway

# Method 2: Manual YAML (multi-doc format) - ✅ WORKS
cat > my-ingresses.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
# ...
---
apiVersion: networking.k8s.io/v1
kind: Ingress
# ...
EOF
./migrate.py -i my-ingresses.yaml -g istio-gateway
```

## Real-World Test Results

Tested with a production file containing 23 Ingresses:

```
🔄 Migration des Ingress vers Gateway API
   Input file: devbench.yaml
   Gateway class: istio-gateway

📥 23 Ingress loaded

✓ 23 HTTPRoute(s) generated in httproutes.yaml
✓ 11 TLSRoute(s) generated in tlsroutes.yaml
✓ All Ingresses migrated successfully

✅ Migration completed
```

## Key Features

- ✅ **Automatic format detection** - No need to specify format
- ✅ **Robust parsing** - Handles both List and multi-doc YAML
- ✅ **Preserves all metadata** - Labels, annotations, namespaces
- ✅ **Production tested** - Works with real-world exports

## Why This Matters

Most users will use `kubectl get ingress -o yaml` to export their Ingresses, which produces List format. Without this support, the migration tool would fail on the most common use case!

This fix ensures the tool "just works" for everyone, regardless of how they export their Ingresses.

---

**Version:** 1.0.1+  
**Date:** January 18, 2026  
**Issue:** Fixed in response to user feedback
