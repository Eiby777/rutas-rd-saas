"""
Management command to optimize delivery routes for pending batches.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.models import DeliveryBatch, Route, Vehicle, Driver
from apps.optimization.services.route_optimizer import RouteOptimizer
from apps.optimization.services.distance_calculator import DistanceCalculator

class Command(BaseCommand):
    help = 'Optimize delivery routes for pending batches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-id',
            type=str,
            help='Specific batch ID to optimize (if not provided, processes all pending batches)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-optimization even if batch is not in draft status'
        )

    def handle(self, *args, **options):
        batch_id = options.get('batch_id')
        force = options.get('force', False)
        
        # Get batches to process
        if batch_id:
            batches = DeliveryBatch.objects.filter(id=batch_id)
            if not batches.exists():
                self.stdout.write(self.style.ERROR(f'No batch found with ID: {batch_id}'))
                return
        else:
            status_filter = ['draft'] if not force else ['draft', 'ready']
            batches = DeliveryBatch.objects.filter(status__in=status_filter)
            if not batches.exists():
                self.stdout.write(self.style.SUCCESS('No batches to optimize'))
                return
        
        for batch in batches:
            self.stdout.write(f'Optimizing batch: {batch.name} (ID: {batch.id})')
            
            # Get available vehicles for this user
            vehicles = Vehicle.objects.filter(owner=batch.owner, is_active=True)
            if not vehicles.exists():
                self.stdout.write(self.style.ERROR(f'No active vehicles found for user: {batch.owner}'))
                continue
            
            # Get available drivers for this user
            drivers = Driver.objects.filter(owner=batch.owner, is_active=True)
            if not drivers.exists():
                self.stdout.write(self.style.ERROR(f'No active drivers found for user: {batch.owner}'))
                continue
            
            # Get deliveries for this batch
            deliveries = batch.deliveries.all()
            if not deliveries.exists():
                self.stdout.write(self.style.WARNING(f'No deliveries found for batch: {batch.id}'))
                continue
            
            try:
                # Prepare locations (depot + delivery points)
                locations = [
                    (batch.depot_coordinates['lat'], batch.depot_coordinates['lng'])
                ]
                for delivery in deliveries:
                    if delivery.coordinates:
                        locations.append((delivery.coordinates['lat'], delivery.coordinates['lng']))
                
                # Calculate distance matrix
                distance_matrix = DistanceCalculator.get_distance_matrix(locations, locations)
                
                # Initialize and run optimizer
                optimizer = RouteOptimizer(distance_matrix)
                solution = optimizer.solve(
                    num_vehicles=min(len(vehicles), len(drivers)),
                    max_stops_per_vehicle=max(v.max_stops for v in vehicles)
                )
                
                if not solution['routes']:
                    self.stdout.write(self.style.ERROR('No valid routes could be generated'))
                    continue
                
                # Delete existing routes for this batch
                batch.routes.all().delete()
                
                # Create new routes
                total_distance = 0
                total_duration = 0
                
                for i, route_data in enumerate(solution['routes']):
                    if not route_data['stops']:
                        continue
                        
                    # Assign vehicle and driver (round-robin)
                    vehicle = vehicles[i % len(vehicles)]
                    driver = drivers[i % len(drivers)]
                    
                    # Create route
                    route = Route.objects.create(
                        batch=batch,
                        vehicle=vehicle,
                        driver=driver,
                        route_order=i + 1,
                        total_distance_km=route_data['distance'],
                        estimated_duration_minutes=route_data['duration'],
                        status='planned',
                        route_geometry={
                            'type': 'LineString',
                            'coordinates': route_data['geometry']
                        }
                    )
                    
                    # Update deliveries with route and stop order
                    for stop_order, delivery_idx in enumerate(route_data['stops'], 1):
                        if delivery_idx > 0:  # Skip depot (index 0)
                            try:
                                delivery = deliveries[delivery_idx - 1]
                                delivery.route = route
                                delivery.stop_order = stop_order
                                delivery.status = 'assigned'
                                delivery.save()
                            except IndexError:
                                continue
                    
                    total_distance += route_data['distance']
                    total_duration += route_data['duration']
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  - Route {i+1}: {len(route_data["stops"])-1} stops, '  
                            f'{route_data["distance"]:.1f} km, '  
                            f'{route_data["duration"]} min'
                        )
                    )
                
                # Update batch status
                batch.status = 'ready'
                batch.total_distance_km = total_distance
                batch.estimated_duration_minutes = total_duration
                batch.optimized_at = timezone.now()
                batch.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Optimization complete: {len(solution["routes"])} routes created, '  
                        f'Total distance: {total_distance:.1f} km, '  
                        f'Total duration: {total_duration} min'
                    )
                )
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error optimizing batch {batch.id}: {str(e)}'))
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))
                continue
