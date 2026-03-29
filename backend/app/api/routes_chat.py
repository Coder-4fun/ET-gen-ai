"""ET Markets — Chatbot API Routes (SSE streaming)"""
import json
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas import ChatRequest
from app.intelligence.chatbot_agent import stream_chat_response
from app.state import app_state

router = APIRouter()

@router.post("")
async def chat(req: ChatRequest):
    """Stream chat response via SSE."""
    session_id = req.session_id
    if session_id not in app_state.chat_sessions:
        app_state.chat_sessions[session_id] = []

    history = app_state.chat_sessions[session_id]
    signals = app_state.get_signals()
    portfolio = app_state.get_portfolio()

    # Append user message
    history.append({"role": "user", "content": req.message, "timestamp": datetime.now().isoformat()})

    async def event_stream():
        full_response = []
        try:
            async for chunk in stream_chat_response(req.message, history, signals, portfolio):
                full_response.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            # Save assistant response to history
            assistant_msg = "".join(full_response)
            history.append({
                "role": "assistant",
                "content": assistant_msg,
                "timestamp": datetime.now().isoformat()
            })
            app_state.chat_sessions[session_id] = history[-20:]  # Keep last 20 turns
            yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    return app_state.chat_sessions.get(session_id, [])
