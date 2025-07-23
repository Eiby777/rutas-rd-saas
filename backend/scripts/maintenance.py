import os
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management import call_command
from django.core.cache import cache
from django.utils import timezone
from apps.core.models import DeliveryBatch, Route, Delivery, LocationUpdate
from apps.notifications.services import NotificationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(settings.BASE_DIR, 'logs/maintenance.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MaintenanceService:
    """Service for performing system maintenance tasks."""
    
    @classmethod
    def cleanup_old_data(cls, days_to_keep=90, dry_run=False):
        """
        Clean up old data to keep the database size in check.
        
        Args:
            days_to_keep: Number of days of data to keep
            dry_run: If True, only show what would be deleted
            
        Returns:
            dict: Statistics about the cleanup operation
        """
        logger.info(f'Starting data cleanup (dry_run={dry_run})...')
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        stats = {
            'started_at': timezone.now(),
            'cutoff_date': cutoff_date,
            'deleted': {},
            'dry_run': dry_run
        }
        
        try:
            # Clean up old location updates (keep only 30 days by default)
            location_updates = LocationUpdate.objects.filter(
                timestamp__lt=timezone.now() - timedelta(days=30)
            )
            stats['location_updates'] = location_updates.count()
            
            if not dry_run:
                location_updates.delete()
            
            # Archive completed batches older than cutoff_date
            old_batches = DeliveryBatch.objects.filter(
                status='completed',
                updated_at__lt=cutoff_date
            )
            
            batch_ids = list(old_batches.values_list('id', flat=True))
            stats['batches'] = len(batch_ids)
            
            if not dry_run and batch_ids:
                # Delete related data in reverse order of dependencies
                LocationUpdate.objects.filter(route__batch_id__in=batch_ids).delete()
                Delivery.objects.filter(batch_id__in=batch_ids).delete()
                Route.objects.filter(batch_id__in=batch_ids).delete()
                old_batches.delete()
            
            # Clean up old cached data
            if not dry_run:
                cache.delete_pattern('route_*')
                cache.delete_pattern('batch_*')
                cache.delete_pattern('driver_*')
            
            stats['completed_at'] = timezone.now()
            logger.info(f'Cleanup completed: {stats}')
            return stats
            
        except Exception as e:
            logger.error(f'Error during cleanup: {str(e)}', exc_info=True)
            stats['error'] = str(e)
            return stats
    
    @classmethod
    def send_delivery_reminders(cls):
        """Send reminders for upcoming deliveries."""
        logger.info('Sending delivery reminders...')
        
        # Get batches starting in the next 24 hours
        now = timezone.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        batches = DeliveryBatch.objects.filter(
            delivery_date__gte=start.date(),
            delivery_date__lt=end.date(),
            status__in=['ready', 'in_progress']
        )
        
        stats = {
            'started_at': now,
            'batches_processed': 0,
            'notifications_sent': 0,
            'batches': []
        }
        
        notification_service = NotificationService()
        
        for batch in batches:
            batch_stats = {
                'batch_id': str(batch.id),
                'batch_name': batch.name,
                'notifications': []
            }
            
            # Get drivers with routes in this batch
            routes = Route.objects.filter(batch=batch).select_related('driver')
            
            for route in routes:
                if not route.driver or not route.driver.phone:
                    continue
                
                # Prepare notification
                try:
                    driver_name = route.driver.name.split()[0]  # First name only
                    message = (
                        f'Hola {driver_name}, recuerda que tienes una ruta programada para mañana. '
                        f'Total de paradas: {route.deliveries.count()}. ¡Buen viaje! 🚚'
                    )
                    
                    # Send notification
                    success = notification_service.send_sms(
                        to=route.driver.phone,
                        message=message,
                        context={'batch_id': str(batch.id), 'route_id': str(route.id)}
                    )
                    
                    notification = {
                        'driver': route.driver.name,
                        'phone': route.driver.phone,
                        'success': success,
                        'message': message[:50] + '...' if len(message) > 50 else message
                    }
                    
                    batch_stats['notifications'].append(notification)
                    
                    if success:
                        stats['notifications_sent'] += 1
                    
                except Exception as e:
                    logger.error(f'Error sending notification to {route.driver.phone}: {str(e)}')
                    notification = {
                        'driver': route.driver.name,
                        'phone': route.driver.phone,
                        'success': False,
                        'error': str(e)
                    }
                    batch_stats['notifications'].append(notification)
            
            stats['batches_processed'] += 1
            stats['batches'].append(batch_stats)
        
        stats['completed_at'] = timezone.now()
        logger.info(f'Delivery reminders completed: {stats}')
        return stats
    
    @classmethod
    def backup_database(cls, output_dir=None):
        """
        Create a database backup using Django's dumpdata command.
        
        Args:
            output_dir: Directory to save the backup file. Defaults to settings.BACKUP_DIR.
            
        Returns:
            str: Path to the created backup file
        """
        from django.conf import settings
        
        if not output_dir:
            output_dir = getattr(settings, 'BACKUP_DIR', os.path.join(settings.BASE_DIR, 'backups'))
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f'db_backup_{timestamp}.json')
        
        try:
            logger.info(f'Starting database backup to {output_file}')
            
            # Use Django's dumpdata command
            with open(output_file, 'w', encoding='utf-8') as f:
                call_command('dumpdata', format='json', indent=2, stdout=f)
            
            # Compress the backup
            import gzip
            compressed_file = f'{output_file}.gz'
            with open(output_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Remove uncompressed file
            os.remove(output_file)
            
            logger.info(f'Database backup completed: {compressed_file}')
            return compressed_file
            
        except Exception as e:
            logger.error(f'Error during database backup: {str(e)}', exc_info=True)
            # Clean up partial files
            if os.path.exists(output_file):
                os.remove(output_file)
            if 'compressed_file' in locals() and os.path.exists(compressed_file):
                os.remove(compressed_file)
            raise


def main():
    """Run maintenance tasks from the command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Rutas RD Maintenance Utilities')
    subparsers = parser.add_subparsers(dest='command', help='Maintenance command to run')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--days', type=int, default=90, help='Number of days of data to keep')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without making changes')
    
    # Reminders command
    reminders_parser = subparsers.add_parser('reminders', help='Send delivery reminders')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create a database backup')
    backup_parser.add_argument('--output-dir', help='Directory to save the backup file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'cleanup':
            result = MaintenanceService.cleanup_old_data(
                days_to_keep=args.days,
                dry_run=args.dry_run
            )
            print(f'Cleanup completed: {result}')
            
        elif args.command == 'reminders':
            result = MaintenanceService.send_delivery_reminders()
            print(f'Sent {result["notifications_sent"]} reminders for {result["batches_processed"]} batches')
            
        elif args.command == 'backup':
            backup_file = MaintenanceService.backup_database(
                output_dir=args.output_dir
            )
            print(f'Backup created: {backup_file}')
            
    except Exception as e:
        logger.error(f'Error in {args.command}: {str(e)}', exc_info=True)
        raise


if __name__ == '__main__':
    main()
