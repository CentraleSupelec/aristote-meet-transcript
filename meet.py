import sqlite3
from flask import Flask, jsonify, request, redirect, Response
from datetime import datetime

import os
from dotenv import load_dotenv
from aristote import get_enrichment_version, get_transcript, request_enrichment
from minio import Minio

load_dotenv(".env")

DATABASE_URL = os.environ["DATABASE_URL"]

MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]
MINIO_URL = os.environ["MINIO_URL"]
MINIO_BUCKET = os.environ["MINIO_BUCKET"]

app = Flask(__name__)


def get_filename_by_enrichment_id(
    conn: sqlite3.Connection, enrichment_id: str
) -> str | None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT filename FROM enrichment_requests WHERE enrichment_id = ?", (enrichment_id,)
    )
    row = cursor.fetchone()

    if row:
        return row[0]
    return None


def update_status_by_filename(conn: sqlite3.Connection, filename: str, status: str):
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE enrichment_requests
        SET status = ?
        WHERE filename = ?
    """,
        (status, filename),
    )
    conn.commit()


def add_line(filename: str, enrichment_id: str):
    cursor = conn.cursor()

    request_sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "PENDING"

    cursor.execute(
        """
        INSERT INTO enrichment_requests (filename, enrichment_id, request_sent_at, status)
        VALUES (?, ?, ?, ?, ?)
    """,
        (filename, enrichment_id, request_sent_at, status),
    )

    conn.commit()


@app.route("/webhook/minio", methods=["POST"])
def minio_webhook():
    data = request.get_json()
    s3 = data['s3']
    bucket = s3['bucket']
    bucket_name = bucket['name']
    object = s3['object']
    filename = object['key']

    if bucket_name != MINIO_BUCKET:
        return "Not interested in this bucket"

    client = Minio(MINIO_URL,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
    )

    url = client.presigned_get_object(MINIO_BUCKET, object_name=filename)
    enrichment_id = request_enrichment(url)
    add_line(filename, enrichment_id)
    return ""


@app.route("/webhook/aristote", methods=["POST"])
def aristote_webhook():
    data = request.get_json()

    enrichment_id = data["id"]
    conn = sqlite3.connect(DATABASE_URL)
    filename = get_filename_by_enrichment_id(conn=conn, enrichment_id=enrichment_id)

    if data["status"] == "SUCCESS":
        initial_version_id = data["initialVersionId"]
        print(f"Filename : {filename}")
        if filename:
            update_status_by_filename(conn=conn, filename=filename, status="SUCCESS")
            enrichment_version = get_enrichment_version(
                enrichment_id, initial_version_id
            )
            language = enrichment_version["transcript"]["language"]
            transcript = get_transcript(enrichment_id, initial_version_id, language)
            #TODO: Send transcript/summary to django webhook
        return ""
    elif data["status"] == "FAILURE":
        update_status_by_filename(conn=conn, filename=filename, status="FAILURE")
        return ""


def initiate_database():
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS enrichment_requests (
        filename TEXT PRIMARY KEY,
        enrichment_id TEXT,
        request_sent_at DATETIME,
        enrichment_notification_received_at DATETIME,
        status TEXT
    )
    """
    )

    conn.commit()

if __name__ == "__main__":
    conn = sqlite3.connect(DATABASE_URL)
    initiate_database()
    app.run(host="0.0.0.0", debug=True)

