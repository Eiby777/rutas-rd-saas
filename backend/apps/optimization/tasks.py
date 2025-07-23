from celery import shared_task
from apps.core.models import DeliveryBatch, Route, Stop
from .services.route_optimizer import RouteOptimizer, create_distance_matrix_from_coordinates

@shared_task
def optimize_batch_task(batch_id):
    try:
        batch = DeliveryBatch.objects.get(id=batch_id)
        batch.status = 'optimizing'
        batch.save()

        # Obtener coordenadas (depot + entregas)
        coordinates = [(batch.depot_coordinates['lat'], batch.depot_coordinates['lng'])]
        deliveries = list(batch.deliveries.all())
        for delivery in deliveries:
            if delivery.coordinates:
                coordinates.append((delivery.coordinates['lat'], delivery.coordinates['lng']))

        # Matrices
        distance_matrix = create_distance_matrix_from_coordinates(coordinates)
        time_matrix = [[d // 50 for d in row] for row in distance_matrix]

        # Optimizar (2 vehículos de prueba)
        optimizer = RouteOptimizer(distance_matrix, time_matrix)
        result = optimizer.optimize(num_vehicles=2)

        if result:
            # Guardar rutas y paradas
            for i, route_data in enumerate(result['routes']):
                vehicle = batch.owner.vehicles.first() or None
                driver = batch.owner.drivers.first() or None

                route = Route.objects.create(
                    batch=batch,
                    vehicle=vehicle,
                    driver=driver,
                    route_order=i+1,
                    total_distance_km=route_data['total_distance'] / 1000,
                    estimated_duration_minutes=route_data['total_time'] // 60,
                    status='planned'
                )

                for stop_idx in route_data['stops'][1:-1]:  # Sin depot inicial y final
                    delivery = deliveries[stop_idx - 1]  # Índice ajustado
                    Stop.objects.create(
                        route=route,
                        delivery=delivery,
                        stop_order=stop_idx
                    )

            batch.status = 'ready'
            batch.total_distance_km = result['total_distance'] / 1000
            batch.estimated_duration_minutes = result['total_time'] // 60
        else:
            batch.status = 'failed'

        batch.save()
        return True

    except Exception as e:
        batch.status = 'failed'
        batch.save()
        return False
