from django.test import TestCase, override_settings
from unittest.mock import patch, Mock, ANY
from apps.core.services.geocoding import GeocodingService

class GeocodingServiceTestCase(TestCase):
    
    @patch('apps.core.services.geocoding.requests.get')
    def test_osm_geocoding_success(self, mock_get):
        """Test geocodificación exitosa con OSM"""
        # Configurar mock para OSM
        mock_osm_response = Mock()
        mock_osm_response.json.return_value = [{
            'lat': '18.4861',
            'lon': '-69.9312',
            'display_name': 'Santo Domingo, República Dominicana'
        }]
        mock_osm_response.raise_for_status.return_value = None
        
        # Configurar el mock para que solo responda a la URL de OSM
        def side_effect(url, *args, **kwargs):
            if 'nominatim.openstreetmap.org' in url:
                return mock_osm_response
            return Mock(json=Mock(return_value={'status': 'ZERO_RESULTS'}))
            
        mock_get.side_effect = side_effect
        
        result = GeocodingService.geocode_address('Calle Principal 123')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['latitude'], 18.4861)
        self.assertEqual(result['longitude'], -69.9312)
        self.assertEqual(result['source'], 'osm')
        
        # Verificar que se llamó a OSM
        mock_get.assert_called_once()
        self.assertIn('nominatim.openstreetmap.org', mock_get.call_args[0][0])
    
    @override_settings(GOOGLE_MAPS_API_KEY='dummy-key')
    @patch('apps.core.services.geocoding.requests.get')
    def test_geocoding_fallback_to_google(self, mock_get):
        """Test fallback a Google Maps cuando OSM falla"""
        # Mock para OSM (falla)
        mock_osm_response = Mock()
        mock_osm_response.json.return_value = []
        mock_osm_response.raise_for_status.return_value = None
        
        # Mock para Google (éxito)
        mock_google_response = Mock()
        mock_google_response.json.return_value = {
            'status': 'OK',
            'results': [{
                'formatted_address': 'Santo Domingo, República Dominicana',
                'geometry': {
                    'location': {
                        'lat': 18.4861,
                        'lng': -69.9312
                    }
                }
            }]
        }
        mock_google_response.raise_for_status.return_value = None
        
        # Configurar side_effect para manejar múltiples llamadas
        def side_effect(url, *args, **kwargs):
            if 'nominatim.openstreetmap.org' in url:
                return mock_osm_response
            elif 'maps.googleapis.com' in url:
                return mock_google_response
            return Mock(json=Mock(return_value={}))
            
        mock_get.side_effect = side_effect
        
        result = GeocodingService.geocode_address('Calle Principal 123')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['source'], 'google')
        
        # Verificar que se llamó a ambos servicios
        self.assertGreaterEqual(mock_get.call_count, 2)
        calls = [call[0][0] for call in mock_get.call_args_list]
        self.assertTrue(any('nominatim.openstreetmap.org' in url for url in calls))
        self.assertTrue(any('maps.googleapis.com' in url for url in calls))
    
    @override_settings(GOOGLE_MAPS_API_KEY='dummy-key')
    @patch('apps.core.services.geocoding.requests.get')
    def test_google_geocoding_missing_geometry(self, mock_get):
        """Test manejo de respuesta de Google Maps sin geometría"""
        # Mock para OSM (falla)
        mock_osm_response = Mock()
        mock_osm_response.json.return_value = []
        mock_osm_response.raise_for_status.return_value = None
        
        # Mock para Google (sin geometría)
        mock_google_response = Mock()
        mock_google_response.json.return_value = {
            'status': 'OK',
            'results': [{
                'formatted_address': 'Santo Domingo, República Dominicana'
                # Falta el campo 'geometry'
            }]
        }
        mock_google_response.raise_for_status.return_value = None
        
        # Configurar side_effect
        def side_effect(url, *args, **kwargs):
            if 'nominatim.openstreetmap.org' in url:
                return mock_osm_response
            elif 'maps.googleapis.com' in url:
                return mock_google_response
            return Mock(json=Mock(return_value={}))
            
        mock_get.side_effect = side_effect
        
        with self.assertLogs('apps.core.services.geocoding', level='ERROR') as cm:
            result = GeocodingService.geocode_address('Calle Principal 123')
            self.assertIsNone(result)
            # Verificar que se registró el error esperado
            self.assertTrue(any('falta geometry/location' in log for log in cm.output))
    
    @override_settings(GOOGLE_MAPS_API_KEY='dummy-key')
    @patch('apps.core.services.geocoding.requests.get')
    def test_google_geocoding_invalid_status(self, mock_get):
        """Test manejo de estado inválido en respuesta de Google Maps"""
        # Mock para OSM (falla)
        mock_osm_response = Mock()
        mock_osm_response.json.return_value = []
        mock_osm_response.raise_for_status.return_value = None
        
        # Mock para Google (error de cuota)
        mock_google_response = Mock()
        mock_google_response.json.return_value = {
            'status': 'OVER_QUERY_LIMIT',
            'results': []
        }
        mock_google_response.raise_for_status.return_value = None
        
        # Configurar side_effect
        def side_effect(url, *args, **kwargs):
            if 'nominatim.openstreetmap.org' in url:
                return mock_osm_response
            elif 'maps.googleapis.com' in url:
                return mock_google_response
            return Mock(json=Mock(return_value={}))
            
        mock_get.side_effect = side_effect
        
        with self.assertLogs('apps.core.services.geocoding', level='ERROR') as cm:
            result = GeocodingService.geocode_address('Calle Principal 123')
            self.assertIsNone(result)
            # Verificar que se registró el error de la API
            self.assertTrue(any('Google Maps API error' in log for log in cm.output))
