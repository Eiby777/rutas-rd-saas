# Utility Scripts and Management Commands

This directory contains utility scripts and management commands for the Rutas RD SaaS application.

## Management Commands

### `create_sample_data`

Creates sample data for development and testing.

**Usage:**
```bash
python manage.py create_sample_data [options]
```

**Options:**
- `--users`: Number of users to create (default: 1)
- `--vehicles`: Number of vehicles per user (default: 3)
- `--drivers`: Number of drivers per user (default: 3)
- `--customers`: Number of customers per user (default: 10)
- `--batches`: Number of delivery batches per user (default: 2)

### `optimize_routes`

Optimizes delivery routes for pending batches.

**Usage:**
```bash
python manage.py optimize_routes [--batch-id BATCH_ID] [--force]
```

**Options:**
- `--batch-id`: Specific batch ID to optimize (if not provided, processes all pending batches)
- `--force`: Force re-optimization even if batch is not in draft status

### `export_import_data`

Exports and imports application data.

**Export Usage:**
```bash
python manage.py export_import_data export [--output FILE] [--user USERNAME] [--models MODEL1,MODEL2]
```

**Import Usage:**
```bash
python manage.py export_import_data import FILE [--user USERNAME] [--dry-run]
```

## Maintenance Scripts

The `maintenance.py` script provides several system maintenance tasks:

### Cleanup Old Data

```bash
python -m scripts.maintenance cleanup [--days DAYS] [--dry-run]
```

### Send Delivery Reminders

```bash
python -m scripts.maintenance reminders
```

### Create Database Backup

```bash
python -m scripts.maintenance backup [--output-dir DIRECTORY]
```

## Shell Script

The `run_maintenance.sh` script provides an easy way to run maintenance tasks:

```bash
# Run all maintenance tasks
./scripts/run_maintenance.sh all

# Run specific task
./scripts/run_maintenance.sh [cleanup|reminders|backup]
```

## Logs and Backups

- Logs are stored in the `logs/` directory
- Database backups are stored in the `backups/` directory
