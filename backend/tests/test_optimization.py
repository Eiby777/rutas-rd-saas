from django.test import TestCase
from apps.optimization.services.route_optimizer import RouteOptimizer, create_distance_matrix_from_coordinates

class RouteOptimizerTestCase(TestCase):
    
    def setUp(self):
        # Coordenadas de prueba (Santo Domingo)
        self.coordinates = [
            (18.4861, -69.9312),  # Depot
            (18.4500, -69.9000),  # Cliente 1
            (18.5000, -69.8800),  # Cliente 2
            (18.4700, -69.9500),  # Cliente 3
        ]
        
        self.distance_matrix = create_distance_matrix_from_coordinates(self.coordinates)
        self.time_matrix = [[d // 50 for d in row] for row in self.distance_matrix]  # ~50m/min
    
    def test_basic_optimization(self):
        """Test optimización básica con un vehículo"""
        optimizer = RouteOptimizer(self.distance_matrix, self.time_matrix)
        result = optimizer.optimize(num_vehicles=1)
        
        self.assertIsNotNone(result)
        self.assertIn('routes', result)
        self.assertIn('total_distance', result)
        self.assertEqual(len(result['routes']), 1)
    
    def test_multi_vehicle_optimization(self):
        """Test optimización con múltiples vehículos"""
        optimizer = RouteOptimizer(self.distance_matrix, self.time_matrix)
        result = optimizer.optimize(num_vehicles=2)
        
        self.assertIsNotNone(result)
        self.assertLessEqual(len(result['routes']), 2)
    
    def test_distance_matrix_creation(self):
        """Test creación de matriz de distancias"""
        matrix = create_distance_matrix_from_coordinates(self.coordinates)
        
        self.assertEqual(len(matrix), len(self.coordinates))
        self.assertEqual(len(matrix[0]), len(self.coordinates))
        self.assertEqual(matrix[0][0], 0)  # Distancia a sí mismo = 0
