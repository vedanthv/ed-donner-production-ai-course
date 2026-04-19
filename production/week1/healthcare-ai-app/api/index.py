# How JWT works : https://chatgpt.com/s/t_69e46ae6653c8191aa5b68f6404079ee

import os

# FastAPI core framework + dependency injection
from fastapi import FastAPI, Depends  # type: ignore

# Used to stream responses back to the client (real-time output)
from fastapi.responses import StreamingResponse  # type: ignore

# Pydantic is used for request validation and schema definition
from pydantic import BaseModel  # type: ignore

# Clerk authentication (JWT validation)
from fastapi_clerk_auth import (
    ClerkConfig,
    ClerkHTTPBearer,
    HTTPAuthorizationCredentials,
)  # type: ignore

# OpenAI client for LLM interaction
from openai import OpenAI  # type: ignore


# Initialize FastAPI app
app = FastAPI()


# -----------------------------
# Authentication Setup (Clerk)
# -----------------------------
# Clerk uses JWKS (JSON Web Key Set) URL to validate JWT tokens
clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))

# HTTP Bearer auth middleware
# This ensures all requests to protected routes have valid tokens
clerk_guard = ClerkHTTPBearer(clerk_config)


# -----------------------------
# Request Body Schema
# -----------------------------
# Defines the expected input JSON structure for the API
class Visit(BaseModel):
    patient_name: str
    date_of_visit: str
    notes: str


# -----------------------------
# System Prompt (LLM Behavior)
# -----------------------------
# This instructs the model:
# - What role it should play
# - Exact format of output (strict structure)
system_prompt = """
You are provided with notes written by a doctor from a patient's visit.
Your job is to summarize the visit for the doctor and provide an email.

Reply with exactly three sections with the headings:

### Summary of visit for the doctor's records
### Next steps for the doctor
### Draft of email to patient in patient-friendly language
"""


# -----------------------------
# User Prompt Generator
# -----------------------------
# Converts structured Visit object into text prompt for LLM
def user_prompt_for(visit: Visit) -> str:
    return f"""
Create the summary, next steps and draft email for:

Patient Name: {visit.patient_name}
Date of Visit: {visit.date_of_visit}
Notes: {visit.notes}
"""


# -----------------------------
# API Endpoint
# -----------------------------
@app.post("/api")
def consultation_summary(
    visit: Visit,
    # Dependency injection ensures request is authenticated
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard),
):
    # Extract user ID from decoded JWT token
    # Useful for logging, auditing, or tracking usage
    user_id = creds.decoded["sub"]

    # Initialize OpenAI client
    client = OpenAI()

    # Build user prompt from input data
    user_prompt = user_prompt_for(visit)

    # Messages follow chat format (system + user)
    prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # -----------------------------
    # OpenAI Streaming Call
    # -----------------------------
    # stream=True enables incremental response (token-by-token)
    stream = client.chat.completions.create(
        model="gpt-4.1-nano",  # Fast, lightweight model
        messages=prompt,
        stream=True,
    )

    # -----------------------------
    # Streaming Generator Function
    # -----------------------------
    # This function yields chunks of data as they arrive from OpenAI
    # and formats them as Server-Sent Events (SSE)
    def event_stream():
        for chunk in stream:
            # Each chunk contains partial text (delta)
            text = chunk.choices[0].delta.content

            # Safety check: skip empty chunks
            if text:
                # Split text by newline to preserve formatting
                lines = text.split("\n")

                # Yield all complete lines except the last one
                # (last line may be incomplete due to streaming)
                for line in lines[:-1]:
                    # SSE format requires "data: <message>\n\n"
                    yield f"data: {line}\n\n"

                    # Extra blank line for formatting consistency in frontend
                    yield "data:  \n"

                # Yield last line (may be partial but still needed)
                yield f"data: {lines[-1]}\n\n"

    # -----------------------------
    # Return Streaming Response
    # -----------------------------
    # media_type="text/event-stream" is required for SSE
    return StreamingResponse(event_stream(), media_type="text/event-stream")