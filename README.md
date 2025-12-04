1. Create virtualenv and install requirements:
   python -m venv .venv
   .venv/Scripts/activate
   pip install -r requirements.txt

2. Run:
   uvicorn app.main:app --reload

3. Endpoints:
   POST /upload-file (multipart/form-data file)
   POST /extract  {query, top_k}
   POST /answer   {query, top_k}
   GET  /documents
   DELETE /documents/{doc_id}