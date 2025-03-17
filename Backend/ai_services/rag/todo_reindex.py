#!/usr/bin/env python
"""
Reindex all Todos in the database to ChromaDB.

This script can be used to initialize or rebuild the ChromaDB index
for all Todo items in the database.

Usage:
    python todo_reindex.py [--user-id USER_ID] [--batch-size BATCH_SIZE] [--verbose]

Args:
    --user-id: Optional user ID to reindex only that user's Todos
    --batch-size: Number of Todos to process at once (default: 100)
    --verbose: Print detailed progress information
"""

import os
import sys
import argparse
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Backend.data_layer.database.connection import get_db
from Backend.core.config import settings
from Backend.data_layer.database.models.todo import Todo
from Backend.ai_services.rag.todo_ai_service import TodoAIService
from Backend.data_layer.repositories.todo_repository import TodoRepository
from sqlalchemy.future import select
from sqlalchemy import and_

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_all_todos(db: AsyncSession, user_id: Optional[int] = None, batch_size: int = 100) -> List[Todo]:
    """Get all todos from the database, optionally filtered by user ID."""
    try:
        # Create a base query
        query = select(Todo)
        if user_id is not None:
            query = query.where(Todo.user_id == user_id)
        
        # Execute the query and get results
        result = await db.execute(query)
        todos = result.scalars().all()
        
        logger.info(f"Found {len(todos)} todos to reindex")
        return todos
    except Exception as e:
        logger.error(f"Error getting todos: {str(e)}")
        return []

async def reindex_todos(
    todos: List[Todo], 
    batch_size: int = 100, 
    verbose: bool = False
) -> Dict[str, Any]:
    """Reindex todos in ChromaDB."""
    try:
        todo_ai_service = TodoAIService()
        
        total_todos = len(todos)
        success_count = 0
        error_count = 0
        start_time = datetime.now()
        
        # Process todos in batches
        for i in range(0, total_todos, batch_size):
            batch = todos[i:i + batch_size]
            batch_size = len(batch)
            batch_success = 0
            
            # Process each todo in the batch
            for todo in batch:
                try:
                    result = await todo_ai_service.index_todo(todo)
                    if result:
                        success_count += 1
                        batch_success += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    if verbose:
                        logger.error(f"Error indexing todo {todo.id}: {str(e)}")
            
            # Print batch progress
            if verbose or i + batch_size >= total_todos:
                logger.info(f"Batch {i//batch_size + 1}: Processed {batch_size} todos, {batch_success} successful")
        
        # Calculate stats
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        todos_per_second = total_todos / duration if duration > 0 else 0
        
        result = {
            "total_todos": total_todos,
            "success_count": success_count,
            "error_count": error_count,
            "duration_seconds": duration,
            "todos_per_second": todos_per_second
        }
        
        logger.info(f"Reindexing complete: {success_count} successful, {error_count} failed, {duration:.2f} seconds")
        return result
    except Exception as e:
        logger.error(f"Error reindexing todos: {str(e)}")
        return {
            "total_todos": len(todos),
            "success_count": 0,
            "error_count": len(todos),
            "duration_seconds": 0,
            "todos_per_second": 0,
            "error": str(e)
        }

async def main(user_id: Optional[int] = None, batch_size: int = 100, verbose: bool = False):
    """Main function to reindex all todos."""
    try:
        # Create a database engine and session
        db_url = settings.DATABASE_URL
        engine = create_async_engine(db_url)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        logger.info("Starting Todo reindexing process")
        logger.info(f"Using batch size: {batch_size}")
        if user_id:
            logger.info(f"Filtering by user ID: {user_id}")
        
        async with async_session() as session:
            # Get all todos
            todos = await get_all_todos(session, user_id, batch_size)
            
            if not todos:
                logger.info("No todos found to reindex")
                return
            
            # Reindex todos
            result = await reindex_todos(todos, batch_size, verbose)
            
            # Print summary
            logger.info("Reindexing summary:")
            logger.info(f"Total todos: {result['total_todos']}")
            logger.info(f"Successfully indexed: {result['success_count']}")
            logger.info(f"Failed to index: {result['error_count']}")
            logger.info(f"Duration: {result['duration_seconds']:.2f} seconds")
            logger.info(f"Speed: {result['todos_per_second']:.2f} todos/second")
    
    except Exception as e:
        logger.error(f"Error in reindexing process: {str(e)}")
    finally:
        # Close the database engine
        await engine.dispose()
        logger.info("Reindexing process complete")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Reindex all Todos in the database to ChromaDB")
    parser.add_argument("--user-id", type=int, help="User ID to reindex only that user's Todos")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of Todos to process at once")
    parser.add_argument("--verbose", action="store_true", help="Print detailed progress information")
    
    args = parser.parse_args()
    
    # Run the reindexing process
    asyncio.run(main(user_id=args.user_id, batch_size=args.batch_size, verbose=args.verbose)) 