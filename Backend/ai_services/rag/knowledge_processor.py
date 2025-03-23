import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import PyPDF2
from concurrent.futures import ThreadPoolExecutor

from Backend.ai_services.rag.rag_service import RAGService

logger = logging.getLogger(__name__)


class KnowledgeProcessor:
    """Processes knowledge base documents and adds them to ChromaDB"""

    def __init__(self, rag_service: Optional[RAGService] = None):
        self.rag_service = rag_service or RAGService()
        self.max_workers = 4
        self.chunk_size = 5  # Number of pages to process in one batch
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

    async def _process_pdf_batch(
        self,
        file_path: Path,
        start_page: int,
        end_page: int,
        metadata: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Process a batch of PDF pages."""
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                content = []
                processed_pages = []

                # Process pages in the batch
                for page_num in range(start_page, min(end_page, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()

                    # Create page-specific metadata
                    page_metadata = metadata.copy()
                    page_metadata.update({
                        "page_number": page_num + 1,
                        "total_pages": len(pdf_reader.pages),
                        "source_file": file_path.name,
                        "content_type": "pdf_page",
                        "batch_processed": True
                    })

                    # Add to content list
                    content.append(page_text)
                    processed_pages.append(page_num + 1)

                    # Add to knowledge base in smaller chunks
                    if len(content) >= 5:  # Process in chunks of 5 pages
                        success = await self.rag_service.add_to_knowledge_base(
                            content=content,
                            metadata=[page_metadata for _ in content],
                            normalize=True
                        )
                        if not success:
                            logger.error(
                                f"Failed to process pages {processed_pages}")
                            return False, processed_pages
                        content = []

                # Process any remaining pages
                if content:
                    success = await self.rag_service.add_to_knowledge_base(
                        content=content,
                        metadata=[page_metadata for _ in content],
                        normalize=True
                    )
                    if not success:
                        logger.error(
                            f"Failed to process remaining pages {processed_pages}")
                        return False, processed_pages

                return True, processed_pages
        except Exception as e:
            logger.error(f"Error processing PDF batch: {str(e)}")
            return False, []

    async def process_knowledge_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Process all PDF files in the knowledge base directory with batch processing

        Args:
            directory_path: Path to the knowledge base directory

        Returns:
            Dict with processing results
        """
        results = {
            "processed": 0,
            "failed": 0,
            "files": [],
            "batches_processed": 0
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

                # Create base metadata
                metadata = {
                    "domain": domain,
                    "filename": file_path.name,
                    "date_added": file_path.stat().st_mtime,
                    "file_size": file_path.stat().st_size,
                    "content_type": "pdf"
                }

                # Get total pages
                with open(file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    total_pages = len(pdf_reader.pages)

                # Process in batches
                batch_results = []
                for start_page in range(0, total_pages, self.chunk_size):
                    end_page = min(start_page + self.chunk_size, total_pages)
                    success, processed_pages = await self._process_pdf_batch(
                        file_path=file_path,
                        start_page=start_page,
                        end_page=end_page,
                        metadata=metadata
                    )
                    batch_results.append({
                        "start_page": start_page + 1,
                        "end_page": end_page,
                        "success": success,
                        "processed_pages": processed_pages
                    })
                    results["batches_processed"] += 1

                # Update results
                file_result = {
                    "filename": file_path.name,
                    "domain": domain,
                    "total_pages": total_pages,
                    "batch_results": batch_results,
                    "success": all(b["success"] for b in batch_results)
                }

                results["files"].append(file_result)
                if file_result["success"]:
                    results["processed"] += 1
                else:
                    results["failed"] += 1

            logger.info(
                f"Knowledge base processing complete: {results['processed']} processed, {results['failed']} failed, {results['batches_processed']} batches")
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
