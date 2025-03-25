import os
import asyncio
import click
import logging
from pathlib import Path

from Backend.ai_services.rag.knowledge_processor import process_knowledge_base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def rag():
    """RAG service command group"""
    pass


@rag.command()
@click.option('--dir', '-d', help='Path to knowledge base directory')
@click.option('--force', '-f', is_flag=True, help='Force reprocessing of all files')
@click.option('--domain', help='Process only files for a specific domain')
def process_kb(dir=None, force=False, domain=None):
    """Process knowledge base PDF files into ChromaDB"""
    click.echo(f"Processing knowledge base{'(forced)' if force else ''}...")

    # Process knowledge base
    results = asyncio.run(process_knowledge_base(dir))

    # Display results
    click.echo(f"Processing complete:")
    click.echo(f"  - Files processed: {results['processed']}")
    click.echo(f"  - Files failed: {results['failed']}")

    # Display files
    if results['files']:
        click.echo("\nProcessed files:")
        for file in results['files']:
            status = "✅" if file['success'] else "❌"
            click.echo(f"  {status} {file['filename']} ({file['domain']})")


@rag.command()
@click.option('--domain', '-d', required=True, help='Domain to query')
@click.argument('query')
def query(domain, query):
    """Query the RAG knowledge base"""
    from Backend.ai_services.rag.rag_service import RAGService

    click.echo(f"Querying {domain} knowledge base: '{query}'")

    # Run query
    async def run_query():
        rag_service = RAGService()
        results = await rag_service.query_knowledge_base(
            query=query,
            context={"domain": domain},
            filters={"domain": domain}
        )
        return results

    results = asyncio.run(run_query())

    # Display results
    click.echo("\nResults:")
    if results and 'answer' in results:
        click.echo(results['answer'])

        if 'sources' in results and results['sources']:
            click.echo("\nSources:")
            for source in results['sources']:
                if isinstance(source, dict):
                    filename = source.get('source_file', 'unknown')
                    page = source.get('page_number', '')
                    page_info = f" (page {page})" if page else ""
                    click.echo(f"  - {filename}{page_info}")
    else:
        click.echo("No results found")


if __name__ == '__main__':
    rag()
