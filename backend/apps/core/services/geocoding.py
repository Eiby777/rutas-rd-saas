import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class GeocodingService:
    """Servicio para convertir direcciones en coordenadas"""
    
    @staticmethod
    def geocode_address(address, city="Santo Domingo", country="República Dominicana"):
        """
        Geocodifica una dirección usando OpenStreetMap Nominatim
        Fallback a Google Maps si está configurado
        """
        full_address = f"{address}, {city}, {country}"
        
        # Intentar con OpenStreetMap primero (gratis)
        try:
            osm_result = GeocodingService._geocode_osm(full_address)
            if osm_result:
                return osm_result
        except Exception as e:
            logger.warning(f"OSM geocoding failed: {e}")
        
        # Fallback a Google Maps
        if settings.GOOGLE_MAPS_API_KEY:
            try:
                return GeocodingService._geocode_google(full_address)
            except Exception as e:
                logger.error(f"Google geocoding failed: {e}")
        
        return None
    
    @staticmethod
    def _geocode_osm(address):
        """Geocodificación con OpenStreetMap Nominatim"""
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'do',  # República Dominicana
        }
        headers = {
            'User-Agent': 'RutasRD-SaaS/1.0 (contacto@rutasrd.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        if results:
            result = results[0]
            return {
                'latitude': float(result['lat']),
                'longitude': float(result['lon']),
                'formatted_address': result['display_name'],
                'source': 'osm'
            }
        return None
    
    @staticmethod
    def _geocode_google(address):
        """Geocodificación con Google Maps API"""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': settings.GOOGLE_MAPS_API_KEY,
            'region': 'do'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            location = result['geometry']['location']
            return {
                'latitude': location['lat'],
                'longitude': location['lng'],
                'formatted_address': result['formatted_address'],
                'source': 'google'
            }
        return None

class DistanceMatrixService:
    """Servicio para calcular distancias entre múltiples puntos"""
    
    @staticmethod
    def get_distance_matrix(origins, destinations):
        """
        Obtiene matriz de distancias usando OSRM (gratis) o Google Maps
        origins/destinations: lista de dicts con 'latitude' y 'longitude'
        """
        try:
            return DistanceMatrixService._get_osrm_matrix(origins, destinations)
        except Exception as e:
            logger.warning(f"OSRM matrix failed: {e}")
            
        if settings.GOOGLE_MAPS_API_KEY:
            try:
                return DistanceMatrixService._get_google_matrix(origins, destinations)
            except Exception as e:
                logger.error(f"Google matrix failed: {e}")
        
        return None
    
    @staticmethod
    def _get_osrm_matrix(origins, destinations):
        """Matriz de distancias con OSRM"""
        # Combinar todos los puntos únicos
        all_points = []
        points_set = set()
        
        for point in origins + destinations:
            coord_key = (point['longitude'], point['latitude'])
            if coord_key not in points_set:
                all_points.append(coord_key)
                points_set.add(coord_key)
        
        # Construir URL para OSRM
        coordinates = ';'.join([f"{lng},{lat}" for lng, lat in all_points])
        url = f"http://router.project-osrm.org/table/v1/driving/{coordinates}"
        params = {
            'sources': ';'.join([str(i) for i in range(len(origins))]),
            'destinations': ';'.join([str(i) for i in range(len(origins), len(all_points))])
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if data['code'] == 'Ok':
            return {
                'distances': data['distances'],  # en metros
                'durations': data['durations'],  # en segundos
                'source': 'osrm'
            }
        return None
    
    @staticmethod
    def _get_google_matrix(origins, destinations):
        """Matriz de distancias con Google Maps API"""
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        origins_str = '|'.join([f"{o['latitude']},{o['longitude']}" for o in origins])
        destinations_str = '|'.join([f"{d['latitude']},{d['longitude']}" for d in destinations])
        
        params = {
            'origins': origins_str,
            'destinations': destinations_str,
            'key': settings.GOOGLE_MAPS_API_KEY,
            'mode': 'driving',
            'region': 'do'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if data['status'] == 'OK':
            # Procesar la respuesta
            distances = []
            durations = []
            
            for row in data['rows']:
                row_distances = []
                row_durations = []
                for element in row['elements']:
                    if element['status'] == 'OK':
                        row_distances.append(element['distance']['value'])  # en metros
                        row_durations.append(element['duration']['value'])  # en segundos
                    else:
                        row_distances.append(float('inf'))
                        row_durations.append(float('inf'))
                
                distances.append(row_distances)
                durations.append(row_durations)
            
            return {
                'distances': distances,
                'durations': durations,
                'source': 'google'
            }
        return None
