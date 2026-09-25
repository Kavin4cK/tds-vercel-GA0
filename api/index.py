from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json
import math


app = FastAPI()


# Allow browser-based dashboards from any website to send POST requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["*"],
)


# This describes the JSON body that the POST request must contain.
class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


# Read the supplied telemetry bundle once, when this function instance starts.
DATA_FILE = Path(__file__).with_name("q-vercel-latency.json")

with DATA_FILE.open("r", encoding="utf-8") as file:
    TELEMETRY = json.load(file)


def mean(numbers: list[float]) -> float:
    return sum(numbers) / len(numbers)


def percentile_95(numbers: list[float]) -> float:
    """
    Calculate p95 using linear interpolation, equivalent to NumPy's
    usual percentile method.

    Example: if there are 100 sorted values, p95 lies at position 94.05
    when counting positions from zero.
    """
    values = sorted(numbers)

    if len(values) == 1:
        return values[0]

    position = 0.95 * (len(values) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    if lower_index == upper_index:
        return values[lower_index]

    fraction = position - lower_index

    return (
        values[lower_index]
        + fraction * (values[upper_index] - values[lower_index])
    )


@app.post("/analytics")
def analytics(request: AnalyticsRequest):
    results = {}

    for region in request.regions:
        region_records = [
            record
            for record in TELEMETRY
            if record["region"] == region
        ]

        # A clear error is better than returning made-up averages for
        # a region that is not present in the telemetry file.
        if not region_records:
            raise HTTPException(
                status_code=400,
                detail=f"No telemetry records found for region: {region}"
            )

        latencies = [record["latency_ms"] for record in region_records]
        uptimes = [record["uptime"] for record in region_records]

        results[region] = {
            "avg_latency": mean(latencies),
            "p95_latency": percentile_95(latencies),
            "avg_uptime": mean(uptimes),
            "breaches": sum(
                latency > request.threshold_ms
                for latency in latencies
            )
        }

    return results