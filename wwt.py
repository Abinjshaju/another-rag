from fastapi import FastAPI
import uvicorn
import weaviate


app = FastAPI()

@app.get("/connect")
def connect_to_weaviate():
    client = weaviate.connect_to_local()
    client.close()
    return {"message": "Connected to Weaviate"}

@app.post("/initialize-schema")
def initialize_schema():
    client = weaviate.connect_to_local()
    # Example schema definition
    schema = {
        "classes": [
            {
                "class": "pdf_schema",
                "properties": [
                    {
                        "name": "name",
                        "dataType": ["string"]
                    }
                ]
            }
        ]
    }
    client.schema.create(schema)
    return {"message": "Schema initialized"}


if __name__ == "__main__":
    uvicorn.run("wwt:app", host="0.0.0.0", port=5822, reload=True)
