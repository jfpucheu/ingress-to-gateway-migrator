#!/usr/bin/env python3
"""
Script de migration Ingress Nginx vers Gateway API (HTTPRoute/TLSRoute) pour Istio
"""

import yaml
import argparse
import sys
from typing import Dict, List, Any, Tuple
from collections import defaultdict


class IngressMigrator:
    """Classe pour migrer les Ingress vers Gateway API"""
    
    # Annotations Nginx supportées et leur équivalent Istio/Gateway API
    SUPPORTED_ANNOTATIONS = {
        'nginx.ingress.kubernetes.io/rewrite-target': 'rewrite',
        'nginx.ingress.kubernetes.io/ssl-redirect': 'ssl-redirect',
        'nginx.ingress.kubernetes.io/force-ssl-redirect': 'force-ssl-redirect',
        'nginx.ingress.kubernetes.io/backend-protocol': 'backend-protocol',
        'nginx.ingress.kubernetes.io/cors-allow-origin': 'cors',
        'nginx.ingress.kubernetes.io/cors-allow-methods': 'cors',
        'nginx.ingress.kubernetes.io/cors-allow-headers': 'cors',
        'nginx.ingress.kubernetes.io/proxy-body-size': 'proxy-body-size',
        'nginx.ingress.kubernetes.io/proxy-connect-timeout': 'timeout',
        'nginx.ingress.kubernetes.io/proxy-send-timeout': 'timeout',
        'nginx.ingress.kubernetes.io/proxy-read-timeout': 'timeout',
    }
    
    # Annotations non supportées
    UNSUPPORTED_ANNOTATIONS = [
        'nginx.ingress.kubernetes.io/auth-type',
        'nginx.ingress.kubernetes.io/auth-secret',
        'nginx.ingress.kubernetes.io/auth-realm',
        'nginx.ingress.kubernetes.io/configuration-snippet',
        'nginx.ingress.kubernetes.io/server-snippet',
        'nginx.ingress.kubernetes.io/modsecurity-snippet',
        'nginx.ingress.kubernetes.io/limit-rps',
        'nginx.ingress.kubernetes.io/limit-rpm',
    ]
    
    def __init__(self, gateway_class: str, gateway_name: str = None, 
                 gateway_namespace: str = 'istio-system', gateway_port: int = None,
                 gateway_section: str = None):
        self.gateway_class = gateway_class
        self.gateway_name = gateway_name or gateway_class
        self.gateway_namespace = gateway_namespace
        self.gateway_port = gateway_port
        self.gateway_section = gateway_section
        self.http_routes = []
        self.tls_routes = []
        self.failed_ingresses = []
    
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
    
    def check_annotations(self, ingress: Dict) -> Tuple[bool, List[str]]:
        """Vérifie si les annotations sont supportées"""
        annotations = ingress.get('metadata', {}).get('annotations', {})
        unsupported = []
        
        for anno in annotations.keys():
            if anno.startswith('nginx.ingress.kubernetes.io/'):
                if anno in self.UNSUPPORTED_ANNOTATIONS:
                    unsupported.append(anno)
        
        return len(unsupported) == 0, unsupported
    
    def migrate_ingress(self, ingress: Dict) -> None:
        """Migre un Ingress vers HTTPRoute/TLSRoute"""
        try:
            is_supported, unsupported_annos = self.check_annotations(ingress)
            
            if not is_supported:
                self.failed_ingresses.append({
                    'ingress': ingress,
                    'reason': f"Annotations non supportées: {', '.join(unsupported_annos)}"
                })
                return
            
            spec = ingress.get('spec', {})
            tls_configs = spec.get('tls', [])
            rules = spec.get('rules', [])
            
            if not rules:
                self.failed_ingresses.append({
                    'ingress': ingress,
                    'reason': "Aucune règle définie dans l'Ingress"
                })
                return
            
            # Créer HTTPRoute pour chaque règle
            for rule in rules:
                http_route = self.create_http_route(ingress, rule, tls_configs)
                if http_route:
                    self.http_routes.append(http_route)
            
            # Créer TLSRoute si TLS est configuré
            if tls_configs:
                for tls_config in tls_configs:
                    tls_route = self.create_tls_route(ingress, tls_config)
                    if tls_route:
                        self.tls_routes.append(tls_route)
        
        except Exception as e:
            self.failed_ingresses.append({
                'ingress': ingress,
                'reason': f"Erreur lors de la migration: {str(e)}"
            })
    
    def create_http_route(self, ingress: Dict, rule: Dict, tls_configs: List) -> Dict:
        """Creates an HTTPRoute from an Ingress rule"""
        metadata = ingress.get('metadata', {})
        name = metadata.get('name', 'unnamed')
        namespace = metadata.get('namespace', 'default')
        host = rule.get('host', '')
        
        # Unique name for HTTPRoute
        route_name = f"{name}-{host.replace('.', '-')}" if host else name
        
        # Build parentRef with custom values
        parent_ref = {
            'name': self.gateway_name,
            'namespace': self.gateway_namespace
        }
        if self.gateway_port:
            parent_ref['port'] = self.gateway_port
        if self.gateway_section:
            parent_ref['sectionName'] = self.gateway_section
        
        http_route = {
            'apiVersion': 'gateway.networking.k8s.io/v1',
            'kind': 'HTTPRoute',
            'metadata': {
                'name': route_name,
                'namespace': namespace,
            },
            'spec': {
                'parentRefs': [parent_ref],
                'rules': []
            }
        }
        
        # Copy relevant labels and annotations
        if metadata.get('labels'):
            http_route['metadata']['labels'] = metadata['labels'].copy()
        
        # Add hostname if present
        if host:
            http_route['spec']['hostnames'] = [host]
        
        # Convert HTTP paths
        http_paths = rule.get('http', {}).get('paths', [])
        for path in http_paths:
            route_rule = self.convert_http_path(path, ingress)
            if route_rule:
                http_route['spec']['rules'].append(route_rule)
        
        return http_route if http_route['spec']['rules'] else None
    
    def convert_http_path(self, path: Dict, ingress: Dict) -> Dict:
        """Convertit un path HTTP Ingress en règle HTTPRoute"""
        path_value = path.get('path', '/')
        path_type = path.get('pathType', 'Prefix')
        backend = path.get('backend', {})
        
        # Conversion du pathType
        match_type = 'PathPrefix'
        if path_type == 'Exact':
            match_type = 'Exact'
        elif path_type == 'ImplementationSpecific':
            match_type = 'PathPrefix'  # Par défaut
        
        rule = {
            'matches': [{
                'path': {
                    'type': match_type,
                    'value': path_value
                }
            }],
            'backendRefs': []
        }
        
        # Convertir le backend
        if 'service' in backend:
            service = backend['service']
            backend_ref = {
                'name': service.get('name'),
                'port': service.get('port', {}).get('number', 80)
            }
            rule['backendRefs'].append(backend_ref)
        
        # Gérer les annotations de rewrite
        annotations = ingress.get('metadata', {}).get('annotations', {})
        if 'nginx.ingress.kubernetes.io/rewrite-target' in annotations:
            rewrite_target = annotations['nginx.ingress.kubernetes.io/rewrite-target']
            rule['filters'] = [{
                'type': 'URLRewrite',
                'urlRewrite': {
                    'path': {
                        'type': 'ReplacePrefixMatch',
                        'replacePrefixMatch': rewrite_target
                    }
                }
            }]
        
        return rule
    
    def create_tls_route(self, ingress: Dict, tls_config: Dict) -> Dict:
        """Creates a TLSRoute from TLS configuration - ONLY if ssl-passthrough is enabled"""
        metadata = ingress.get('metadata', {})
        annotations = metadata.get('annotations', {})
        
        # Only create TLSRoute if ssl-passthrough is explicitly enabled
        ssl_passthrough = annotations.get('nginx.ingress.kubernetes.io/ssl-passthrough', '').lower()
        if ssl_passthrough != 'true':
            return None
        
        name = metadata.get('name', 'unnamed')
        namespace = metadata.get('namespace', 'default')
        hosts = tls_config.get('hosts', [])
        secret_name = tls_config.get('secretName')
        
        if not hosts:
            return None
        
        # Unique name for TLSRoute
        route_name = f"{name}-tls-{hosts[0].replace('.', '-')}"
        
        # Build parentRef with custom values if provided
        parent_ref = {
            'name': self.gateway_name,
            'namespace': self.gateway_namespace
        }
        if self.gateway_port:
            parent_ref['port'] = self.gateway_port
        if self.gateway_section:
            parent_ref['sectionName'] = self.gateway_section
        
        tls_route = {
            'apiVersion': 'gateway.networking.k8s.io/v1alpha2',
            'kind': 'TLSRoute',
            'metadata': {
                'name': route_name,
                'namespace': namespace,
            },
            'spec': {
                'parentRefs': [parent_ref],
                'hostnames': hosts,
                'rules': [{
                    'backendRefs': [{
                        'name': self.gateway_name,
                        'port': 443
                    }]
                }]
            }
        }
        
        # Copy labels
        if metadata.get('labels'):
            tls_route['metadata']['labels'] = metadata['labels'].copy()
        
        # Add annotation to reference TLS secret if present
        if secret_name:
            tls_route['metadata']['annotations'] = {
                'gateway.istio.io/tls-secret': secret_name
            }
        
        return tls_route
    
    def save_routes(self, http_output: str, tls_output: str, failed_output: str) -> None:
        """Sauvegarde les routes générées et les échecs"""
        # Sauvegarder HTTPRoutes
        if self.http_routes:
            with open(http_output, 'w') as f:
                yaml.dump_all(self.http_routes, f, default_flow_style=False, sort_keys=False)
            print(f"✓ {len(self.http_routes)} HTTPRoute(s) générée(s) dans {http_output}")
        else:
            print("⚠ Aucun HTTPRoute généré")
        
        # Sauvegarder TLSRoutes
        if self.tls_routes:
            with open(tls_output, 'w') as f:
                yaml.dump_all(self.tls_routes, f, default_flow_style=False, sort_keys=False)
            print(f"✓ {len(self.tls_routes)} TLSRoute(s) générée(s) dans {tls_output}")
        else:
            print("⚠ Aucun TLSRoute généré")
        
        # Sauvegarder les échecs
        if self.failed_ingresses:
            with open(failed_output, 'w') as f:
                f.write("# Ingresses non migrés\n\n")
                for item in self.failed_ingresses:
                    f.write(f"# Raison: {item['reason']}\n")
                    f.write("---\n")
                    yaml.dump(item['ingress'], f, default_flow_style=False, sort_keys=False)
                    f.write("\n")
            print(f"⚠ {len(self.failed_ingresses)} Ingress non migré(s) - voir {failed_output}")
        else:
            print("✓ Tous les Ingress ont été migrés avec succès")


def main():
    parser = argparse.ArgumentParser(
        description='Migrate Nginx Ingress to Gateway API (HTTPRoute/TLSRoute) for Istio',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i ingresses.yaml -g istio-gateway
  %(prog)s -i ingresses.yaml -g istio-gateway --gateway-name my-gateway --gateway-namespace gateway-system
  %(prog)s -i ingresses.yaml -g my-gateway -o routes.yaml -t tls-routes.yaml --gateway-port 443
        """
    )
    
    parser.add_argument('-i', '--input', required=True,
                        help='YAML file containing Ingresses to migrate')
    parser.add_argument('-g', '--gateway-class', required=True,
                        help='Target Gateway class name (e.g., istio-gateway)')
    parser.add_argument('--gateway-name', 
                        help='Gateway resource name (defaults to gateway-class value)')
    parser.add_argument('--gateway-namespace', default='istio-system',
                        help='Gateway namespace (default: istio-system)')
    parser.add_argument('--gateway-port', type=int,
                        help='Gateway port to specify in parentRef (optional)')
    parser.add_argument('--gateway-section',
                        help='Gateway listener section name (optional)')
    parser.add_argument('-o', '--http-output', default='httproutes.yaml',
                        help='Output file for HTTPRoutes (default: httproutes.yaml)')
    parser.add_argument('-t', '--tls-output', default='tlsroutes.yaml',
                        help='Output file for TLSRoutes (default: tlsroutes.yaml)')
    parser.add_argument('-f', '--failed-output', default='failed-ingresses.yaml',
                        help='Output file for unmigrated Ingresses (default: failed-ingresses.yaml)')
    
    args = parser.parse_args()
    
    print(f"🔄 Migrating Ingress to Gateway API")
    print(f"   Input file: {args.input}")
    print(f"   Gateway class: {args.gateway_class}")
    if args.gateway_name:
        print(f"   Gateway name: {args.gateway_name}")
    print(f"   Gateway namespace: {args.gateway_namespace}")
    if args.gateway_port:
        print(f"   Gateway port: {args.gateway_port}")
    if args.gateway_section:
        print(f"   Gateway section: {args.gateway_section}")
    print()
    
    # Create migrator with gateway configuration
    migrator = IngressMigrator(
        gateway_class=args.gateway_class,
        gateway_name=args.gateway_name,
        gateway_namespace=args.gateway_namespace,
        gateway_port=args.gateway_port,
        gateway_section=args.gateway_section
    )
    
    # Load Ingresses
    ingresses = migrator.load_ingresses(args.input)
    print(f"📥 {len(ingresses)} Ingress loaded")
    print()
    
    # Migrate each Ingress
    for ingress in ingresses:
        migrator.migrate_ingress(ingress)
    
    # Save results
    print()
    migrator.save_routes(args.http_output, args.tls_output, args.failed_output)
    print()
    print("✅ Migration completed")
    print()
    print("ℹ️  Note: TLSRoutes are only created for Ingresses with ssl-passthrough annotation")
    print("   All other TLS certificates will be handled by the Gateway configuration")


if __name__ == '__main__':
    main()
