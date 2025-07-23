"""
Management commands for exporting and importing application data.
"""
import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

User = get_user_model()

class Command(BaseCommand):
    help = 'Export and import application data'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='command', help='Sub-command help')
        
        # Export command
        export_parser = subparsers.add_parser('export', help='Export data to JSON file')
        export_parser.add_argument('--output', '-o', type=str, help='Output file path')
        export_parser.add_argument('--user', type=str, help='Username to export data for (default: all users)')
        export_parser.add_argument('--models', type=str, help='Comma-separated list of models to export')
        
        # Import command
        import_parser = subparsers.add_parser('import', help='Import data from JSON file')
        import_parser.add_argument('input_file', type=str, help='Input JSON file path')
        import_parser.add_argument('--user', type=str, help='Username to import data for')
        import_parser.add_argument('--dry-run', action='store_true', help='Simulate import without saving')
    
    def handle(self, *args, **options):
        command = options.get('command')
        
        if command == 'export':
            self.export_data(options)
        elif command == 'import':
            self.import_data(options)
        else:
            self.stdout.write(self.style.ERROR('Please specify a valid command: export or import'))
    
    def export_data(self, options):
        """Export data to a JSON file."""
        from apps.core.models import (
            Vehicle, Driver, Customer, DeliveryBatch, Delivery, Route, LocationUpdate
        )
        
        # Default models to export
        model_map = {
            'vehicle': Vehicle,
            'driver': Driver,
            'customer': Customer,
            'deliverybatch': DeliveryBatch,
            'delivery': Delivery,
            'route': Route,
            'locationupdate': LocationUpdate,
        }
        
        # Filter models if specified
        if options.get('models'):
            selected_models = {m.strip().lower() for m in options['models'].split(',')}
            model_map = {k: v for k, v in model_map.items() if k in selected_models}
        
        # Get user filter
        user = None
        if options.get('user'):
            try:
                user = User.objects.get(username=options['user'])
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User not found: {options["user"]}'))
                return
        
        # Prepare output file path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = options.get('output') or f'rutas_rd_export_{timestamp}.json'
        
        # Collect data
        data = {'meta': {'exported_at': datetime.now().isoformat(), 'version': '1.0'}}
        
        with transaction.atomic():
            for model_name, model in model_map.items():
                queryset = model.objects.all()
                
                # Filter by user if specified and model has owner field
                if user and hasattr(model, 'owner'):
                    queryset = queryset.filter(owner=user)
                
                # Serialize data
                serialized_data = serializers.serialize('python', queryset)
                data[model_name] = serialized_data
                
                self.stdout.write(
                    self.style.SUCCESS(f'Exported {len(serialized_data)} {model_name} records')
                )
        
        # Save to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully exported data to {output_file}')
            )
            return output_file
            
        except IOError as e:
            self.stdout.write(self.style.ERROR(f'Error writing to file: {str(e)}'))
    
    def import_data(self, options):
        """Import data from a JSON file."""
        from apps.core.models import (
            Vehicle, Driver, Customer, DeliveryBatch, Delivery, Route, LocationUpdate
        )
        
        input_file = options['input_file']
        dry_run = options.get('dry_run', False)
        target_user = options.get('user')
        
        if not os.path.exists(input_file):
            self.stdout.write(self.style.ERROR(f'File not found: {input_file}'))
            return
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.stdout.write(self.style.ERROR(f'Error reading file: {str(e)}'))
            return
        
        # Get or create user mapping
        user_map = {}
        if target_user:
            try:
                user = User.objects.get(username=target_user)
                user_map['default'] = user
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Target user not found: {target_user}'))
                return
        
        model_map = {
            'vehicle': Vehicle,
            'driver': Driver,
            'customer': Customer,
            'deliverybatch': DeliveryBatch,
            'delivery': Delivery,
            'route': Route,
            'locationupdate': LocationUpdate,
        }
        
        # Track created objects for relationship resolution
        created_objects = {}
        
        try:
            with transaction.atomic():
                # Process models in dependency order
                for model_name in ['user', 'vehicle', 'driver', 'customer', 'deliverybatch', 'route', 'delivery', 'locationupdate']:
                    if model_name not in data:
                        continue
                    
                    model_class = model_map.get(model_name)
                    if not model_class:
                        continue
                    
                    self.stdout.write(f'Processing {model_name}...')
                    
                    # Initialize storage for this model's objects
                    if model_name not in created_objects:
                        created_objects[model_name] = {}
                    
                    # Process each object
                    for obj_data in data[model_name]:
                        # Skip if we already processed this object
                        if obj_data['pk'] in created_objects[model_name]:
                            continue
                        
                        # Handle user mapping for ownership
                        if 'fields' in obj_data and 'owner' in obj_data['fields']:
                            if target_user:
                                # Replace owner with target user
                                obj_data['fields']['owner'] = user.id
                            elif obj_data['fields']['owner'] not in user_map:
                                # Create a mapping for this user
                                try:
                                    user = User.objects.get(pk=obj_data['fields']['owner'])
                                    user_map[obj_data['fields']['owner']] = user
                                except User.DoesNotExist:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'User {obj_data["fields"]["owner"]} not found, '
                                            'skipping related objects'
                                        )
                                    )
                                    continue
                        
                        # Create model instance
                        obj = model_class(**obj_data['fields'])
                        
                        if not dry_run:
                            try:
                                obj.save()
                                created_objects[model_name][obj_data['pk']] = obj
                                self.stdout.write(
                                    self.style.SUCCESS(f'  - Created {model_name} {obj.id}')
                                )
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(f'  - Error creating {model_name}: {str(e)}')
                                )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'  - Would create {model_name} {obj_data["pk"]}')
                            )
                
                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(self.style.SUCCESS('Dry run complete. No changes were made.'))
                else:
                    self.stdout.write(self.style.SUCCESS('Import completed successfully!'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during import: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            transaction.set_rollback(True)
            self.stdout.write(self.style.ERROR('Import failed. All changes have been rolled back.'))
