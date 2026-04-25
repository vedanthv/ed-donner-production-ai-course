from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
import json
import uuid
import boto3
from botocore.exceptions import ClientError
from mangum import Mangum
from datetime import datetime
from context import prompt

# Load environment variables
load_dotenv(override=True)

app = FastAPI()

# CORS
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bedrock client
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("DEFAULT_AWS_REGION", "us-east-1")
)

BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "arn:aws:bedrock:us-east-1:425515537709:inference-profile/global.amazon.nova-2-lite-v1:0" 
)

# Storage
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
S3_BUCKET = os.getenv("S3_BUCKET", "")
MEMORY_DIR = "/tmp/memory"

if USE_S3:
    s3_client = boto3.client("s3")


# ---------------- MEMORY ---------------- #

def get_memory_path(session_id: str) -> str:
    return f"{session_id}.json"


def load_conversation(session_id: str) -> List[Dict]:
    if USE_S3:
        try:
            response = s3_client.get_object(
                Bucket=S3_BUCKET,
                Key=get_memory_path(session_id)
            )
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return []
            raise
    else:
        os.makedirs(MEMORY_DIR, exist_ok=True)
        file_path = os.path.join(MEMORY_DIR, get_memory_path(session_id))

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return []


def save_conversation(session_id: str, messages: List[Dict]):
    if USE_S3:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=get_memory_path(session_id),
            Body=json.dumps(messages),
            ContentType="application/json",
        )
    else:
        os.makedirs(MEMORY_DIR, exist_ok=True)
        file_path = os.path.join(MEMORY_DIR, get_memory_path(session_id))

        with open(file_path, "w") as f:
            json.dump(messages, f)


# ---------------- MODELS ---------------- #

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


# ---------------- BEDROCK CALL ---------------- #

def call_bedrock(conversation: List[Dict], user_message: str) -> str:
    messages = []

    # ✅ STRICT SANITIZATION
    for msg in conversation[-20:]:
        role = msg.get("role")
        content = msg.get("content")

        # Skip invalid entries
        if role not in ["user", "assistant"]:
            continue

        if not content or not isinstance(content, str):
            continue

        content = content.strip()
        if not content:
            continue

        messages.append({
            "role": role,
            "content": [{"text": content}]
        })

    # ✅ ALWAYS add current message (clean)
    user_message = (user_message or "").strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Empty message")

    messages.append({
        "role": "user",
        "content": [{"text": user_message}]
    })

    try:
        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,

            # ✅ KEEP system separate
            system=[{"text": prompt()}],

            messages=messages,

            inferenceConfig={
                "maxTokens": 2000,
                "temperature": 0.7,
                "topP": 0.9
            }
        )

        return response["output"]["message"]["content"][0]["text"]

    except ClientError as e:
        print("==== BEDROCK RAW ERROR ====")
        print(e.response)
        print("===========================")

        raise HTTPException(
            status_code=500,
            detail=f"Bedrock error: {e.response}"
        )

# ---------------- ROUTES ---------------- #

@app.get("/")
async def root():
    return {
        "message": "AI Digital Twin API (Bedrock)",
        "model": BEDROCK_MODEL_ID
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        conversation = load_conversation(session_id)

        assistant_response = call_bedrock(conversation, request.message)

        # Save conversation
        conversation.append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })

        conversation.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": datetime.now().isoformat()
        })

        save_conversation(session_id, conversation)

        return ChatResponse(
            response=assistant_response,
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    return {
        "session_id": session_id,
        "messages": load_conversation(session_id)
    }


# Lambda handler
handler = Mangum(app)