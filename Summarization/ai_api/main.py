from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from transformers import BartForConditionalGeneration, BartTokenizer
import nltk

nltk.download('punkt')
from nltk.tokenize import sent_tokenize

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = 'cpu'
model_path = "/home/hany/Summarization/model"

model = BartForConditionalGeneration.from_pretrained(model_path)
model.to(device)
tokenizer = BartTokenizer.from_pretrained(model_path)
model.eval()

class TextInput(BaseModel):
    text: str


def chunk_text(text, max_tokens=900, overlap_ratio=0.15):
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    current_len = 0

    for para in paragraphs:
        para_len = len(tokenizer.tokenize(para))

        if current_len + para_len <= max_tokens:
            current_chunk += para + "\n\n"
            current_len += para_len
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())

            sentences = sent_tokenize(para)
            temp_chunk = ""
            temp_len = 0

            for sent in sentences:
                sent_len = len(tokenizer.tokenize(sent))

                if temp_len + sent_len <= max_tokens:
                    temp_chunk += sent + " "
                    temp_len += sent_len
                else:
                    chunks.append(temp_chunk.strip())

                    overlap_tokens = int(temp_len * overlap_ratio)
                    overlap_words = temp_chunk.split()[-overlap_tokens:]

                    temp_chunk = " ".join(overlap_words) + " " + sent + " "
                    temp_len = len(tokenizer.tokenize(temp_chunk))

            if temp_chunk:
                chunks.append(temp_chunk.strip())

            current_chunk = ""
            current_len = 0

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


@app.post("/summarize")
def summarize(input: TextInput):
    try:
        text_tokens = len(tokenizer.tokenize(input.text))

        if text_tokens < 800:
            ratio = 0.5
        elif text_tokens < 2000:
            ratio = 0.4
        else:
            ratio = 0.3

        max_length = min(600, int(text_tokens * ratio))
        min_length = max(50, int(max_length * 0.4))

        chunks = chunk_text(input.text)

        summaries = []

        for chunk in chunks:
            inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=1024)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            summary_ids = model.generate(
                **inputs,
                max_length=max_length,
                min_length=min_length,
                num_beams=8,
                length_penalty=2.0,
                no_repeat_ngram_size=2
            )

            summaries.append(
                tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
            )

        final_summary = " ".join(summaries)

        return {
            "original_tokens": text_tokens,
            "summary_tokens_limit": max_length,
            "summary": final_summary
        }

    except Exception as e:
        return {"error": str(e)}
