from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List
from datetime import datetime
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import os
from openai import OpenAI

from Backend.data_layer.database.connection import get_db
from Backend.app.schemas.task_schemas import TaskCreate, TaskResponse
from Backend.services.ai_service import AIService
from Backend.api.auth import get_current_user
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction
from Backend.ai_services.llm.llm_service import LLMService
from Backend.data_layer.database.models.user import User
from Backend.ai_services.rag.todo_ai_service import TodoAIService
from Backend.orchestration.ai_orchestrator import AIOrchestrator


# Set up logger
logger = logging.getLogger(__name__)

class LLMRequest(BaseModel):
    prompt: str
    context: Dict = None
    model_parameters: Dict = None

router = APIRouter(prefix="/ai", tags=["AI Services"])

# Initialize centralized AI service
ai_service = AIService()
llm_service = LLMService()

# Add TodoAIService instance
todo_ai_service = TodoAIService()

@router.post("/analyze/task")
async def analyze_task(
    task_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Analyze task using AI agents."""
    try:
        result = await ai_service.process_task_with_ai(
            task_data=task_data,
            task_id=task_data.get("id"),
            process_type="analysis"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/productivity/{user_id}")
async def get_productivity_insights(
    user_id: int,
    interval: str = "daily",
    metrics: List[str] = ["focus", "efficiency", "workload"],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get AI-generated productivity insights."""
    try:
        # Use AIService to get tasks and analyze productivity
        tasks = await ai_service.get_user_tasks(user_id, db)
        insights = await ai_service.analyze_productivity(tasks, interval)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classify-task")
async def classify_task(
    task_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Classify a task using AI."""
    try:
        return await ai_service.classify_task(task_data, db, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-text")
async def analyze_text(
    text: str,
    analysis_type: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Analyze text using different AI services."""
    try:
        return await ai_service.analyze_text(text, analysis_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-productivity")
async def analyze_productivity(
    tasks: List[Dict],
    time_period: str = "daily",
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Analyze task productivity patterns."""
    try:
        return await ai_service.analyze_productivity(tasks, time_period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize")
async def summarize_text(
    text: str,
    max_length: int = 130,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate text summary."""
    try:
        result = await ai_service.summarization_service.generate_summary(text, max_length)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback/{interaction_id}")
async def submit_ai_feedback(
    interaction_id: int,
    feedback_score: float,
    feedback_text: str = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Submit feedback for an AI interaction."""
    try:
        # Use AIService to handle feedback submission
        return await ai_service.submit_feedback(
            interaction_id=interaction_id,
            feedback_score=feedback_score,
            feedback_text=feedback_text,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/llm/generate")
async def generate_llm_response(
    request: LLMRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a response from the LLM service."""
    try:
        logger.info(f"Generating LLM response for user {current_user.id}")
        response = await llm_service.generate_response(
            prompt=request.prompt,
            context=request.context,
            model_parameters=request.model_parameters
        )
        return response
    except Exception as e:
        logger.error(f"Error generating LLM response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/llm/generate/stream")
async def generate_llm_stream(
    request: LLMRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a streaming response from the LLM service."""
    if not current_user:
        logger.error("Authentication required for streaming endpoint")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        logger.info(f"Starting streaming response for user {current_user.id}")
        
        # Create a direct connection to the OpenAI client
        github_token = os.environ.get("GITHUB_TOKEN", "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")
        base_url = "https://models.inference.ai.azure.com"
        model_name = "gpt-4o-mini"
        
        # Configure the OpenAI client directly
        client = OpenAI(
            api_key=github_token,
            base_url=base_url
        )
        
        # Prepare messages
        messages = []
        if request.context and request.context.get("system_message"):
            messages.append({
                "role": "system",
                "content": request.context["system_message"]
            })
        else:
            messages.append({
                "role": "system",
                "content": ""
            })
        
        messages.append({"role": "user", "content": request.prompt})
        
        # Prepare parameters
        params = {
            "temperature": 1.0,
            "max_tokens": 4096,
            "top_p": 1.0
        }
        
        if request.model_parameters:
            params.update(request.model_parameters)
        
        async def generate():
            try:
                # Create a direct streaming response
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    stream=True,
                    **params
                )
                
                # Stream the response
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        yield f"data: {content}\n\n"
                
                # Send a final empty data message to signal the end of the stream
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Error in stream generator: {str(e)}")
                error_msg = str(e).replace('"', '\\"')  # Escape quotes
                yield f"data: {{\"error\": \"{error_msg}\" }}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Error in stream response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/llm/model-info")
async def get_model_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get information about the LLM model."""
    try:
        logger.info(f"Getting model info for user {current_user.id}")
        model_info = await llm_service.get_model_info()
        return model_info
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/llm/enhance-task")
async def enhance_task_description(
    task: Dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enhance a task description using LLM."""
    try:
        logger.info(f"Enhancing task description for user {current_user.id}")
        result = await llm_service.enhance_task_description(task)
        return result
    except Exception as e:
        logger.error(f"Error enhancing task description: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/llm/analyze-workflow")
async def analyze_workflow(
    data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze workflow efficiency using LLM."""
    try:
        logger.info(f"Analyzing workflow for user {current_user.id}")
        result = await llm_service.analyze_workflow(
            workflow_id=data.get("workflow_id"),
            historical_data=data.get("historical_data", [])
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/llm/summarize-meeting")
async def summarize_meeting(
    data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Summarize meeting transcript using LLM."""
    try:
        logger.info(f"Summarizing meeting for user {current_user.id}")
        result = await llm_service.summarize_meeting(
            transcript=data.get("transcript", ""),
            participants=data.get("participants", []),
            duration=data.get("duration", 0)
        )
        return result
    except Exception as e:
        logger.error(f"Error summarizing meeting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/llm/todo-rag")
async def process_todo_rag_query(
    request: LLMRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process natural language queries about todos using RAG."""
    try:
        logger.info(f"Processing Todo RAG query for user {current_user.id}")
        
        # Extract user_id and query
        user_id = current_user.id
        query = request.prompt
        
        # Process the query to determine intent
        if "summary" in query.lower() or "summarize" in query.lower():
            # Get todo analytics for summary
            time_period = "week"  # default
            if "day" in query.lower():
                time_period = "day"
            elif "month" in query.lower():
                time_period = "month"
                
            analytics = await todo_ai_service.analyze_todo_completion(
                user_id=user_id,
                time_period=time_period
            )
            
            # Now use the LLM to generate a natural language response
            context = {
                "system_message": """You are a helpful AI assistant specialized in productivity and task management.
                Summarize the todo analytics data in a helpful, conversational way and provide actionable insights.""",
                "analytics": analytics
            }
            
            response = await llm_service.generate_response(
                prompt=f"Please summarize my todo list analytics for the {time_period}.",
                context=context
            )
            
            return response
            
        elif "suggest" in query.lower() or "recommend" in query.lower() or "idea" in query.lower():
            # Generate todo suggestions
            count = 3  # default
            if "more" in query.lower():
                count = 5
                
            suggestions = await todo_ai_service.generate_todo_suggestions(
                user_id=user_id,
                count=count
            )
            
            # Now use the LLM to present the suggestions in a natural way
            context = {
                "system_message": """You are a helpful AI assistant specialized in productivity and task management.
                Present the todo suggestions in a conversational way, explaining why each might be useful.""",
                "suggestions": suggestions
            }
            
            response = await llm_service.generate_response(
                prompt=f"Please suggest {count} todo items for me to consider.",
                context=context
            )
            
            return response
            
        elif "similar" in query.lower() or "like" in query.lower() or "related" in query.lower():
            # Search for similar todos
            # Extract the search subject from the query
            search_terms = query.lower().split("similar to ")[1] if "similar to " in query.lower() else query
            
            similar_todos = await todo_ai_service.find_similar_todos(
                todo=search_terms,
                limit=5,
                user_id=user_id
            )
            
            # Now use the LLM to present the similar todos in a natural way
            context = {
                "system_message": """You are a helpful AI assistant specialized in productivity and task management.
                Present the similar todos in a conversational way, explaining how they relate to the search query.""",
                "similar_todos": similar_todos,
                "search_query": search_terms
            }
            
            response = await llm_service.generate_response(
                prompt=f"Please find todos similar to: {search_terms}",
                context=context
            )
            
            return response
            
        else:
            # For general todo queries, use semantic search 
            search_results = await todo_ai_service.search_todos(
                query=query,
                user_id=user_id,
                limit=5
            )
            
            # Use the LLM to generate a response based on the search results
            context = {
                "system_message": """You are a helpful AI assistant specialized in productivity and task management.
                Respond to the user's query about their todos in a helpful, conversational way.""",
                "search_results": search_results
            }
            
            response = await llm_service.generate_response(
                prompt=query,
                context=context
            )
            
            return response
            
    except Exception as e:
        logger.error(f"Error processing Todo RAG query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/llm/todo-rag/stream")
async def process_todo_rag_query_stream(
    request: LLMRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process natural language queries about todos using RAG with streaming response."""
    if not current_user:
        logger.error("Authentication required for streaming endpoint")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    try:
        logger.info(f"Processing streaming Todo RAG query for user {current_user.id}")
        
        # Extract user_id and query
        user_id = current_user.id
        query = request.prompt
        
        # Prepare a context based on the query type
        context = ""
        system_message = """You are a helpful AI assistant specialized in productivity and task management.
        Respond to the user's query about their todos in a helpful, conversational way."""
        
        if "summary" in query.lower() or "summarize" in query.lower():
            # Get todo analytics for summary
            time_period = "week"  # default
            if "day" in query.lower():
                time_period = "day"
            elif "month" in query.lower():
                time_period = "month"
                
            analytics = await todo_ai_service.analyze_todo_completion(
                user_id=user_id,
                time_period=time_period
            )
            
            context = f"Todo analytics for {time_period}: {analytics}"
            
        elif "suggest" in query.lower() or "recommend" in query.lower() or "idea" in query.lower():
            # Generate todo suggestions
            count = 3  # default
            if "more" in query.lower():
                count = 5
                
            suggestions = await todo_ai_service.generate_todo_suggestions(
                user_id=user_id,
                count=count
            )
            
            context = f"Todo suggestions: {suggestions}"
            
        elif "similar" in query.lower() or "like" in query.lower() or "related" in query.lower():
            # Search for similar todos
            search_terms = query.lower().split("similar to ")[1] if "similar to " in query.lower() else query
            
            similar_todos = await todo_ai_service.find_similar_todos(
                todo=search_terms,
                limit=5,
                user_id=user_id
            )
            
            context = f"Similar todos to '{search_terms}': {similar_todos}"
            
        else:
            # For general todo queries, use semantic search 
            search_results = await todo_ai_service.search_todos(
                query=query,
                user_id=user_id,
                limit=5
            )
            
            context = f"Todo search results for '{query}': {search_results}"
        
        # Configure the OpenAI client directly
        github_token = os.environ.get("GITHUB_TOKEN", "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")
        base_url = "https://models.inference.ai.azure.com"
        model_name = "gpt-4o-mini"
        
        client = OpenAI(
            api_key=github_token,
            base_url=base_url
        )
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_message + "\n\nHere is information about the user's todos:\n" + context},
            {"role": "user", "content": query}
        ]
        
        # Prepare parameters
        params = {
            "temperature": 1.0,
            "max_tokens": 4096,
            "top_p": 1.0
        }
        
        if request.model_parameters:
            params.update(request.model_parameters)
        
        async def generate():
            try:
                # Create a direct streaming response
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    stream=True,
                    **params
                )
                
                # Stream the response
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        yield f"data: {content}\n\n"
                
                # Send a final empty data message to signal the end of the stream
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Error in stream generator: {str(e)}")
                error_msg = str(e).replace('"', '\\"')  # Escape quotes
                yield f"data: {{\"error\": \"{error_msg}\" }}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in stream response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# TODO: example for what i want
@router.post("/ai/process")
async def process_ai_request(domain: str, prompt: str, user_id: int, db=Depends(get_db)):
    orchestrator = AIOrchestrator(get_db)
    return await orchestrator.process_ai_request(domain, prompt, user_id)
