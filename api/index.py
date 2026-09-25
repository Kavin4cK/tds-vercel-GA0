from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from statistics import mean


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response
# Request format expected by the endpoint
class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


# Telemetry data
DATA = [
    {"region": "apac", "latency_ms": 122.87, "uptime_pct": 99.383},
    {"region": "apac", "latency_ms": 171.7, "uptime_pct": 98.451},
    {"region": "apac", "latency_ms": 176.37, "uptime_pct": 98.4},
    {"region": "apac", "latency_ms": 122.21, "uptime_pct": 98.433},
    {"region": "apac", "latency_ms": 116.79, "uptime_pct": 98.845},
    {"region": "apac", "latency_ms": 200.06, "uptime_pct": 99.026},
    {"region": "apac", "latency_ms": 191.05, "uptime_pct": 98.15},
    {"region": "apac", "latency_ms": 145.38, "uptime_pct": 98.417},
    {"region": "apac", "latency_ms": 191.44, "uptime_pct": 97.945},
    {"region": "apac", "latency_ms": 227.41, "uptime_pct": 99.241},
    {"region": "apac", "latency_ms": 165.87, "uptime_pct": 98.13},
    {"region": "apac", "latency_ms": 164.14, "uptime_pct": 99.04},

    {"region": "emea", "latency_ms": 137.59, "uptime_pct": 98.509},
    {"region": "emea", "latency_ms": 194.54, "uptime_pct": 97.519},
    {"region": "emea", "latency_ms": 204.91, "uptime_pct": 99.099},
    {"region": "emea", "latency_ms": 199.57, "uptime_pct": 98.889},
    {"region": "emea", "latency_ms": 197.77, "uptime_pct": 98.567},
    {"region": "emea", "latency_ms": 120.05, "uptime_pct": 97.144},
    {"region": "emea", "latency_ms": 156.44, "uptime_pct": 98.443},
    {"region": "emea", "latency_ms": 219.51, "uptime_pct": 97.878},
    {"region": "emea", "latency_ms": 161.42, "uptime_pct": 98.199},
    {"region": "emea", "latency_ms": 214.08, "uptime_pct": 99.323},
    {"region": "emea", "latency_ms": 119.66, "uptime_pct": 99.409},
    {"region": "emea", "latency_ms": 204.7, "uptime_pct": 99.217},

    {"region": "amer", "latency_ms": 119.15, "uptime_pct": 97.656},
    {"region": "amer", "latency_ms": 205.55, "uptime_pct": 98.303},
    {"region": "amer", "latency_ms": 213.09, "uptime_pct": 98.191},
    {"region": "amer", "latency_ms": 130.83, "uptime_pct": 98.901},
    {"region": "amer", "latency_ms": 145.82, "uptime_pct": 97.731},
    {"region": "amer", "latency_ms": 223.2, "uptime_pct": 98.191},
    {"region": "amer", "latency_ms": 186.47, "uptime_pct": 98.364},
    {"region": "amer", "latency_ms": 153.57, "uptime_pct": 99.257},
    {"region": "amer", "latency_ms": 137.3, "uptime_pct": 97.522},
    {"region": "amer", "latency_ms": 163.55, "uptime_pct": 97.577},
    {"region": "amer", "latency_ms": 167.67, "uptime_pct": 97.366},
    {"region": "amer", "latency_ms": 113.02, "uptime_pct": 97.116},
]


def percentile_95(values):
    """Calculate the 95th percentile using linear interpolation."""
    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * 0.95
    lower = int(position)
    upper = lower + 1

    if upper >= len(values):
        return values[lower]

    fraction = position - lower

    return values[lower] + (values[upper] - values[lower]) * fraction


@app.post("/")
def analytics(request: AnalyticsRequest):
    result = {}

    for region in request.regions:
        records = [
            row for row in DATA
            if row["region"] == region
        ]

        if not records:
            continue

        latencies = [row["latency_ms"] for row in records]
        uptimes = [row["uptime_pct"] for row in records]

        breaches = sum(
            row["latency_ms"] > request.threshold_ms
            for row in records
        )

        result[region] = {
            "avg_latency": mean(latencies),
            "p95_latency": percentile_95(latencies),
            "avg_uptime": mean(uptimes),
            "breaches": breaches
        }

    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*"
        }
    )