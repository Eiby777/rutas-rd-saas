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
