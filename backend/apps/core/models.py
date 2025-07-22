from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    """Usuario del sistema - Dueño de negocio"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=15, blank=True)
    business_name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('basic', 'Basic'),
            ('pro', 'Pro')
        ],
        default='free'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_name or self.username


class Vehicle(models.Model):
    """Vehículos de la flota"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    name = models.CharField(max_length=100)  # Ej: "Moto 1", "Camión Norte"
    license_plate = models.CharField(max_length=20, blank=True)
    vehicle_type = models.CharField(
        max_length=20,
        choices=[
            ('motorcycle', 'Motocicleta'),
            ('car', 'Automóvil'),
            ('van', 'Van'),
            ('truck', 'Camión')
        ]
    )
    capacity_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # kg
    capacity_volume = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # m³
    max_stops = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.vehicle_type})"


class Driver(models.Model):
    """Conductores/Repartidores"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drivers')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    default_vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Customer(models.Model):
    """Clientes finales"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    default_address = models.TextField(blank=True)
    default_coordinates = models.JSONField(null=True, blank=True)  # {"lat": 18.4861, "lng": -69.9312}
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DeliveryBatch(models.Model):
    """Lote de entregas para un día específico"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_batches')
    name = models.CharField(max_length=200)  # Ej: "Entregas 20 Dic 2024"
    delivery_date = models.DateField()
    depot_address = models.TextField()  # Dirección del almacén/tienda
    depot_coordinates = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Borrador'),
            ('optimizing', 'Optimizando'),
            ('ready', 'Listo'),
            ('in_progress', 'En Progreso'),
            ('completed', 'Completado')
        ],
        default='draft'
    )
    total_stops = models.IntegerField(default=0)
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_duration_minutes = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Delivery(models.Model):
    """Entrega individual"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(DeliveryBatch, on_delete=models.CASCADE, related_name='deliveries')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    address = models.TextField()
    coordinates = models.JSONField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)  # Puede sobrescribir el teléfono del cliente

    # Detalles del paquete
    reference_number = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    special_instructions = models.TextField(blank=True)

    # Ventana de tiempo
    earliest_time = models.TimeField(null=True, blank=True)
    latest_time = models.TimeField(null=True, blank=True)

    # Estado y seguimiento
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('assigned', 'Asignado'),
            ('out_for_delivery', 'En Ruta'),
            ('delivered', 'Entregado'),
            ('failed', 'Falló'),
            ('returned', 'Devuelto')
        ],
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference_number} - {self.customer.name}"


class Route(models.Model):
    """Ruta optimizada para un vehículo específico"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(DeliveryBatch, on_delete=models.CASCADE, related_name='routes')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)

    route_order = models.IntegerField()  # Orden de la ruta (1, 2, 3...)
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_duration_minutes = models.IntegerField()

    # Geometría de la ruta (para mostrar en mapa)
    route_geometry = models.JSONField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('planned', 'Planificado'),
            ('started', 'Iniciado'),
            ('completed', 'Completado')
        ],
        default='planned'
    )

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ruta {self.route_order} - {self.vehicle.name}"


class Stop(models.Model):
    """Parada individual en una ruta"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    delivery = models.OneToOneField(Delivery, on_delete=models.CASCADE)

    stop_order = models.IntegerField()  # Orden en la ruta (1, 2, 3...)
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)
    actual_arrival_time = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)

    # Fotos de confirmación
    proof_photo = models.URLField(blank=True)
    signature_image = models.URLField(blank=True)

    # Notas del conductor
    driver_notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('arrived', 'Llegó'),
            ('delivered', 'Entregado'),
            ('failed', 'Falló')
        ],
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Parada {self.stop_order} - {self.delivery.customer.name}"


class LocationUpdate(models.Model):
    """Actualizaciones de ubicación en tiempo real"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='location_updates')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)

    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    accuracy = models.FloatField(null=True, blank=True)  # Precisión GPS en metros
    speed = models.FloatField(null=True, blank=True)  # km/h
    heading = models.FloatField(null=True, blank=True)  # grados

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ubicación {self.driver.name} - {self.timestamp}"


class NotificationLog(models.Model):
    """Registro de notificaciones enviadas"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='notifications')

    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('sms', 'SMS'),
            ('whatsapp', 'WhatsApp'),
            ('email', 'Email')
        ]
    )

    recipient = models.CharField(max_length=100)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('sent', 'Enviado'),
            ('delivered', 'Entregado'),
            ('failed', 'Falló')
        ]
    )

    external_id = models.CharField(max_length=100, blank=True)  # ID de Twilio/WhatsApp
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.notification_type.upper()} → {self.recipient} [{self.status}]"