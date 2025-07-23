¡Perfecto! Felicidades por completar las primeras **2 semanas** del roadmap del SaaS de Optimización de Rutas RD. Has sentado unas **bases sólidas** con una arquitectura bien estructurada, modelos robustos, integración de APIs clave (mapas, OR-Tools), testing y automatización con Docker.

Ahora, continuamos con el **Plan Detallado de las Semanas 3-4**, tal como se menciona en el roadmap original, pero con el mismo nivel de profundidad técnico, enfoque en el mercado dominicano y preparación para un MVP funcional y escalable.

---

# ✅ **Plan Detallado Semanas 3-4: Frontend + Integración API + MVP Funcional**
**Objetivo**: Construir el **frontend web** (React) y conectarlo con el backend Django REST Framework, permitiendo al usuario crear lotes de entregas, visualizar rutas optimizadas y comenzar a usar el sistema de forma interactiva.

---

## 🗓️ **SEMANA 3: Frontend Web + Integración API**

### **Día 15: Setup del Frontend con React y Tailwind CSS**

#### ✅ Objetivo
Configurar el entorno de frontend con React 18, Vite (para mejor rendimiento), Tailwind CSS y estructura modular.

#### 📁 Estructura de Carpetas
```bash
cd frontend
npm create vite@latest . -- --template react
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

#### Configuración de Tailwind
```js
// tailwind.config.js
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: '#004aad', // Azul corporativo (inspirado en bandera RD)
        secondary: '#d9534f',
        success: '#5cb85c',
      },
    },
  },
  plugins: [],
}
```

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

#### Instalar dependencias clave
```bash
npm install axios react-router-dom @headlessui/react @heroicons/react
```

---

### **Día 16-17: Diseño de Componentes Clave**

#### 🎯 Componentes principales a desarrollar:

| Componente | Funcionalidad |
|----------|---------------|
| `Auth/Login.js` | Formulario de login con email/contraseña |
| `Layout/DashboardLayout.js` | Sidebar + navbar con menú de navegación |
| `Deliveries/BatchList.js` | Lista de lotes de entregas con estado |
| `Deliveries/BatchForm.js` | Formulario para crear/editar lote |
| `Deliveries/DeliveryForm.js` | Sub-formulario de entregas (dirección, cliente, ventana horaria) |
| `UI/MapPreview.js` | Contenedor para Leaflet/OpenStreetMap |
| `UI/LoadingSpinner.js`, `Alert.js` | UX reutilizable |

#### Ejemplo: `BatchForm.js`
```jsx
// frontend/src/components/Deliveries/BatchForm.js
import React, { useState } from 'react';
import axios from 'axios';

export default function BatchForm({ onSuccess }) {
  const [name, setName] = useState('');
  const [deliveryDate, setDeliveryDate] = useState('');
  const [depotAddress, setDepotAddress] = useState('');
  const [deliveries, setDeliveries] = useState([{ address: '', phone: '' }]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('/api/delivery-batches/', {
        name,
        delivery_date: deliveryDate,
        depot_address: depotAddress,
        deliveries: deliveries.map(d => ({
          address: d.address,
          phone: d.phone
        }))
      });
      onSuccess(response.data);
    } catch (error) {
      console.error('Error creando lote:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded shadow">
      <h2 className="text-xl font-bold mb-4">Nuevo Lote de Entregas</h2>
      <input
        type="text"
        placeholder="Nombre del lote"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="border p-2 w-full mb-3"
        required
      />
      <input
        type="date"
        value={deliveryDate}
        onChange={(e) => setDeliveryDate(e.target.value)}
        className="border p-2 w-full mb-3"
        required
      />
      <textarea
        placeholder="Dirección del almacén"
        value={depotAddress}
        onChange={(e) => setDepotAddress(e.target.value)}
        className="border p-2 w-full mb-3"
        required
      />

      <h3 className="font-semibold mt-4">Entregas</h3>
      {deliveries.map((d, i) => (
        <div key={i} className="flex gap-2 mb-2">
          <input
            type="text"
            placeholder="Dirección"
            value={d.address}
            onChange={(e) => {
              const newDeliveries = [...deliveries];
              newDeliveries[i].address = e.target.value;
              setDeliveries(newDeliveries);
            }}
            className="border p-2 flex-1"
          />
          <input
            type="text"
            placeholder="Teléfono"
            value={d.phone}
            onChange={(e) => {
              const newDeliveries = [...deliveries];
              newDeliveries[i].phone = e.target.value;
              setDeliveries(newDeliveries);
            }}
            className="border p-2 w-40"
          />
        </div>
      ))}

      <button
        type="button"
        onClick={() => setDeliveries([...deliveries, { address: '', phone: '' }])}
        className="text-sm bg-gray-200 px-3 py-1 rounded mb-3"
      >
        + Añadir entrega
      </button>

      <button
        type="submit"
        className="bg-primary text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Crear Lote
      </button>
    </form>
  );
}
```

---

### **Día 18-19: Integración con API Django REST Framework**

#### ✅ Configurar Axios y Endpoints

```js
// frontend/src/api/client.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para tokens
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export default api;
```

#### 🔗 Endpoints clave del backend (ya implementados en DRF)
```txt
GET    /api/delivery-batches/         → Listar lotes
POST   /api/delivery-batches/         → Crear lote + entregas
GET    /api/delivery-batches/{id}/    → Detalle con rutas
POST   /api/batches/{id}/optimize/    → Optimizar rutas (Celery async)
GET    /api/routes/?batch_id=...      → Rutas optimizadas
```

#### 💡 Vista: `BatchDetailView.js`
- Muestra entregas del lote.
- Botón "Optimizar rutas" que llama al endpoint `/optimize/`.
- Muestra estado: `draft`, `optimizing`, `ready`.

---

### **Día 20: Mapa Interactivo con Leaflet**

#### ✅ Instalar Leaflet
```bash
npm install leaflet react-leaflet
```

#### 🗺️ Componente `InteractiveMap.js`
```jsx
// frontend/src/components/UI/InteractiveMap.js
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix: Iconos en React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

export default function InteractiveMap({ deliveries = [], routeGeometry = null }) {
  const depot = deliveries[0]?.coordinates || [18.4861, -69.9312];

  return (
    <MapContainer center={depot} zoom={13} className="h-96 w-full rounded">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />
      {deliveries.map((d, i) => (
        <Marker key={i} position={[d.coordinates.lat, d.coordinates.lng]}>
          <Popup>
            {d.customer?.name} - {d.address}
          </Popup>
        </Marker>
      ))}
      {routeGeometry && (
        <Polyline
          positions={routeGeometry}
          color="blue"
          weight={5}
        />
      )}
    </MapContainer>
  );
}
```

---

## 🗓️ **SEMANA 4: Optimización Automatizada + MVP Funcional**

### **Día 21-22: Endpoint de Optimización Asíncrona (Celery + DRF)**

#### ✅ Nueva vista en Django: `OptimizeBatchView`

```python
# backend/apps/optimization/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.core.models import DeliveryBatch
from .tasks import optimize_batch_task

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def optimize_batch(request, batch_id):
    try:
        batch = DeliveryBatch.objects.get(id=batch_id, owner=request.user)
        if batch.status != 'draft':
            return Response({'error': 'Solo lotes en borrador pueden optimizarse'}, status=400)

        # Lanzar tarea Celery
        task = optimize_batch_task.delay(str(batch.id))
        return Response({
            'status': 'optimizing',
            'task_id': task.id,
            'message': 'La optimización está en progreso...'
        })
    except DeliveryBatch.DoesNotExist:
        return Response({'error': 'Lote no encontrado'}, status=404)
```

#### 📦 Tarea Celery: `optimize_batch_task`

```python
# backend/apps/optimization/tasks.py
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
```

---

### **Día 23: Polling del Estado de Optimización (Frontend)**

#### 🔄 Hook personalizado: `useOptimizationStatus.js`

```js
// frontend/src/hooks/useOptimizationStatus.js
import { useEffect, useState } from 'react';
import api from '../api/client';

export function useOptimizationStatus(batchId, interval = 3000) {
  const [status, setStatus] = useState('optimizing');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const poll = async () => {
      try {
        const response = await api.get(`/api/delivery-batches/${batchId}/`);
        setStatus(response.data.status);
        if (['ready', 'failed'].includes(response.data.status)) {
          setLoading(false);
        }
      } catch (err) {
        setLoading(false);
      }
    };

    const id = setInterval(poll, interval);
    return () => clearInterval(id);
  }, [batchId]);

  return { status, loading };
}
```

---

### **Día 24: Visualización de Rutas Optimizadas**

- Mostrar cada ruta con:
  - Vehículo y conductor asignado.
  - Secuencia de paradas.
  - Distancia y duración estimada.
  - Mapa con trazado de la ruta.
- Botón "Iniciar ruta" → cambia estado a `in_progress`.

---

### **Día 25: Panel de Administrador MVP**

#### 📊 Dashboard básico (`Dashboard.js`)
```jsx
// Mostrar:
- Total entregas hoy
- Rutas optimizadas vs. manuales (simulación)
- Tiempo estimado ahorrado
- Mapa con todas las rutas activas
```

---

### **Día 26-27: Pruebas de Integración y MVP**

#### ✅ Checklist de MVP funcional
| Funcionalidad | Estado |
|--------------|--------|
| Login y autenticación | ✅ |
| Crear lote de entregas | ✅ |
| Geocodificación automática | ✅ |
| Optimizar rutas (OR-Tools) | ✅ |
| Visualizar rutas en mapa | ✅ |
| Exportar a CSV | ✅ (usar `json2csv`) |
| Notificaciones básicas (SMS) | ⚠️ (próxima semana) |

#### 🧪 Prueba con datos reales
- Usar el comando `create_sample_data`.
- Optimizar lote de 15 entregas en Santo Domingo.
- Verificar tiempos y distancias realistas.

---

### **Día 28: Documentación y Entrega Semanal**

#### 📄 Documentar en `/docs/`
- `api/usage.md`: Cómo usar los endpoints.
- `user-guide/admin.md`: Guía rápida para el dueño del negocio.
- `deployment/local.md`: Cómo levantar todo con Docker.

#### 🚀 Comandos clave
```bash
# Levantar todo
docker-compose up --build

# Correr pruebas
./scripts/run_tests.sh

# Crear datos de prueba
python backend/manage.py create_sample_data
```

---

## ✅ **Entregables Semanas 3-4**

Al finalizar:
- ✅ **Frontend web funcional** (React + Tailwind)
- ✅ **API REST completa** con autenticación y optimización asíncrona
- ✅ **Integración de mapa interactivo** (Leaflet)
- ✅ **MVP operativo**: crear lote → optimizar → ver rutas
- ✅ **Tareas en segundo plano** (Celery + Redis)
- ✅ **Documentación básica** y scripts de prueba

---

## 🎯 **Estado del MVP**
- **Backend API**: 100% completo
- **Frontend**: 90% funcional
- **Optimización**: Automatizada y visualizada
- **Testing**: Pruebas de integración básicas
- **Deploy**: Listo para despliegue en DigitalOcean

---

¿Quieres que continúe ahora con las **Semanas 5-6** (App móvil PWA + Notificaciones SMS/WhatsApp), o prefieres profundizar en **seguridad, despliegue en producción o escalabilidad** antes de avanzar?
