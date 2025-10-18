"""Utility helpers for persisting raw payloads to MinIO."""

from __future__ import annotations

import json
import logging
from typing import Any

import botocore
import boto3

logger = logging.getLogger(__name__)


class MinioStore:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str) -> None:
        self.endpoint = endpoint
        self.bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=botocore.client.Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

    def ensure_bucket(self) -> None:
        """Create the bucket on first run (idempotent)."""
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except botocore.exceptions.ClientError:
            logger.info("Creating missing MinIO bucket %s", self.bucket)
            self._client.create_bucket(Bucket=self.bucket)

    def put_json(self, key: str, payload: Any) -> None:
        """Store JSON payloads under a stable key for replay/debugging."""
        body = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
        self._client.put_object(Bucket=self.bucket, Key=key, Body=body, ContentType="application/json")
