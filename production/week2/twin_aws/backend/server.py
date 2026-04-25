from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
import json
import uuid
import boto3
from botocore.exceptions import ClientError
from mangum import Mangum
from context import prompt

# Load environment variables
load_dotenv(override=True)

app = FastAPI()

origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # IMPORTANT
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Storage config
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


# ---------------- ROUTES ---------------- #

@app.get("/")
async def root():
    return {"message": "API running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        # Load memory
        conversation = load_conversation(session_id)

        # Build prompt
        messages = [{"role": "system", "content": prompt()}]

        for msg in conversation[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        messages.append({
            "role": "user",
            "content": request.message
        })

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        full_response = response.choices[0].message.content or ""

        # Save conversation
        conversation.append({"role": "user", "content": request.message})
        conversation.append({"role": "assistant", "content": full_response})
        save_conversation(session_id, conversation)

        return {
            "response": full_response,
            "session_id": session_id
        }

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


handler = Mangum(app)