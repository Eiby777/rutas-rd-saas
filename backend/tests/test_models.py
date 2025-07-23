from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Vehicle, Driver, Customer, DeliveryBatch, Delivery
from decimal import Decimal
import uuid

User = get_user_model()

class CoreModelsTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@rutasrd.com',
            password='testpass123',
            business_name='Test Business'
        )
    
    def test_user_creation(self):
        """Test creación de usuario personalizado"""
        self.assertTrue(isinstance(self.user.id, uuid.UUID))
        self.assertEqual(self.user.business_name, 'Test Business')
        self.assertEqual(self.user.subscription_plan, 'free')
    
    def test_vehicle_creation(self):
        """Test creación de vehículo"""
        vehicle = Vehicle.objects.create(
            owner=self.user,
            name='Moto 1',
            license_plate='A123456',
            vehicle_type='motorcycle',
            capacity_weight=Decimal('100.00'),
            max_stops=25
        )
        
        self.assertEqual(vehicle.owner, self.user)
        self.assertEqual(vehicle.vehicle_type, 'motorcycle')
        self.assertTrue(vehicle.is_active)
    
    def test_driver_creation(self):
        """Test creación de conductor"""
        vehicle = Vehicle.objects.create(
            owner=self.user,
            name='Moto 1',
            vehicle_type='motorcycle'
        )
        
        driver = Driver.objects.create(
            owner=self.user,
            name='Juan Pérez',
            phone='8091234567',
            default_vehicle=vehicle
        )
        
        self.assertEqual(driver.name, 'Juan Pérez')
        self.assertEqual(driver.default_vehicle, vehicle)
        self.assertTrue(driver.is_active)
    
    def test_customer_creation(self):
        """Test creación de cliente"""
        customer = Customer.objects.create(
            owner=self.user,
            name='María González',
            phone='8097654321',
            default_address='Calle Principal #123, Santo Domingo',
            default_coordinates={'lat': 18.4861, 'lng': -69.9312}
        )
        
        self.assertEqual(customer.owner, self.user)
        self.assertIsInstance(customer.default_coordinates, dict)
    
    def test_delivery_batch_creation(self):
        """Test creación de lote de entregas"""
        from datetime import date
        
        batch = DeliveryBatch.objects.create(
            owner=self.user,
            name='Entregas Test',
            delivery_date=date.today(),
            depot_address='Almacén Principal, Santo Domingo',
            depot_coordinates={'lat': 18.4861, 'lng': -69.9312}
        )
        
        self.assertEqual(batch.status, 'draft')
        self.assertEqual(batch.total_stops, 0)
    
    def test_delivery_creation(self):
        """Test creación de entrega"""
        from datetime import date
        
        customer = Customer.objects.create(
            owner=self.user,
            name='Test Customer',
            phone='8091111111'
        )
        
        batch = DeliveryBatch.objects.create(
            owner=self.user,
            name='Test Batch',
            delivery_date=date.today(),
            depot_address='Test Depot'
        )
        
        delivery = Delivery.objects.create(
            batch=batch,
            customer=customer,
            address='Test Address 123',
            coordinates={'lat': 18.5000, 'lng': -69.9000},
            reference_number='DEL001',
            description='Test Package'
        )
        
        self.assertEqual(delivery.status, 'pending')
        self.assertEqual(delivery.batch, batch)
        self.assertEqual(delivery.customer, customer)
