"""
Blog Image Upload Service

Handles image upload, compression, and storage to Cloudflare R2
"""
import os
import io
from datetime import datetime
from typing import Tuple, Optional
from uuid import uuid4
from urllib.parse import quote
from PIL import Image
import boto3
from botocore.exceptions import ClientError


class ImageUploadService:
    """Service for uploading and processing blog images"""

    def __init__(self):
        # Use blog-specific R2 credentials
        self.r2_access_key = os.getenv("R2_BLOG_ACCESS_KEY")
        self.r2_secret_key = os.getenv("R2_BLOG_SECRET_KEY")
        self.r2_endpoint = os.getenv("R2_ENDPOINT")
        self.r2_bucket = os.getenv("R2_BLOG_BUCKET", "Blog-Photo")
        self.cdn_base_url = os.getenv("R2_CDN_URL", self.r2_endpoint)

        missing = []
        if not self.r2_access_key:
            missing.append("R2_BLOG_ACCESS_KEY")
        if not self.r2_secret_key:
            missing.append("R2_BLOG_SECRET_KEY")
        if not self.r2_endpoint:
            missing.append("R2_ENDPOINT")
        if missing:
            raise ValueError(f"Blog R2 misconfigured. Missing env vars: {', '.join(missing)}")

        # Image constraints
        self.max_size_bytes = 5 * 1024 * 1024  # 5MB
        self.allowed_formats = {"JPEG", "PNG", "GIF", "WEBP"}
        self.max_width_adaptive = 1920  # Max width for adaptive mode

    def build_cdn_url(self, storage_path: str) -> str:
        """Build a browser-safe CDN URL for an R2 object key."""
        encoded_path = quote(storage_path, safe="/")
        return f"{self.cdn_base_url.rstrip('/')}/{encoded_path}"

    def _get_s3_client(self):
        """Get boto3 S3 client for R2"""
        return boto3.client(
            "s3",
            endpoint_url=self.r2_endpoint,
            aws_access_key_id=self.r2_access_key,
            aws_secret_access_key=self.r2_secret_key,
            region_name="auto",
        )

    def validate_image(self, file_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image file

        Returns: (is_valid, error_message)
        """
        # Check size
        if len(file_data) > self.max_size_bytes:
            return False, f"File size exceeds {self.max_size_bytes / 1024 / 1024}MB limit"

        # Check format
        try:
            img = Image.open(io.BytesIO(file_data))
            if img.format not in self.allowed_formats:
                return False, f"Format {img.format} not allowed. Allowed: {', '.join(self.allowed_formats)}"
            return True, None
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"

    def process_image(
        self,
        file_data: bytes,
        resize_mode: str = "original"
    ) -> Tuple[bytes, int, int, str]:
        """
        Process image: resize and compress

        Args:
            file_data: Original image bytes
            resize_mode: "original" or "adaptive_width"

        Returns:
            (processed_bytes, width, height, format)
        """
        img = Image.open(io.BytesIO(file_data))
        original_format = img.format
        width, height = img.size

        # Convert RGBA to RGB for JPEG
        if img.mode == "RGBA" and resize_mode == "adaptive_width":
            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background

        if resize_mode == "adaptive_width" and width > self.max_width_adaptive:
            # Calculate new dimensions
            ratio = self.max_width_adaptive / width
            new_width = self.max_width_adaptive
            new_height = int(height * ratio)

            # Resize with high-quality resampling
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            width, height = new_width, new_height

        # Compress and save
        output = io.BytesIO()

        if resize_mode == "adaptive_width":
            # Convert to WebP for better compression
            img.save(output, format="WEBP", quality=85, method=6)
            output_format = "WEBP"
        else:
            # Keep original format with light compression
            if original_format == "JPEG":
                img.save(output, format="JPEG", quality=90, optimize=True)
                output_format = "JPEG"
            elif original_format == "PNG":
                img.save(output, format="PNG", optimize=True)
                output_format = "PNG"
            elif original_format == "GIF":
                img.save(output, format="GIF", optimize=True)
                output_format = "GIF"
            else:
                img.save(output, format="WEBP", quality=90)
                output_format = "WEBP"

        processed_data = output.getvalue()
        return processed_data, width, height, output_format

    def upload_to_r2(
        self,
        file_data: bytes,
        filename: str,
        content_type: str
    ) -> Tuple[str, str]:
        """
        Upload file to Cloudflare R2

        Returns:
            (storage_path, cdn_url)
        """
        # Generate unique storage path
        now = datetime.utcnow()
        unique_id = str(uuid4())[:8]
        storage_path = f"blog/{now.year}/{now.month:02d}/{unique_id}_{filename}"

        try:
            s3_client = self._get_s3_client()
            s3_client.put_object(
                Bucket=self.r2_bucket,
                Key=storage_path,
                Body=file_data,
                ContentType=content_type,
                CacheControl="public, max-age=31536000",  # Cache for 1 year
            )

            # Generate CDN URL
            cdn_url = self.build_cdn_url(storage_path)
            return storage_path, cdn_url

        except ClientError as e:
            raise Exception(f"Failed to upload to R2: {str(e)}")

    def delete_from_r2(self, storage_path: str) -> bool:
        """Delete file from R2"""
        try:
            s3_client = self._get_s3_client()
            s3_client.delete_object(
                Bucket=self.r2_bucket,
                Key=storage_path
            )
            return True
        except ClientError as e:
            print(f"Failed to delete from R2: {str(e)}")
            return False

    def process_and_upload(
        self,
        file_data: bytes,
        filename: str,
        resize_mode: str = "original"
    ) -> dict:
        """
        Complete workflow: validate -> process -> upload

        Returns:
            {
                "storage_path": str,
                "url": str,
                "filename": str,
                "size_bytes": int,
                "width": int,
                "height": int,
                "content_type": str,
                "resize_mode": str
            }
        """
        # Validate
        is_valid, error = self.validate_image(file_data, filename)
        if not is_valid:
            raise ValueError(error)

        # Process (resize/compress)
        processed_data, width, height, output_format = self.process_image(file_data, resize_mode)

        # Determine content type and filename
        content_type_map = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "GIF": "image/gif",
            "WEBP": "image/webp"
        }
        content_type = content_type_map.get(output_format, "image/jpeg")

        # Update filename extension if format changed
        name_without_ext = os.path.splitext(filename)[0]
        ext_map = {"JPEG": ".jpg", "PNG": ".png", "GIF": ".gif", "WEBP": ".webp"}
        final_filename = f"{name_without_ext}{ext_map.get(output_format, '.jpg')}"

        # Upload to R2
        storage_path, cdn_url = self.upload_to_r2(processed_data, final_filename, content_type)

        return {
            "storage_path": storage_path,
            "url": cdn_url,
            "filename": final_filename,
            "size_bytes": len(processed_data),
            "width": width,
            "height": height,
            "content_type": content_type,
            "resize_mode": resize_mode
        }


# Global instance
_image_service: Optional[ImageUploadService] = None


def get_image_service() -> ImageUploadService:
    """Get or create image upload service instance"""
    global _image_service
    if _image_service is None:
        _image_service = ImageUploadService()
    return _image_service
