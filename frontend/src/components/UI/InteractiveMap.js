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
