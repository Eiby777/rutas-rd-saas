from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RouteOptimizer:
    """Optimizador de rutas usando Google OR-Tools"""
    
    def __init__(self, distance_matrix, time_matrix, depot_index=0):
        self.distance_matrix = distance_matrix
        self.time_matrix = time_matrix
        self.depot_index = depot_index
        self.num_locations = len(distance_matrix)
    
    def optimize(self, num_vehicles, vehicle_capacities=None, time_windows=None):
        """
        Optimiza rutas para múltiples vehículos
        
        Args:
            num_vehicles: Número de vehículos disponibles
            vehicle_capacities: Lista con capacidad de cada vehículo
            time_windows: Lista de tuplas (inicio, fin) para cada ubicación
        
        Returns:
            Dict con rutas optimizadas
        """
        try:
            # Crear el modelo de routing
            manager = pywrapcp.RoutingIndexManager(
                self.num_locations, 
                num_vehicles, 
                self.depot_index
            )
            routing = pywrapcp.RoutingModel(manager)
            
            # Callback de distancia
            def distance_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return self.distance_matrix[from_node][to_node]
            
            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
            
            # Agregar restricción de capacidad si se especifica
            if vehicle_capacities:
                self._add_capacity_constraints(routing, manager, vehicle_capacities)
            
            # Agregar ventanas de tiempo si se especifican
            if time_windows:
                self._add_time_constraints(routing, manager, time_windows)
            
            # Configurar parámetros de búsqueda
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.FromSeconds(30)  # 30 segundos máximo
            
            # Resolver
            solution = routing.SolveWithParameters(search_parameters)
            
            if solution:
                return self._extract_solution(manager, routing, solution)
            else:
                logger.error("No se encontró solución para la optimización")
                return None
                
        except Exception as e:
            logger.error(f"Error en optimización de rutas: {e}")
            return None
    
    def _add_capacity_constraints(self, routing, manager, capacities):
        """Añade restricciones de capacidad por vehículo"""
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            # Aquí deberías tener las demandas por ubicación
            # Por simplicidad, asumimos demanda = 1 por parada
            return 1 if from_node != 0 else 0
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            capacities,  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity'
        )
    
    def _add_time_constraints(self, routing, manager, time_windows):
        """Añade ventanas de tiempo"""
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return self.time_matrix[from_node][to_node]
        
        time_callback_index = routing.RegisterTransitCallback(time_callback)
        
        time_dimension_name = 'Time'
        routing.AddDimension(
            time_callback_index,
            30,  # allow waiting time
            1440,  # maximum time per vehicle (1440 minutos = 24 horas)
            False,  # don't force start cumul to zero
            time_dimension_name
        )
        
        time_dimension = routing.GetDimensionOrDie(time_dimension_name)
        
        # Agregar ventanas de tiempo para cada ubicación
        for location_idx, time_window in enumerate(time_windows):
            if time_window:
                start_time, end_time = time_window
                index = manager.NodeToIndex(location_idx)
                time_dimension.CumulVar(index).SetRange(start_time, end_time)
    
    def _extract_solution(self, manager, routing, solution):
        """Extrae la solución en formato útil"""
        routes = []
        total_distance = 0
        total_time = 0
        
        for vehicle_id in range(routing.vehicles()):
            index = routing.Start(vehicle_id)
            route = {
                'vehicle_id': vehicle_id,
                'stops': [],
                'total_distance': 0,
                'total_time': 0
            }
            
            route_distance = 0
            route_time = 0
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route['stops'].append(node_index)
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                
                if not routing.IsEnd(index):
                    from_node = manager.IndexToNode(previous_index)
                    to_node = manager.IndexToNode(index)
                    route_distance += self.distance_matrix[from_node][to_node]
                    route_time += self.time_matrix[from_node][to_node]
            
            # Agregar parada final (depot)
            final_node = manager.IndexToNode(index)
            route['stops'].append(final_node)
            
            route['total_distance'] = route_distance
            route['total_time'] = route_time
            total_distance += route_distance
            total_time += route_time
            
            # Solo agregar rutas que tienen paradas (excluyendo depot)
            if len(route['stops']) > 2:  # depot inicial + paradas + depot final
                routes.append(route)
        
        return {
            'routes': routes,
            'total_distance': total_distance,
            'total_time': total_time,
            'objective_value': solution.ObjectiveValue()
        }

# Función utilitaria para crear matriz de distancias euclidiana
def create_distance_matrix_from_coordinates(coordinates):
    """
    Crea matriz de distancias euclidiana a partir de coordenadas
    coordinates: lista de tuplas (lat, lng)
    """
    num_locations = len(coordinates)
    matrix = [[0 for _ in range(num_locations)] for _ in range(num_locations)]
    
    for i in range(num_locations):
        for j in range(num_locations):
            if i != j:
                distance = haversine_distance(
                    coordinates[i][0], coordinates[i][1],
                    coordinates[j][0], coordinates[j][1]
                )
                matrix[i][j] = int(distance * 1000)  # convertir a metros
    
    return matrix

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcula distancia haversine entre dos puntos en km"""
    R = 6371  # Radio de la Tierra en km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance
