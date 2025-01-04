import boto3
import os
from typing import Optional
from botocore.config import Config
from dotenv import load_dotenv

from ingestion.models import ExtractedImage

load_dotenv()
R2_ENDPOINT = os.getenv("R2_ENDPOINT") or "dummy"
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID") or "dummy"
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")

class R2ImageStore:
    def __init__(
        self,
        bucket_name: str,
    ):
        self.bucket = bucket_name
        self.s3 = boto3.client(
            service_name="s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name="auto"
        )

    def _get_image_key(self, paper_id: str, xref: int) -> str:
        return f"{paper_id}/{xref}.png"

    async def store_image(self, paper_id: str, image: ExtractedImage) -> str:
        key = self._get_image_key(paper_id, image.page_num)
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=image.image_data,
            ContentType="image/png"
        )
        return key

    async def get_image(self, paper_id: str, xref: int) -> Optional[bytes]:
        key = self._get_image_key(paper_id, xref)
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except self.s3.exceptions.NoSuchKey:
            return None
