
import os, io
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
from app.estimate_schema import EstimateRequest
from app.pdf_utils import build_pdf

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not configured")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="QuickEstimate Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://quickestimate.site", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.post("/transcribe-and-parse")
async def transcribe_and_parse(audio: UploadFile = File(...)):
    try:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", file=await audio.read()
        )
        transcript_text = transcription.text

        system_prompt = (
            "You are an assistant that extracts estimate data from a transcript. "
            "Return JSON with keys: client_name, job_type, job_description, "
            "items (array of {description, quantity, unit_price}), notes (string). "
            "Tax, totals, etc. are NOT included."
        )
        user_prompt = f"Transcript:\n{transcript_text}"
        chat_resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        parsed_json = chat_resp.choices[0].message.content

        estimate = EstimateRequest.model_validate_json(parsed_json)
        return {"transcript": transcript_text, "parsed_json": estimate}

    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

@app.post("/generate-pdf")
async def generate_pdf(data: EstimateRequest):
    try:
        pdf_bytes = build_pdf(data.model_dump())
        headers = {"Content-Disposition": 'attachment; filename="estimate.pdf"'}
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
