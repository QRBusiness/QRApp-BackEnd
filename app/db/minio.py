import io
import json
import uuid
from mimetypes import guess_type
from typing import Any, List

from minio import Minio
from minio.deleteobjects import DeleteObject

from app.core.config import settings


class MinIO:
    def __init__(
        self,
        bucket_name: str,
        endpoint: str = "localhost:9000",
        access_key: str | None = None,
        secret_key: str | None = None,
        secure: bool = False,
        public: bool = False,
    ):
        self.endpoint = endpoint
        self.secure = secure
        self.bucket_name = bucket_name
        self.client = Minio(
            endpoint=self.endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=self.secure,
        )
        self.initialize(public)

    def initialize(self, public: bool = False):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            if public:
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"],
                        }
                    ],
                }
                self.client.set_bucket_policy(bucket_name=self.bucket_name, policy=json.dumps(policy))

    def upload_from_file(self, file_path: str, object_name: str | None = None) -> str:
        content_type, _ = guess_type(file_path)
        if object_name is None:
            object_name = file_path
        with open(file_path, "rb") as f:
            self.upload(object=f, object_name=object_name, content_type=content_type or "application/octet-stream")
        return object_name

    def upload(self, object: Any, object_name: str = None, content_type: str = "application/octet-stream") -> str:
        if object_name is None:
            object_name = f"{uuid.uuid4().hex}"
        if isinstance(object, bytes):
            data = io.BytesIO(object)
            size = len(object)
        elif hasattr(object, "read"):
            data = object
            data.seek(0, io.SEEK_END)
            size = data.tell()
            data.seek(0)
        else:
            raise ValueError("Error. Provide bytes or file-like object.")

        self.client.put_object(
            bucket_name=self.bucket_name, object_name=object_name, data=data, length=size, content_type=content_type
        )
        return object_name

    def remove(self, object_name: str | List[str]) -> bool:
        try:
            if isinstance(object_name, str):
                self.client.remove_object(self.bucket_name, object_name)
            else:
                object_name = [DeleteObject(obj) for obj in object_name]
                self.client.remove_objects(self.bucket_name, object_name)
            return True
        except Exception as e:
            print(e)
            return False

    def objects(self):
        return [object.object_name for object in self.client.list_objects(self.bucket_name)]

    def get_url(self, object_name: str):
        return f"{"https" if self.secure else "http"}://{self.endpoint}/{self.bucket_name}/{object_name}"


QRCode = MinIO(
    bucket_name="qrcode",
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=True,
    public=True,
)
