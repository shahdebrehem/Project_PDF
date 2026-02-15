# PDF Summarizer

This project is a PDF summarization application built with:

- **Flutter** for the frontend
- **FastAPI** for the backend
- **HuggingFace BART model** for AI summarization

## Features

- Upload and summarize PDF documents
- Copy & Download summarized text
- Supports multiple platforms (Web, Android, iOS, Desktop)
- Stores session data locally with SharedPreferences

## Model

The AI summarizer model is hosted on HuggingFace:  
[https://huggingface.co/hany22/PDF-Summarizer](https://huggingface.co/hany22/PDF-Summarizer)

## Usage

1. Run the FastAPI backend:

```bash
cd Summarization
uvicorn app:app --reload
```
2. Run the Flutter frontend:
```flutter run -d chrome```
3. Open the app and go to the Summary page to upload PDF and generate summaries.
