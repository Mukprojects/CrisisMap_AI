#!/usr/bin/env python3
"""
CrisisMap AI Command Line Interface.

A professional CLI for managing the CrisisMap AI application with commands for
data management, server operations, and system maintenance.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import uvicorn
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Setup rich console
console = Console()

# Setup logging with rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


class CrisisMapCLI:
    """Main CLI class for CrisisMap AI."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment."""
        import os
        return {
            'mongodb_uri': os.getenv('MONGODB_URI'),
            'db_name': os.getenv('DB_NAME', 'crisismap'),
            'api_host': os.getenv('API_HOST', '0.0.0.0'),
            'api_port': int(os.getenv('API_PORT', 8000)),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        }
    
    def display_banner(self):
        """Display the application banner."""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║    ██████╗██████╗ ██╗███████╗██╗███████╗███╗   ███╗ █████╗    ║
║   ██╔════╝██╔══██╗██║██╔════╝██║██╔════╝████╗ ████║██╔══██╗   ║
║   ██║     ██████╔╝██║███████╗██║███████╗██╔████╔██║███████║   ║
║   ██║     ██╔══██╗██║╚════██║██║╚════██║██║╚██╔╝██║██╔══██║   ║
║   ╚██████╗██║  ██║██║███████║██║███████║██║ ╚═╝ ██║██║  ██║   ║
║    ╚═════╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝   ║
║                                                               ║
║              Advanced Crisis Intelligence Platform             ║
║                         Version 1.0.0                        ║
╚═══════════════════════════════════════════════════════════════╝
        """
        console.print(banner, style="bold blue")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool):
    """CrisisMap AI - Advanced Crisis Intelligence Platform."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    
    if not quiet:
        cli_instance = CrisisMapCLI()
        cli_instance.display_banner()
    
    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--workers', default=1, help='Number of worker processes')
@click.option('--log-level', default='info', help='Log level')
@click.pass_context
def serve(ctx: click.Context, host: str, port: int, reload: bool, workers: int, log_level: str):
    """Start the CrisisMap AI server."""
    if not ctx.obj['quiet']:
        console.print(Panel.fit(
            f"🚀 Starting CrisisMap AI Server\n"
            f"📍 Address: http://{host}:{port}\n"
            f"👥 Workers: {workers}\n"
            f"🔄 Reload: {'Enabled' if reload else 'Disabled'}",
            title="Server Configuration",
            border_style="green"
        ))
    
    try:
        uvicorn.run(
            "crisismap_ai.api.app:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level=log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        console.print("\n👋 Server stopped gracefully", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Server error: {e}", style="red")
        sys.exit(1)


@cli.group()
def database():
    """Database management commands."""
    pass


@database.command()
@click.option('--check-only', is_flag=True, help='Only check connection without setup')
@click.pass_context
def setup(ctx: click.Context, check_only: bool):
    """Setup database connection and create indexes."""
    from crisismap_ai.database.db_connection import get_db_connection
    from crisismap_ai.create_vector_index import main as create_index
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("🔗 Connecting to database...", total=None)
        
        try:
            db_conn = get_db_connection()
            db_conn.connect()
            
            if db_conn.is_connected():
                progress.update(task, description="✅ Database connected successfully!")
                
                if not check_only:
                    progress.update(task, description="📊 Creating vector search index...")
                    create_index()
                    progress.update(task, description="✅ Vector search index created!")
                
                console.print(Panel.fit(
                    "✅ Database setup completed successfully!",
                    title="Database Status",
                    border_style="green"
                ))
            else:
                raise Exception("Failed to establish database connection")
                
        except Exception as e:
            console.print(Panel.fit(
                f"❌ Database setup failed: {e}",
                title="Database Error",
                border_style="red"
            ))
            sys.exit(1)


@database.command()
@click.option('--collection', default='crisis_events', help='Collection to show stats for')
@click.pass_context
def stats(ctx: click.Context, collection: str):
    """Show database statistics."""
    from crisismap_ai.database.db_connection import get_db_connection
    
    try:
        db_conn = get_db_connection()
        db_conn.connect()
        
        if not db_conn.is_connected():
            raise Exception("Could not connect to database")
        
        # Get collection stats
        stats = db_conn.db.command("collStats", collection)
        
        table = Table(title=f"Database Statistics - {collection}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Document Count", f"{stats.get('count', 0):,}")
        table.add_row("Total Size", f"{stats.get('size', 0):,} bytes")
        table.add_row("Average Document Size", f"{stats.get('avgObjSize', 0):.2f} bytes")
        table.add_row("Storage Size", f"{stats.get('storageSize', 0):,} bytes")
        table.add_row("Indexes", f"{stats.get('nindexes', 0)}")
        table.add_row("Index Size", f"{stats.get('totalIndexSize', 0):,} bytes")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error getting database stats: {e}", style="red")
        sys.exit(1)


@cli.group()
def data():
    """Data management commands."""
    pass


@data.command()
@click.option('--dataset', type=click.Choice(['all', 'earthquake', 'tsunami', 'floods', 'volcano', 'who', 'emdat']), 
              default='all', help='Dataset to ingest')
@click.option('--limit', default=1000, help='Maximum number of records to process')
@click.option('--force', is_flag=True, help='Force re-ingestion of existing data')
@click.pass_context
def ingest(ctx: click.Context, dataset: str, limit: int, force: bool):
    """Ingest crisis data from various sources."""
    from crisismap_ai.main import main as run_ingestion
    
    console.print(Panel.fit(
        f"📥 Starting data ingestion\n"
        f"🗂️  Dataset: {dataset}\n"
        f"📊 Limit: {limit:,} records\n"
        f"🔄 Force: {'Yes' if force else 'No'}",
        title="Data Ingestion",
        border_style="blue"
    ))
    
    try:
        # Use the existing main function with appropriate arguments
        sys.argv = ['main.py', '--action', 'ingest', '--dataset', dataset, '--limit', str(limit)]
        if force:
            sys.argv.append('--force')
        
        run_ingestion()
        
        console.print("✅ Data ingestion completed successfully!", style="green")
        
    except Exception as e:
        console.print(f"❌ Data ingestion failed: {e}", style="red")
        sys.exit(1)


@data.command()
@click.option('--output', '-o', default='data_export.json', help='Output file path')
@click.option('--format', type=click.Choice(['json', 'csv']), default='json', help='Export format')
@click.option('--limit', default=None, help='Maximum number of records to export')
@click.pass_context
def export(ctx: click.Context, output: str, format: str, limit: Optional[int]):
    """Export crisis data to file."""
    from crisismap_ai.database.db_connection import get_db_connection
    import json
    import csv
    
    try:
        db_conn = get_db_connection()
        db_conn.connect()
        
        if not db_conn.is_connected():
            raise Exception("Could not connect to database")
        
        # Get data from database
        query = {}
        cursor = db_conn.collection.find(query)
        if limit:
            cursor = cursor.limit(limit)
        
        data = list(cursor)
        
        # Convert ObjectId to string for JSON serialization
        for doc in data:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task(f"📤 Exporting {len(data)} records...", total=None)
            
            if format == 'json':
                with open(output, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            elif format == 'csv':
                if data:
                    with open(output, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            
            progress.update(task, description=f"✅ Exported to {output}")
        
        console.print(f"✅ Successfully exported {len(data)} records to {output}", style="green")
        
    except Exception as e:
        console.print(f"❌ Export failed: {e}", style="red")
        sys.exit(1)


@cli.group()
def models():
    """AI/ML model management commands."""
    pass


@models.command()
@click.pass_context
def download(ctx: click.Context):
    """Download and cache required AI models."""
    from crisismap_ai.embedding.embedding_generator import get_embedding_generator
    from crisismap_ai.models.llm_response import get_llm_response_generator
    from crisismap_ai.models.summarization import get_summarizer
    
    models_to_download = [
        ("Embedding Model", get_embedding_generator),
        ("LLM Response Model", get_llm_response_generator),
        ("Summarization Model", get_summarizer),
    ]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        for model_name, model_func in models_to_download:
            task = progress.add_task(f"📥 Downloading {model_name}...", total=None)
            
            try:
                model_func()
                progress.update(task, description=f"✅ {model_name} ready")
            except Exception as e:
                progress.update(task, description=f"❌ {model_name} failed: {e}")
                console.print(f"❌ Failed to download {model_name}: {e}", style="red")
    
    console.print("✅ Model download process completed!", style="green")


@models.command()
@click.option('--query', required=True, help='Test query for the models')
@click.pass_context
def test(ctx: click.Context, query: str):
    """Test AI models with a sample query."""
    from crisismap_ai.embedding.embedding_generator import get_embedding_generator
    from crisismap_ai.models.llm_response import get_llm_response_generator
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Test embedding generation
            task1 = progress.add_task("🧮 Testing embedding generation...", total=None)
            embedding_gen = get_embedding_generator()
            embedding = embedding_gen.generate_embedding(query)
            progress.update(task1, description=f"✅ Embedding generated (dim: {len(embedding)})")
            
            # Test LLM response
            task2 = progress.add_task("🤖 Testing LLM response...", total=None)
            llm_gen = get_llm_response_generator()
            response = llm_gen.generate_response(query, [])
            progress.update(task2, description="✅ LLM response generated")
        
        console.print(Panel.fit(
            f"Query: {query}\n\n"
            f"Embedding Dimension: {len(embedding)}\n"
            f"LLM Response: {response.get('response', 'No response')[:100]}...",
            title="Model Test Results",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"❌ Model test failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.pass_context
def health(ctx: click.Context):
    """Check system health and status."""
    from crisismap_ai.database.db_connection import get_db_connection
    import requests
    
    health_checks = []
    
    # Database check
    try:
        db_conn = get_db_connection()
        db_conn.connect()
        db_status = "✅ Connected" if db_conn.is_connected() else "❌ Disconnected"
    except Exception as e:
        db_status = f"❌ Error: {e}"
    
    health_checks.append(("Database", db_status))
    
    # API check (if running)
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        api_status = f"✅ Running (Status: {response.status_code})"
    except Exception:
        api_status = "❌ Not running or unreachable"
    
    health_checks.append(("API Server", api_status))
    
    # Models check
    try:
        from crisismap_ai.embedding.embedding_generator import get_embedding_generator
        get_embedding_generator()
        models_status = "✅ Available"
    except Exception as e:
        models_status = f"❌ Error: {e}"
    
    health_checks.append(("AI Models", models_status))
    
    # Display results
    table = Table(title="System Health Check")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    
    for component, status in health_checks:
        table.add_row(component, status)
    
    console.print(table)


@cli.command()
@click.option('--component', type=click.Choice(['api', 'database', 'models', 'all']), 
              default='all', help='Component to show info for')
@click.pass_context
def info(ctx: click.Context, component: str):
    """Show system information."""
    import platform
    import sys
    from crisismap_ai import __version__ if hasattr(__import__('crisismap_ai'), '__version__') else "1.0.0"
    
    info_data = {
        'System': {
            'Platform': platform.system(),
            'Python Version': sys.version.split()[0],
            'CrisisMap AI Version': "1.0.0",
            'Architecture': platform.machine(),
        },
        'Configuration': {
            'MongoDB URI': ctx.obj.get('mongodb_uri', 'Not configured')[:50] + '...' if ctx.obj.get('mongodb_uri') else 'Not configured',
            'API Host': ctx.obj.get('api_host', 'Not configured'),
            'API Port': str(ctx.obj.get('api_port', 'Not configured')),
            'Debug Mode': str(ctx.obj.get('debug', False)),
        }
    }
    
    if component == 'all':
        for category, data in info_data.items():
            table = Table(title=category)
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data.items():
                table.add_row(key, str(value))
            
            console.print(table)
            console.print()
    else:
        # Show specific component info
        console.print(f"Component '{component}' info not implemented yet.", style="yellow")


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n👋 Operation cancelled by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}", style="red")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()