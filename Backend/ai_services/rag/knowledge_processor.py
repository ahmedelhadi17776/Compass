import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from Backend.ai_services.rag.rag_service import RAGService

logger = logging.getLogger(__name__)


class KnowledgeProcessor:
    """Processes knowledge base documents and adds them to ChromaDB"""

    def __init__(self, rag_service: Optional[RAGService] = None):
        self.rag_service = rag_service or RAGService()

    async def process_knowledge_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Process all PDF files in the knowledge base directory

        Args:
            directory_path: Path to the knowledge base directory

        Returns:
            Dict with processing results
        """
        results = {
            "processed": 0,
            "failed": 0,
            "files": []
        }

        try:
            directory = Path(directory_path)
            if not directory.exists() or not directory.is_dir():
                logger.error(f"Directory not found: {directory_path}")
                return results

            # Process all PDF files
            for file_path in directory.glob("**/*.pdf"):
                logger.info(f"Processing PDF: {file_path}")

                # Extract domain from filename
                filename = file_path.name.lower()
                if "habit" in filename:
                    domain = "habits"
                elif "todo" in filename:
                    domain = "todos"
                elif "task" in filename:
                    domain = "tasks"
                elif "ai" in filename:
                    domain = "ai"
                elif "user" in filename:
                    domain = "users"
                else:
                    domain = "default"

                # Create metadata
                metadata = {
                    "domain": domain,
                    "filename": file_path.name,
                    "date_added": file_path.stat().st_mtime,
                    "file_size": file_path.stat().st_size,
                    "content_type": "pdf"
                }

                # Process the PDF
                success = await self.rag_service.add_pdf_to_knowledge_base(
                    pdf_path=str(file_path),
                    metadata=metadata
                )

                # Update results
                file_result = {
                    "filename": file_path.name,
                    "domain": domain,
                    "success": success
                }

                results["files"].append(file_result)
                if success:
                    results["processed"] += 1
                else:
                    results["failed"] += 1

            logger.info(
                f"Knowledge base processing complete: {results['processed']} processed, {results['failed']} failed")
            return results

        except Exception as e:
            logger.error(f"Error processing knowledge base: {str(e)}")
            return results


async def process_knowledge_base(kb_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Utility function to process the knowledge base

    Args:
        kb_dir: Optional path to knowledge base directory

    Returns:
        Processing results
    """
    if not kb_dir:
        # Use default path from project
        kb_dir = os.path.join(
            os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))),
            "ai_services", "rag", "knowledge_base"
        )

    processor = KnowledgeProcessor()
    return await processor.process_knowledge_directory(kb_dir)

if __name__ == "__main__":
    # When run directly, process the knowledge base
    import asyncio
    results = asyncio.run(process_knowledge_base())
    print(
        f"Processed {results['processed']} files, {results['failed']} failed")
