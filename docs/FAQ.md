# FAQ - Frequently Asked Questions

## General Questions

### What is Gateway API?

Gateway API is the next generation of Kubernetes APIs for ingress traffic management. It's the successor to the Ingress API, offering more features, flexibility, and expressiveness.

**Advantages over Ingress:**
- Role separation (Infrastructure vs Application)
- Native support for advanced routing
- Better protocol support (HTTP, HTTPS, TCP, UDP, TLS, gRPC)
- Extensibility via CRDs
- Multi-namespace support

### Why migrate to Gateway API?

- ✅ **Kubernetes standard** - Becoming the official standard
- ✅ **More features** - Advanced routing, weight-based routing, etc.
- ✅ **Better separation of concerns** - Ops vs Devs
- ✅ **Long-term support** - Ingress will gradually be deprecated
- ✅ **Multi-vendor compatibility** - Istio, Nginx, Contour, etc.

### Should I migrate immediately?

No, the Ingress API will continue to be supported for several years. However:
- For new projects: use Gateway API
- For existing projects: plan a gradual migration
- Use this migration to modernize your infrastructure

## Script Questions

### Does the script support all Nginx annotations?

No. The script supports common annotations that have equivalents in Gateway API/Istio. Unsupported annotations are listed in `failed-ingresses.yaml` with reasons.

**Supported annotations:**
- `rewrite-target`
- `ssl-redirect`
- `backend-protocol`
- `cors-allow-*`
- `proxy-*` (timeouts, body size)

**Annotations requiring additional Istio resources:**
- `auth-*` → RequestAuthentication, AuthorizationPolicy
- `rate-limit` → EnvoyFilter with rate limiting
- `configuration-snippet` → EnvoyFilter
- `modsecurity-*` → EnvoyFilter with WAF

### Can I customize the conversion?

Yes! The script is open-source. You can:
1. Modify `SUPPORTED_ANNOTATIONS` to add your annotations
2. Implement conversion logic in the methods
3. Contribute your changes to the project

### Does the script modify my existing Ingresses?

No, the script is **read-only**. It generates new HTTPRoute/TLSRoute files without touching the original Ingresses.

## Migration Questions

### Can I keep Ingress and HTTPRoute in parallel?

Yes! This is actually recommended for gradual migration. Use different LoadBalancers or gradually switch DNS.

### How to do zero-downtime migration?

**Option 1: Blue/Green**
1. Deploy HTTPRoute with new LoadBalancer
2. Test thoroughly
3. Switch DNS
4. Delete old Ingress

**Option 2: Canary with traffic weights**
Start with 10% traffic to Gateway API, gradually increase to 100%.

### What to do if an Ingress fails migration?

1. Check `failed-ingresses.yaml` for the reason
2. For unsupported annotations:
   - Create complementary Istio resources
   - Or migrate manually
3. Refer to the [Migration Guide](MIGRATION_GUIDE.md)

## Istio Questions

### Is Istio required?

For this script, yes, as it specifically targets Istio as the provider. However, Gateway API works with several providers: Istio, Nginx Gateway Fabric, Contour, Kong, Traefik, HAProxy.

### What Istio version is required?

Istio 1.16+ for full Gateway API v1 support. Recommended versions:
- **Minimum**: Istio 1.16
- **Recommended**: Istio 1.20+
- **Optimal**: Latest stable version

## 🤖 AI Development

### Was this tool developed entirely by AI?

This tool was developed **with Claude AI assistance** to rapidly address urgent migration needs. The combination of human expertise and AI assistance enabled:
- Rapid development with maintained quality
- Comprehensive documentation from the start
- Extensive test coverage
- Best practices implementation

All generated code has been reviewed, tested, and validated for production use.

---

**More questions?** Open an [issue](https://github.com/jfpucheu/ingress-to-gateway-migrator/issues) or check the [complete documentation](../README.md).
