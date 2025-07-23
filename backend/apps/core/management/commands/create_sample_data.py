"""
Management command to create sample data for development and testing.
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import (
    Vehicle, Driver, Customer, DeliveryBatch, Delivery, Route
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=1,
            help='Number of users to create (default: 1)'
        )
        parser.add_argument(
            '--vehicles',
            type=int,
            default=3,
            help='Number of vehicles per user (default: 3)'
        )
        parser.add_argument(
            '--drivers',
            type=int,
            default=3,
            help='Number of drivers per user (default: 3)'
        )
        parser.add_argument(
            '--customers',
            type=int,
            default=10,
            help='Number of customers per user (default: 10)'
        )
        parser.add_argument(
            '--batches',
            type=int,
            default=2,
            help='Number of delivery batches per user (default: 2)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        # Create users
        for user_num in range(1, options['users'] + 1):
            user, created = User.objects.get_or_create(
                username=f'user{user_num}',
                defaults={
                    'email': f'user{user_num}@example.com',
                    'business_name': f'Empresa {user_num}',
                    'phone': f'809{random.randint(1000000, 9999999)}',
                    'subscription_plan': 'pro' if user_num % 2 == 0 else 'basic',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))
            
            # Create vehicles for this user
            vehicles = []
            for i in range(options['vehicles']):
                vehicle = Vehicle.objects.create(
                    owner=user,
                    name=f'Vehículo {i+1}',
                    license_plate=f'ABC{random.randint(100, 999)}',
                    vehicle_type=random.choice(['motorcycle', 'car', 'van', 'truck']),
                    capacity_weight=random.uniform(100, 1000),
                    capacity_volume=random.uniform(5, 50),
                    max_stops=random.randint(10, 50)
                )
                vehicles.append(vehicle)
                self.stdout.write(self.style.SUCCESS(f'Created vehicle: {vehicle.name}'))
            
            # Create drivers for this user
            drivers = []
            for i in range(options['drivers']):
                driver = Driver.objects.create(
                    owner=user,
                    name=f'Conductor {i+1}',
                    phone=f'809{random.randint(1000000, 9999999)}',
                    email=f'driver{i+1}@empresa{user_num}.com',
                    license_number=f'LIC{random.randint(10000, 99999)}',
                    default_vehicle=random.choice(vehicles) if vehicles else None,
                    is_active=random.choice([True, True, True, False])  # 75% chance of being active
                )
                drivers.append(driver)
                self.stdout.write(self.style.SUCCESS(f'Created driver: {driver.name}'))
            
            # Create customers for this user
            customers = []
            for i in range(options['customers']):
                customer = Customer.objects.create(
                    owner=user,
                    name=f'Cliente {i+1}',
                    phone=f'809{random.randint(1000000, 9999999)}',
                    email=f'cliente{i+1}@ejemplo.com',
                    default_address=f'Calle {random.randint(1, 100)} # {random.randint(1, 50)}, Santo Domingo',
                    default_coordinates={
                        'lat': 18.4 + random.uniform(-0.2, 0.2),
                        'lng': -69.9 + random.uniform(-0.2, 0.2)
                    }
                )
                customers.append(customer)
            self.stdout.write(self.style.SUCCESS(f'Created {len(customers)} customers'))
            
            # Create delivery batches with deliveries
            for batch_num in range(options['batches']):
                delivery_date = datetime.now().date() + timedelta(days=batch_num)
                batch = DeliveryBatch.objects.create(
                    owner=user,
                    name=f'Entregas {delivery_date.strftime("%d/%m/%Y")}',
                    delivery_date=delivery_date,
                    depot_address='Almacén Principal, Santo Domingo',
                    depot_coordinates={'lat': 18.4861, 'lng': -69.9312},
                    status='draft'
                )
                
                # Create deliveries for this batch
                batch_customers = random.sample(customers, min(15, len(customers)))
                for i, customer in enumerate(batch_customers):
                    Delivery.objects.create(
                        batch=batch,
                        customer=customer,
                        address=customer.default_address,
                        coordinates=customer.default_coordinates,
                        phone=customer.phone,
                        reference_number=f'PED-{batch.id[:6].upper()}-{i+1:03d}',
                        description=f'Paquete {i+1} para {customer.name}',
                        weight=random.uniform(0.5, 20),
                        status='pending',
                        earliest_time=datetime.strptime('08:00', '%H:%M').time(),
                        latest_time=datetime.strptime('17:00', '%H:%M').time()
                    )
                
                batch.total_stops = len(batch_customers)
                batch.save()
                self.stdout.write(self.style.SUCCESS(f'Created delivery batch: {batch.name} with {batch.total_stops} deliveries'))
        
        self.stdout.write(self.style.SUCCESS('Sample data creation complete!'))
