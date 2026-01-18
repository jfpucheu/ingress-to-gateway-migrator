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
    
    def __init__(self, gateway_class: str):
        self.gateway_class = gateway_class
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
        """Crée un HTTPRoute depuis une règle Ingress"""
        metadata = ingress.get('metadata', {})
        name = metadata.get('name', 'unnamed')
        namespace = metadata.get('namespace', 'default')
        host = rule.get('host', '')
        
        # Nom unique pour l'HTTPRoute
        route_name = f"{name}-{host.replace('.', '-')}" if host else name
        
        http_route = {
            'apiVersion': 'gateway.networking.k8s.io/v1',
            'kind': 'HTTPRoute',
            'metadata': {
                'name': route_name,
                'namespace': namespace,
            },
            'spec': {
                'parentRefs': [{
                    'name': self.gateway_class,
                    'namespace': 'istio-system',  # À adapter selon votre configuration
                }],
                'rules': []
            }
        }
        
        # Copier les labels et annotations pertinentes
        if metadata.get('labels'):
            http_route['metadata']['labels'] = metadata['labels'].copy()
        
        # Ajouter hostname si présent
        if host:
            http_route['spec']['hostnames'] = [host]
        
        # Convertir les paths HTTP
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
        """Crée un TLSRoute depuis une configuration TLS"""
        metadata = ingress.get('metadata', {})
        name = metadata.get('name', 'unnamed')
        namespace = metadata.get('namespace', 'default')
        hosts = tls_config.get('hosts', [])
        secret_name = tls_config.get('secretName')
        
        if not hosts or not secret_name:
            return None
        
        # Nom unique pour le TLSRoute
        route_name = f"{name}-tls-{hosts[0].replace('.', '-')}"
        
        tls_route = {
            'apiVersion': 'gateway.networking.k8s.io/v1alpha2',
            'kind': 'TLSRoute',
            'metadata': {
                'name': route_name,
                'namespace': namespace,
            },
            'spec': {
                'parentRefs': [{
                    'name': self.gateway_class,
                    'namespace': 'istio-system',
                    'sectionName': 'https'
                }],
                'hostnames': hosts,
                'rules': [{
                    'backendRefs': [{
                        'name': self.gateway_class,
                        'port': 443
                    }]
                }]
            }
        }
        
        # Copier les labels
        if metadata.get('labels'):
            tls_route['metadata']['labels'] = metadata['labels'].copy()
        
        # Ajouter une annotation pour référencer le secret TLS
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
        description='Migre les Ingress Nginx vers Gateway API (HTTPRoute/TLSRoute) pour Istio',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s -i ingresses.yaml -g istio-gateway
  %(prog)s -i ingresses.yaml -g my-gateway -o routes.yaml -t tls-routes.yaml
        """
    )
    
    parser.add_argument('-i', '--input', required=True,
                        help='Fichier YAML contenant les Ingress à migrer')
    parser.add_argument('-g', '--gateway-class', required=True,
                        help='Nom de la Gateway classe cible (ex: istio-gateway)')
    parser.add_argument('-o', '--http-output', default='httproutes.yaml',
                        help='Fichier de sortie pour les HTTPRoutes (défaut: httproutes.yaml)')
    parser.add_argument('-t', '--tls-output', default='tlsroutes.yaml',
                        help='Fichier de sortie pour les TLSRoutes (défaut: tlsroutes.yaml)')
    parser.add_argument('-f', '--failed-output', default='failed-ingresses.yaml',
                        help='Fichier de sortie pour les Ingress non migrés (défaut: failed-ingresses.yaml)')
    
    args = parser.parse_args()
    
    print(f"🔄 Migration des Ingress vers Gateway API")
    print(f"   Fichier d'entrée: {args.input}")
    print(f"   Gateway classe: {args.gateway_class}")
    print()
    
    # Créer le migrateur
    migrator = IngressMigrator(args.gateway_class)
    
    # Charger les Ingress
    ingresses = migrator.load_ingresses(args.input)
    print(f"📥 {len(ingresses)} Ingress chargé(s)")
    print()
    
    # Migrer chaque Ingress
    for ingress in ingresses:
        migrator.migrate_ingress(ingress)
    
    # Sauvegarder les résultats
    print()
    migrator.save_routes(args.http_output, args.tls_output, args.failed_output)
    print()
    print("✅ Migration terminée")


if __name__ == '__main__':
    main()
