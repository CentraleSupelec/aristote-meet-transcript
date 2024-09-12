import os
from typing import Literal
import requests
import base64
import json

from dotenv import load_dotenv
from requests.models import Response

load_dotenv(".env")

ARISTOTE_API_BASE_URL = os.environ["ARISTOTE_API_BASE_URL"]
ARISTOTE_API_CLIENT_ID = os.environ["ARISTOTE_API_CLIENT_ID"]
ARISTOTE_API_CLIENT_SECRET = os.environ["ARISTOTE_API_CLIENT_SECRET"]
ARISTOTE_END_USER_IDENTIFIER = os.environ["ARISTOTE_END_USER_IDENTIFIER"]

WEBHOOK_BASE_URL = os.environ["WEBHOOK_BASE_URL"]

token = None


def get_token():
    token_response: Response = requests.post(
        f"{ARISTOTE_API_BASE_URL}/token",
        json={
            "grant_type": "client_credentials",
        },
        headers={
            "Authorization": "Basic "
            + base64.b64encode(
                f"{ARISTOTE_API_CLIENT_ID}:{ARISTOTE_API_CLIENT_SECRET}".encode()
            ).decode(),
        },
        timeout=1000,
    )

    if token_response.status_code == 200:
        global token
        token = token_response.json()["access_token"]
    else:
        print(f"Couldn't get token. Error code : {token_response.status_code}")
        return


def aristote_api(
    uri: str, method: Literal["GET", "POST"], json: dict = None, headers: dict = {}
) -> Response:
    get_token()
    headers["Authorization"] = "Bearer " + token
    if json:
        headers["Accept"] = "application/json"

    prefixed_uri = f"{ARISTOTE_API_BASE_URL}/v1/{uri}"
    if method == "GET":
        return requests.get(url=prefixed_uri, headers=headers)
    elif method == "POST":
        return requests.post(url=prefixed_uri, json=json, headers=headers)


def request_enrichment(url) -> str:
    enrichment_parameters = {
        "generateMetadata": False,
        "generateQuiz": False,
        "generateNotes": True,
        "aiModel": "Llama-3-70b-Instruct-AWQ",
        "infrastructure": "CentraleSupélec"
    }

    payload = {
        "url": url,
        "notificationWebhookUrl": f"{WEBHOOK_BASE_URL}/webhook/aristote",
        "enrichmentParameters": enrichment_parameters,
        "endUserIdentifier": ARISTOTE_END_USER_IDENTIFIER,
    }

    enrichment_response = aristote_api(
        uri="enrichments/url", method="POST", json=payload
    )

    if enrichment_response.status_code == 200:
        enrichment_id = enrichment_response.json()["id"]
        return enrichment_id


def get_enrichment_version(enrichment_id, version_id):
    enrichment_version_response = aristote_api(
        uri=f"enrichments/{enrichment_id}/versions/{version_id}", method="GET"
    )
    if enrichment_version_response.status_code == 200:
        return json.loads(enrichment_version_response.text)


def get_transcript(enrichment_id, version_id, language: str = None):
    query_params = ""
    if language:
        query_params = f"?language={language}"

    transcript_response = aristote_api(
        uri=f"enrichments/{enrichment_id}/versions/{version_id}/download_transcript{query_params}",
        method="GET",
    )

    if transcript_response.status_code == 200:
        return transcript_response.text
