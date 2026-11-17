import os
import asyncio
from google.genai import Client

# Vertex AI mode:
client = Client(vertexai=True, project=os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-ee26737d3114"), location="us-central1")
res = client.models.generate_content(model="gemini-2.5-flash", contents="Respond in one sentence: What is the Stabilization Navigator?")
print(res.text)
