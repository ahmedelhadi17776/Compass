from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from crewai import Agent, Task, Crew
from langchain.tools import Tool
from Backend.ai_services.llm.llm_service import LLMService
from Backend.utils.logging_utils import get_logger
from pydantic import Field
from Backend.services.todo_service import TodoService
from Backend.data_layer.database.models.todo import TodoStatus, TodoPriority
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class TodoAgent:
    def __init__(self, db_session=None):
        self.agent = Agent(
            role="Todo Management Specialist",
            goal="Create and edit todos from natural language instructions",
            backstory="""I am an expert in todo management and organization. I help users 
                        efficiently create and manage their todos by understanding natural 
                        language and extracting structured information.""",
            tools=[
                Tool(
                    name="create_todo",
                    func=self.create_todo,
                    description="Creates a new todo item from natural language"
                ),
                Tool(
                    name="edit_todo",
                    func=self.edit_todo,
                    description="Processes a natural language request to edit a todo, identifying which todo to edit and how"
                )
            ],
            verbose=True,
            allow_delegation=True  # Enable task delegation
        )
        
        self.ai_service = LLMService()
        self.db = db_session
        
        # Initialize services instead of repositories
        if db_session:
            # For TodoService, we need to provide a TodoRepository instance
            from Backend.data_layer.repositories.todo_repository import TodoRepository
            todo_repo = TodoRepository(db_session)
            self.todo_service = TodoService(todo_repo)
        else:
            self.todo_service = None
    
    async def create_todo(self, description: str, user_id: int = None) -> Dict[str, Any]:
        """Create a new todo item from natural language description."""
        try:
            # Set current_time once at the beginning
            current_time = datetime.utcnow()
            
            # Use LLM to extract structured data
            todo_analysis = await self.ai_service.generate_response(
                prompt=f"""Extract structured todo information from this description:
Description: {description}

Extract and format as JSON:
- title: A clear, concise title for the todo item
- description: Any additional details (can be empty)
- priority: high, medium, or low
- due_date: Extract any mentioned deadline (YYYY-MM-DD format)
- tags: Array of relevant tags""",
                context={
                    "system_message": "You are a todo extraction AI. Extract structured todo information from natural language."
                }
            )
            
            try:
                # Parse the JSON response
                response_text = todo_analysis.get("text", "")
                
                # Extract JSON from markdown if needed
                if "```json" in response_text:
                    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                
                todo_data = json.loads(response_text)
                
                # Add metadata - use actual datetime objects, not strings
                todo_data["created_at"] = current_time
                todo_data["updated_at"] = current_time
                todo_data["is_recurring"] = False
                todo_data["user_id"] = user_id
                
                # Set status to PENDING by default
                todo_data["status"] = TodoStatus.PENDING
                
                # Convert priority string to enum value
                priority_mapping = {
                    "low": TodoPriority.LOW,
                    "medium": TodoPriority.MEDIUM,
                    "mid": TodoPriority.MEDIUM,
                    "high": TodoPriority.HIGH
                }
                
                if "priority" in todo_data:
                    priority_str = todo_data["priority"].lower()
                    todo_data["priority"] = priority_mapping.get(priority_str, TodoPriority.MEDIUM)
                else:
                    todo_data["priority"] = TodoPriority.MEDIUM
                
                # Convert due_date string to datetime object if present
                if "due_date" in todo_data and todo_data["due_date"]:
                    try:
                        # Parse YYYY-MM-DD format
                        due_date = datetime.strptime(todo_data["due_date"], "%Y-%m-%d")
                        
                        # Ensure due_date is not in the past
                        if due_date < current_time:
                            # If due date is in the past, set it to end of current day
                            logger.warning(f"Due date {due_date} is in the past, adjusting to future date")
                            adjusted_due_date = current_time.replace(hour=23, minute=59, second=59)
                            todo_data["due_date"] = adjusted_due_date
                        else:
                            todo_data["due_date"] = due_date
                    except ValueError:
                        # If parsing fails, remove invalid date
                        logger.warning(f"Invalid due_date format: {todo_data['due_date']}")
                        todo_data.pop("due_date", None)
                
                # Save to database if service is available
                if self.todo_service is not None:
                    db_todo = await self.todo_service.create_todo(**todo_data)
                    if db_todo:
                        todo_data["id"] = db_todo.id if hasattr(db_todo, 'id') else None
                
                # Ensure all values are JSON serializable
                # Convert datetime objects to strings
                for key, value in list(todo_data.items()):
                    if isinstance(value, datetime):
                        todo_data[key] = value.isoformat()
                    elif isinstance(value, (TodoStatus, TodoPriority)):  # Check if it's an enum
                        todo_data[key] = value.value
                    elif isinstance(value, (list, tuple)):
                        # Handle lists that might contain non-serializable items
                        todo_data[key] = [
                            item.value if isinstance(item, (TodoStatus, TodoPriority)) else 
                            item.isoformat() if hasattr(item, "isoformat") else 
                            item 
                            for item in value
                        ]
                
                return {
                    "status": "success",
                    "message": f"Todo '{todo_data['title']}' created successfully",
                    "todo": todo_data
                }
            except Exception as e:
                logger.error(f"Error parsing todo data: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Could not parse todo information: {str(e)}",
                    "raw_response": todo_analysis.get("text", "")
                }
        except Exception as e:
            logger.error(f"Todo creation failed: {str(e)}")
            return {"status": "error", "message": f"Todo creation failed: {str(e)}"}

    async def edit_todo(self, description: str, user_id: int = None, previous_messages: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Process a natural language request to edit a todo item.
        
        Args:
            description: A natural language description of the edit to perform
            user_id: The ID of the user making the request
            previous_messages: Optional list of previous conversation messages in format [{"sender": "user|assistant", "text": "message content"}]
            
        Returns:
            A dictionary with the status and result of the edit operation
        """
        try:
            logger.info(f"Processing edit request: '{description}' for user {user_id}")
            
            # Process conversation history from input or get from orchestrator
            conversation_history = []
            
            # First priority: Check for directly passed previous_messages
            if previous_messages:
                logger.info(f"Using {len(previous_messages)} directly passed previous messages")
                # Convert previous_messages format to conversation_history format
                for msg in previous_messages:
                    # Ensure msg is a dictionary before calling .get()
                    if isinstance(msg, dict):
                        sender = msg.get("sender", "")
                        text = msg.get("text", "")
                        if sender and text:
                            role = "user" if sender == "user" else "assistant"
                            conversation_history.append({"role": role, "content": text})
                    else:
                        logger.warning(f"Skipping non-dictionary message: {msg}")
            # Second priority: Get from orchestrator if available
            elif self.db:
                from Backend.orchestration.ai_orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator(self.db)
                history = orchestrator._get_conversation_history(user_id)
                if history:
                    conversation_history = history.get_messages()
                    logger.info(f"Retrieved {len(conversation_history)} conversation history messages from AIOrchestrator")
                else:
                    logger.warning("No conversation history found in AIOrchestrator")
            
            # Create a context string from recent conversation for reference resolution
            conversation_context = ""
            if conversation_history:
                # Format up to the last 4 messages (2 exchanges) to provide context
                recent_messages = conversation_history[-4:] if len(conversation_history) >= 4 else conversation_history
                for msg in recent_messages:
                    # Ensure msg is a dictionary before calling .get()
                    if isinstance(msg, dict):
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        if role and content:
                            conversation_context += f"{role.capitalize()}: {content}\n"
                    else:
                        # Handle string messages or other unexpected types
                        if isinstance(msg, str):
                            conversation_context += f"Message: {msg}\n"
                        else:
                            logger.warning(f"Skipping unexpected message type: {type(msg)}")
                logger.info(f"Created conversation context with {len(recent_messages)} recent messages")
            else:
                logger.info("No conversation context created (empty history)")
            
            # First, use LLM to understand what changes are needed and identify the todo
            # Include conversation context to help resolve references like "second todo" or "it"
            logger.info("Calling LLM to extract edit data")
            edit_analysis = await self.ai_service.generate_response(
                prompt=f"""Parse this todo edit request with the conversation context to extract the following information as JSON:

{conversation_context}
Current Request: {description}

Extract and format as JSON:
- todo_identifier: The description, title, or index reference that helps identify which todo the user is referring to (e.g., "Dad's birthday party" or "the second todo in the list")
- edit_type: What kind of edit (e.g., mark_complete, change_title, change_due_date, change_priority, etc.)
- new_value: The new value to set (if applicable)
- index_reference: If the user refers to a todo by position (like "first", "second", "last"), extract that index (1 for first, 2 for second, etc.)""",
                context={
                    "system_message": "You are a todo management AI. Extract edit instructions from natural language within conversation context."
                }
            )
            
            # Parse the response
            response_text = edit_analysis.get("text", "")
            logger.info(f"Raw LLM response: {response_text[:100]}...")
            
            # Extract JSON from markdown if needed
            if "```json" in response_text:
                json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
                    logger.info("Extracted JSON from markdown code block")
            
            try:
                edit_data = json.loads(response_text)
                logger.info(f"Parsed edit data: {edit_data}")
            except Exception as e:
                logger.error(f"Error parsing edit data: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Could not understand edit request: {str(e)}",
                    "raw_response": response_text
                }
            
            # Get the todo identifier from the edit data
            todo_identifier = edit_data.get("todo_identifier")
            index_reference = edit_data.get("index_reference")
            
            logger.info(f"Todo identifier: {todo_identifier}, Index reference: {index_reference}")
            
            if not todo_identifier and not index_reference:
                return {"status": "error", "message": "Could not identify which todo to edit"}
            
            # Use ContextBuilder to get all todos for the user
            if self.db:
                from Backend.orchestration.context_builder import ContextBuilder
                context_builder = ContextBuilder(self.db)
                
                # Get context specifically for todos domain
                logger.info("Fetching todos context")
                context_data = await context_builder.get_full_context(user_id, domains=["todos"])
                
                if "todos" not in context_data or not context_data["todos"]:
                    logger.warning("No todos found in context data")
                    return {"status": "error", "message": "No todos found for this user"}
                
                # Extract todos from the context
                todos = context_data["todos"]
                if isinstance(todos, dict) and "items" in todos:
                    todos = todos["items"]
                
                logger.info(f"Found {len(todos)} todos in context")
                
                best_match_id = None  # Initialize to None
                
                # Handle index-based reference (e.g., "the second todo")
                if index_reference:
                    try:
                        idx = int(index_reference) - 1  # Convert to 0-based index
                        logger.info(f"Processing index reference: {index_reference} (zero-based: {idx})")
                        
                        # Extract the previously listed todos from conversation history if available
                        listed_todos = []
                        
                        # Only look for listed todos in the last assistant message 
                        if conversation_history:
                            for i in range(len(conversation_history) - 1, -1, -1):
                                msg = conversation_history[i]
                                # Ensure msg is a dictionary before calling .get()
                                if isinstance(msg, dict) and msg.get('role') == 'assistant':
                                    content = msg.get('content', '')
                                    if not isinstance(content, str):
                                        logger.warning(f"Content is not a string: {type(content)}")
                                        continue
                                        
                                    logger.info(f"Examining assistant message: {content[:50]}...")
                                    
                                    try:
                                        # Search for numbered list items in the message
                                        # Updated regex to handle more formats with more flexibility
                                        list_pattern = r'(\d+)[\s]*[\.:\)]\s*([^\n(]+)(?:\s*\(([^)]*)\))?'
                                        matches = re.findall(list_pattern, content)
                                        
                                        if matches:
                                            logger.info(f"Found {len(matches)} numbered items in message")
                                            for match in matches:
                                                # Check if match is a tuple with at least 2 elements
                                                if not isinstance(match, tuple) or len(match) < 2:
                                                    logger.warning(f"Unexpected match format: {match}")
                                                    continue
                                                    
                                                try:
                                                    num = match[0].strip()
                                                    title = match[1].strip()
                                                    status = match[2].strip() if len(match) > 2 and match[2] else "unknown"
                                                    
                                                    # Validate the values
                                                    if not num or not title:
                                                        logger.warning(f"Invalid list item: num={num}, title={title}")
                                                        continue
                                                    
                                                    try:
                                                        list_index = int(num)
                                                    except ValueError:
                                                        logger.warning(f"Could not convert '{num}' to an integer index")
                                                        continue
                                                    
                                                    listed_todos.append({
                                                        "list_index": list_index,
                                                        "title": title,
                                                        "status": status
                                                    })
                                                    logger.info(f"Added listed todo: #{num} - '{title}'")
                                                except (ValueError, IndexError) as e:
                                                    logger.warning(f"Error processing match {match}: {str(e)}")
                                            break
                                    except Exception as e:
                                        logger.error(f"Error processing content with regex: {str(e)}")
                        
                        logger.info(f"Found {len(listed_todos)} listed todos in conversation history")
                        
                        # If we found listed todos in conversation, use that order
                        if listed_todos and idx < len(listed_todos):
                            try:
                                # Extract the title from the list item
                                listed_todo = listed_todos[idx]
                                if not isinstance(listed_todo, dict):
                                    logger.warning(f"Listed todo is not a dictionary: {type(listed_todo)}")
                                    raise ValueError("Invalid listed todo format")
                                    
                                referenced_title = listed_todo.get("title")
                                if not referenced_title:
                                    logger.warning("Empty referenced title")
                                    raise ValueError("Empty referenced title")
                                    
                                logger.info(f"Found referenced todo at position {index_reference}: '{referenced_title}'")
                                
                                # Now find that todo in the actual todos list
                                best_match = None
                                for todo in todos:
                                    if not isinstance(todo, dict):
                                        logger.warning(f"Todo is not a dictionary: {type(todo)}")
                                        continue
                                        
                                    todo_title = todo.get("title")
                                    if not todo_title or not isinstance(todo_title, str):
                                        continue
                                        
                                    if referenced_title.lower() in todo_title.lower():
                                        best_match = todo
                                        logger.info(f"Matched todo by title: {todo_title}")
                                        break
                                
                                if best_match:
                                    best_match_id = best_match.get("id")
                                    logger.info(f"Found todo by index reference {index_reference} with ID {best_match_id}")
                                else:
                                    # Fall back to position in the todos array
                                    if idx < len(todos):
                                        todo = todos[idx]
                                        if isinstance(todo, dict):
                                            best_match_id = todo.get("id")
                                            logger.info(f"Falling back to todos array position {idx} with ID {best_match_id}")
                                        else:
                                            logger.warning(f"Todo at position {idx} is not a dictionary: {type(todo)}")
                                            if todo_identifier:
                                                logger.info(f"Falling back to identifier matching due to non-dictionary todo")
                                                # We will continue below with the identifier matching
                                            else:
                                                return {"status": "error", "message": f"Invalid todo at position {index_reference}"}
                                    else:
                                        logger.warning(f"Todo at position {index_reference} not found, array length: {len(todos)}")
                                        if todo_identifier:
                                            logger.info(f"Falling back to identifier matching due to out-of-range index")
                                            # We will continue below with the identifier matching
                                        else:
                                            return {"status": "error", "message": f"Todo at position {index_reference} not found"}
                            except Exception as e:
                                logger.error(f"Error processing listed todo: {str(e)}")
                                if todo_identifier:
                                    logger.info(f"Falling back to identifier matching due to exception: {str(e)}")
                                    # We will continue below with the identifier matching
                                else:
                                    return {"status": "error", "message": f"Error finding todo at position {index_reference}: {str(e)}"}
                        else:
                            # If no listed todos in conversation or index out of range, 
                            # explicitly mention this and use the main todos list
                            if not listed_todos:
                                logger.warning("No numbered list of todos found in conversation history")
                            else:
                                logger.warning(f"Index {index_reference} is out of range for {len(listed_todos)} listed todos")
                            
                            logger.info("Falling back to using the index directly on the user's todos")
                            
                            # If no listed todos in conversation, use the main todos list
                            if idx < len(todos):
                                todo = todos[idx]
                                if isinstance(todo, dict):
                                    best_match_id = todo.get("id")
                                    logger.info(f"Using todos array position {idx} with ID {best_match_id}")
                                else:
                                    logger.warning(f"Todo at position {idx} is not a dictionary: {type(todo)}")
                                    if todo_identifier:
                                        logger.info(f"Falling back to identifier matching due to non-dictionary todo")
                                        # We will continue below with the identifier matching
                                    else:
                                        return {"status": "error", "message": f"Invalid todo at position {index_reference}"}
                            else:
                                logger.warning(f"Todo at position {index_reference} not found, array length: {len(todos)}")
                                if todo_identifier:
                                    logger.info(f"Falling back to identifier matching due to out-of-range index")
                                    # We will continue below with the identifier matching
                                else:
                                    return {"status": "error", "message": f"Todo at position {index_reference} not found"}
                    
                    except (ValueError, IndexError) as e:
                        logger.error(f"Error finding todo by index: {str(e)}")
                        if todo_identifier:
                            logger.info(f"Falling back to identifier matching due to exception in index handling: {str(e)}")
                            # We will continue below with the identifier matching
                        else:
                            return {"status": "error", "message": f"Could not find todo at position {index_reference}"}
                
                # If we still don't have a best_match_id and we have a todo_identifier, use LLM to find by identifier
                if best_match_id is None and todo_identifier:
                    # Use LLM to find the best match by title/description
                    logger.info(f"Finding best match for identifier: '{todo_identifier}'")
                    match_analysis = await self.ai_service.generate_response(
                        prompt=f"""Find the best matching todo from the list based on this identifier: "{todo_identifier}"

Available todos:
{json.dumps(todos, indent=2)}

Return only the ID of the best matching todo as a plain number without any explanation:""",
                        context={
                            "system_message": "You are a precise matching AI. Find the best matching todo and return only its ID."
                        }
                    )
                    
                    try:
                        best_match_id_str = match_analysis.get("text", "").strip()
                        logger.info(f"LLM returned match ID: '{best_match_id_str}'")
                        best_match_id = int(best_match_id_str)
                    except ValueError as e:
                        logger.error(f"Error parsing best match ID: {str(e)}, raw text: '{match_analysis.get('text', '')}'")
                        return {"status": "error", "message": f"Could not identify todo: {str(e)}"}
                
                # Safety check for best_match_id
                if best_match_id is None:
                    logger.error("Failed to identify todo: best_match_id is None")
                    return {"status": "error", "message": "Failed to identify which todo to edit"}
                
                logger.info(f"Final selected todo ID: {best_match_id}")
                
                # Now that we have the todo ID, prepare the update data
                update_data = {}
                
                # Process the edit type
                edit_type = edit_data.get("edit_type", "").lower()
                new_value = edit_data.get("new_value")
                
                logger.info(f"Edit type: {edit_type}, New value: {new_value}")
                
                if edit_type == "mark_complete" or "complete" in edit_type:
                    update_data["status"] = TodoStatus.COMPLETED
                    logger.info("Setting status to COMPLETED")
                elif edit_type == "mark_in_progress" or "progress" in edit_type:
                    update_data["status"] = TodoStatus.IN_PROGRESS
                    logger.info("Setting status to IN_PROGRESS")
                elif edit_type == "mark_pending" or "pending" in edit_type:
                    update_data["status"] = TodoStatus.PENDING
                    logger.info("Setting status to PENDING")
                elif edit_type == "mark_archived" or "archive" in edit_type:
                    update_data["status"] = TodoStatus.ARCHIVED
                    logger.info("Setting status to ARCHIVED")
                elif edit_type == "change_title" or "title" in edit_type:
                    update_data["title"] = new_value
                    logger.info(f"Changing title to '{new_value}'")
                elif edit_type == "change_description" or "description" in edit_type:
                    update_data["description"] = new_value
                    logger.info(f"Changing description to '{new_value}'")
                elif edit_type == "change_priority" or "priority" in edit_type:
                    priority_mapping = {
                        "low": TodoPriority.LOW,
                        "medium": TodoPriority.MEDIUM,
                        "mid": TodoPriority.MEDIUM, 
                        "high": TodoPriority.HIGH
                    }
                    if isinstance(new_value, str):
                        priority_val = priority_mapping.get(new_value.lower(), TodoPriority.MEDIUM)
                        update_data["priority"] = priority_val
                        logger.info(f"Setting priority to {priority_val}")
                elif edit_type == "change_due_date" or "due" in edit_type:
                    if isinstance(new_value, str):
                        try:
                            # Try to parse the date
                            due_date = datetime.strptime(new_value, "%Y-%m-%d")
                            update_data["due_date"] = due_date
                            logger.info(f"Setting due date to {due_date}")
                        except ValueError:
                            logger.warning(f"Invalid due_date format: {new_value}")
                else:
                    # Generic case - just try to update the field with the new value
                    field_name = edit_type.replace("change_", "")
                    update_data[field_name] = new_value
                    logger.info(f"Setting {field_name} to '{new_value}'")
                
                # Apply the update
                if self.todo_service:
                    # Find the todo to get its title for the success message
                    todo_title = None
                    for todo in todos:
                        if isinstance(todo, dict) and todo.get("id") == best_match_id:
                            todo_title = todo.get("title")
                            break
                    
                    if todo_title:
                        logger.info(f"Found todo title: '{todo_title}'")
                    else:
                        logger.warning(f"Could not find title for todo with ID {best_match_id}")
                    
                    logger.info(f"Updating todo {best_match_id} with data: {update_data}")
                    try:
                        updated_todo = await self.todo_service.update_todo(best_match_id, user_id, **update_data)
                        
                        if updated_todo:
                            logger.info(f"Todo {best_match_id} updated successfully")
                            
                            # Convert to dict if it's an ORM object
                            if hasattr(updated_todo, 'to_dict'):
                                updated_todo_dict = updated_todo.to_dict()
                                logger.info("Converted todo object to dictionary")
                            else:
                                updated_todo_dict = updated_todo
                                logger.info("Todo already in dictionary form")
                                
                            # Ensure all values are JSON serializable
                            for key, value in list(updated_todo_dict.items()):
                                if isinstance(value, datetime):
                                    updated_todo_dict[key] = value.isoformat()
                                elif hasattr(value, 'value'):  # Handle enums
                                    updated_todo_dict[key] = value.value
                            
                            # Create a more informative success message that includes the todo title
                            success_message = f"Todo"
                            if todo_title:
                                success_message += f" '{todo_title}'"
                            
                            # Add the action that was performed
                            if edit_type == "mark_complete" or "complete" in edit_type:
                                success_message += " marked as complete"
                            elif edit_type == "mark_in_progress" or "progress" in edit_type:
                                success_message += " marked as in progress"
                            elif edit_type == "mark_pending" or "pending" in edit_type:
                                success_message += " marked as pending"
                            elif edit_type == "mark_archived" or "archive" in edit_type:
                                success_message += " archived"
                            else:
                                success_message += " updated successfully"
                            
                            logger.info(f"Success message: {success_message}")
                                
                            return {
                                "status": "success",
                                "message": success_message,
                                "todo": updated_todo_dict
                            }
                        else:
                            logger.error(f"Failed to update todo with ID {best_match_id}")
                            return {"status": "error", "message": f"Failed to update todo with ID {best_match_id}"}
                    except Exception as e:
                        logger.error(f"Error updating todo: {str(e)}")
                        return {"status": "error", "message": f"Error updating todo: {str(e)}"}
                else:
                    logger.error("Todo service not available")
                    return {"status": "error", "message": "Todo service unavailable"}
            else:
                logger.error("Database session not available")
                return {"status": "error", "message": "Database session unavailable"}
            
        except Exception as e:
            logger.error(f"Todo edit failed: {str(e)}")
            return {"status": "error", "message": f"Todo edit failed: {str(e)}"}