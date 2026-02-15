from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from transformers import BartForConditionalGeneration, BartTokenizer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = 'cuda' if torch.cuda.is_available() else 'cpu'

model_path = "/home/hany/ai_model/bart_model"

model = BartForConditionalGeneration.from_pretrained(model_path).to(device)
tokenizer = BartTokenizer.from_pretrained(model_path)
model.eval()

class TextInput(BaseModel):
    text: str

@app.post("/summarize")
def summarize(input: TextInput):

    inputs = tokenizer(
        input.text,
        return_tensors="pt",
        truncation=True,
        max_length=1024
    ).to(device)

    summary_ids = model.generate(
        **inputs,
        max_length=200,
        min_length=50,
        num_beams=4
    )

    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    return {"summary": summary}
