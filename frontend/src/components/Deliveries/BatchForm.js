import React, { useState } from 'react';
import api from '../../api/client';

export default function BatchForm({ onSuccess }) {
  const [name, setName] = useState('');
  const [deliveryDate, setDeliveryDate] = useState('');
  const [depotAddress, setDepotAddress] = useState('');
  const [deliveries, setDeliveries] = useState([{ address: '', phone: '' }]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/delivery-batches/', {
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
