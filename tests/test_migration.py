"""
Tests unitaires pour le script de migration Ingress vers Gateway API
"""

import pytest
import yaml
import sys
import os

# Ajouter le répertoire parent au path pour importer le module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrate import IngressMigrator


class TestIngressMigrator:
    """Tests pour la classe IngressMigrator"""
    
    @pytest.fixture
    def migrator(self):
        """Fixture pour créer un migrator"""
        return IngressMigrator("test-gateway")
    
    def test_init(self, migrator):
        """Test l'initialisation du migrator"""
        assert migrator.gateway_class == "test-gateway"
        assert migrator.http_routes == []
        assert migrator.tls_routes == []
        assert migrator.failed_ingresses == []
    
    def test_supported_annotations(self, migrator):
        """Test la détection des annotations supportées"""
        ingress = {
            'metadata': {
                'annotations': {
                    'nginx.ingress.kubernetes.io/rewrite-target': '/$2',
                    'nginx.ingress.kubernetes.io/ssl-redirect': 'true'
                }
            }
        }
        is_supported, unsupported = migrator.check_annotations(ingress)
        assert is_supported is True
        assert len(unsupported) == 0
    
    def test_unsupported_annotations(self, migrator):
        """Test la détection des annotations non supportées"""
        ingress = {
            'metadata': {
                'annotations': {
                    'nginx.ingress.kubernetes.io/auth-type': 'basic',
                    'nginx.ingress.kubernetes.io/configuration-snippet': 'test'
                }
            }
        }
        is_supported, unsupported = migrator.check_annotations(ingress)
        assert is_supported is False
        assert 'nginx.ingress.kubernetes.io/auth-type' in unsupported
        assert 'nginx.ingress.kubernetes.io/configuration-snippet' in unsupported
    
    def test_mixed_annotations(self, migrator):
        """Test avec annotations mixtes (supportées et non supportées)"""
        ingress = {
            'metadata': {
                'annotations': {
                    'nginx.ingress.kubernetes.io/rewrite-target': '/$2',
                    'nginx.ingress.kubernetes.io/auth-type': 'basic'
                }
            }
        }
        is_supported, unsupported = migrator.check_annotations(ingress)
        assert is_supported is False
        assert len(unsupported) == 1
    
    def test_http_route_creation(self, migrator):
        """Test la création d'un HTTPRoute"""
        ingress = {
            'metadata': {
                'name': 'test-ingress',
                'namespace': 'default',
                'labels': {'app': 'test'}
            },
            'spec': {
                'rules': [{
                    'host': 'example.com',
                    'http': {
                        'paths': [{
                            'path': '/api',
                            'pathType': 'Prefix',
                            'backend': {
                                'service': {
                                    'name': 'api-service',
                                    'port': {'number': 8080}
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        http_route = migrator.create_http_route(
            ingress, 
            ingress['spec']['rules'][0],
            []
        )
        
        assert http_route is not None
        assert http_route['kind'] == 'HTTPRoute'
        assert http_route['metadata']['name'] == 'test-ingress-example-com'
        assert http_route['metadata']['namespace'] == 'default'
        assert http_route['spec']['hostnames'] == ['example.com']
        assert len(http_route['spec']['rules']) == 1
    
    def test_http_route_with_rewrite(self, migrator):
        """Test la création d'un HTTPRoute avec rewrite"""
        ingress = {
            'metadata': {
                'name': 'test-ingress',
                'namespace': 'default',
                'annotations': {
                    'nginx.ingress.kubernetes.io/rewrite-target': '/new-path'
                }
            },
            'spec': {
                'rules': [{
                    'host': 'example.com',
                    'http': {
                        'paths': [{
                            'path': '/api',
                            'pathType': 'Prefix',
                            'backend': {
                                'service': {
                                    'name': 'api-service',
                                    'port': {'number': 8080}
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        http_route = migrator.create_http_route(
            ingress,
            ingress['spec']['rules'][0],
            []
        )
        
        assert http_route is not None
        rule = http_route['spec']['rules'][0]
        assert 'filters' in rule
        assert rule['filters'][0]['type'] == 'URLRewrite'
    
    def test_tls_route_creation(self, migrator):
        """Test la création d'un TLSRoute"""
        ingress = {
            'metadata': {
                'name': 'test-ingress',
                'namespace': 'default',
                'labels': {'app': 'test'}
            },
            'spec': {}
        }
        
        tls_config = {
            'hosts': ['example.com', 'www.example.com'],
            'secretName': 'example-tls'
        }
        
        tls_route = migrator.create_tls_route(ingress, tls_config)
        
        assert tls_route is not None
        assert tls_route['kind'] == 'TLSRoute'
        assert tls_route['metadata']['name'] == 'test-ingress-tls-example-com'
        assert tls_route['spec']['hostnames'] == ['example.com', 'www.example.com']
        assert tls_route['metadata']['annotations']['gateway.istio.io/tls-secret'] == 'example-tls'
    
    def test_path_type_conversion(self, migrator):
        """Test la conversion des pathType"""
        test_cases = [
            ('Prefix', 'PathPrefix'),
            ('Exact', 'Exact'),
            ('ImplementationSpecific', 'PathPrefix')
        ]
        
        for nginx_type, expected_gateway_type in test_cases:
            path = {
                'path': '/test',
                'pathType': nginx_type,
                'backend': {
                    'service': {
                        'name': 'test-service',
                        'port': {'number': 80}
                    }
                }
            }
            
            ingress = {'metadata': {'annotations': {}}}
            rule = migrator.convert_http_path(path, ingress)
            
            assert rule['matches'][0]['path']['type'] == expected_gateway_type
    
    def test_backend_conversion(self, migrator):
        """Test la conversion du backend"""
        path = {
            'path': '/test',
            'pathType': 'Prefix',
            'backend': {
                'service': {
                    'name': 'test-service',
                    'port': {'number': 8080}
                }
            }
        }
        
        ingress = {'metadata': {'annotations': {}}}
        rule = migrator.convert_http_path(path, ingress)
        
        assert len(rule['backendRefs']) == 1
        assert rule['backendRefs'][0]['name'] == 'test-service'
        assert rule['backendRefs'][0]['port'] == 8080
    
    def test_no_rules_ingress(self, migrator):
        """Test avec un Ingress sans règles"""
        ingress = {
            'metadata': {
                'name': 'empty-ingress',
                'namespace': 'default'
            },
            'spec': {}
        }
        
        migrator.migrate_ingress(ingress)
        
        assert len(migrator.failed_ingresses) == 1
        assert 'Aucune règle' in migrator.failed_ingresses[0]['reason']
    
    def test_labels_preservation(self, migrator):
        """Test que les labels sont préservés"""
        ingress = {
            'metadata': {
                'name': 'test-ingress',
                'namespace': 'default',
                'labels': {
                    'app': 'myapp',
                    'env': 'production'
                }
            },
            'spec': {
                'rules': [{
                    'host': 'example.com',
                    'http': {
                        'paths': [{
                            'path': '/',
                            'pathType': 'Prefix',
                            'backend': {
                                'service': {
                                    'name': 'myapp',
                                    'port': {'number': 80}
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        http_route = migrator.create_http_route(
            ingress,
            ingress['spec']['rules'][0],
            []
        )
        
        assert 'labels' in http_route['metadata']
        assert http_route['metadata']['labels']['app'] == 'myapp'
        assert http_route['metadata']['labels']['env'] == 'production'


class TestIntegration:
    """Tests d'intégration"""
    
    def test_full_migration(self, tmp_path):
        """Test une migration complète"""
        # Créer un fichier Ingress de test
        ingress_file = tmp_path / "test-ingress.yaml"
        ingress_content = """
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-ingress
  namespace: default
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
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
"""
        ingress_file.write_text(ingress_content)
        
        # Exécuter la migration
        migrator = IngressMigrator("test-gateway")
        ingresses = migrator.load_ingresses(str(ingress_file))
        
        assert len(ingresses) == 1
        
        for ingress in ingresses:
            migrator.migrate_ingress(ingress)
        
        # Vérifier les résultats
        assert len(migrator.http_routes) == 1
        assert len(migrator.tls_routes) == 1
        assert len(migrator.failed_ingresses) == 0
    
    def test_multi_document_yaml(self, tmp_path):
        """Test avec un fichier YAML multi-documents"""
        ingress_file = tmp_path / "multi-ingress.yaml"
        ingress_content = """
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-1
  namespace: default
spec:
  rules:
  - host: app1.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app1
            port:
              number: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-2
  namespace: default
spec:
  rules:
  - host: app2.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app2
            port:
              number: 80
"""
        ingress_file.write_text(ingress_content)
        
        migrator = IngressMigrator("test-gateway")
        ingresses = migrator.load_ingresses(str(ingress_file))
        
        assert len(ingresses) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
