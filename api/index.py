import os
import json
import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Load telemetry data (assume q-vercel-latency.json is in project root)
with open('q-vercel-latency.json', 'r') as f:
    telemetry_data = json.load(f)

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)
@app.get("/")
async def health():
    return { "status":"ok" , "message":"deploy successful"}
@app.post("/")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 0)
    
    results = {}
    for region in regions:
        region_data = [r for r in telemetry_data if r.get("region") == region]
        latencies = [r.get("latency_ms", 0) for r in region_data if "latency_ms" in r]
        uptimes = [r.get("uptime", 0) for r in region_data if "uptime" in r]
        
        if latencies:
            results[region] = {
                "avg_latency": float(np.mean(latencies)),
                "p95_latency": float(np.percentile(latencies, 95)),
                "avg_uptime": float(np.mean(uptimes)) if uptimes else 0.0,
                "breaches": sum(1 for lat in latencies if lat > threshold_ms)
            }
    
    return results

# For Vercel compatibility (runs the app)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
