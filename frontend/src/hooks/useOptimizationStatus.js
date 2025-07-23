import { useEffect, useState } from 'react';
import api from '../api/client';

export function useOptimizationStatus(batchId, interval = 3000) {
  const [status, setStatus] = useState('optimizing');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const poll = async () => {
      try {
        const response = await api.get(`/delivery-batches/${batchId}/`);
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
