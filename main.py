import fastapi
import wasabi
import uvicorn
import mimetypes
import os
from langchain_community.document_loaders import PyPDFLoader

app = fastapi.FastAPI()

@app.post("/upload")
async def upload_file(document: fastapi.UploadFile = fastapi.File(...)):
    file_type, _ = mimetypes.guess_type(document.filename)

    if file_type == "application/pdf":
        wasabi.Printer().good(f"Processing {document.filename} as PDF document...")
        path = os.path.join("files", document.filename)
        with open(path, "wb") as f:
            f.write(await document.read())
        wasabi.Printer().info(f"{document.filename} saved successfully.")
        loader = PyPDFLoader(path)
        wasabi.Printer().good(f"{document.filename} loaded successfully.")
        return {"message": "Document processed successfully."}

    else:
        wasabi.Printer().warn("Unsupported file type.")
        return {"message": "Unsupported file type."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5820, reload=True)
