"""Export complete notification template."""


class ExportCompleteTemplate:
    """Template for export job completion notifications."""

    @staticmethod
    def get_title(resource_name: str) -> str:
        """Get notification title."""
        return f"Export complete: {resource_name}"

    @staticmethod
    def get_body(resource_name: str, format_type: str, file_size: str | None = None) -> str:
        """
        Get notification body.

        Args:
            resource_name: Name of the exported resource
            format_type: Export format (PGN/ZIP)
            file_size: File size (optional)

        Returns:
            Notification body text
        """
        size_info = f" ({file_size})" if file_size else ""
        return f"Your export of '{resource_name}' as {format_type} is ready{size_info}"

    @staticmethod
    def get_email_subject(resource_name: str) -> str:
        """Get email subject."""
        return f"Your export is ready: {resource_name}"

    @staticmethod
    def get_email_html(
        resource_name: str,
        format_type: str,
        download_url: str,
        file_size: str | None = None,
        expires_in: str | None = None,
    ) -> str:
        """
        Get HTML email body.

        Args:
            resource_name: Name of the exported resource
            format_type: Export format
            download_url: Pre-signed download URL
            file_size: File size (optional)
            expires_in: Link expiration time (optional)

        Returns:
            HTML email body
        """
        size_info = f"<p>File size: {file_size}</p>" if file_size else ""
        expires_info = f"<p><small>Download link expires in {expires_in}</small></p>" if expires_in else ""

        return f"""
        <html>
            <body>
                <h2>Your export is ready</h2>
                <p>Your export of <strong>{resource_name}</strong> as {format_type} is ready for download.</p>
                {size_info}
                <p><a href="{download_url}" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">Download {format_type}</a></p>
                {expires_info}
            </body>
        </html>
        """

    @staticmethod
    def get_email_text(
        resource_name: str,
        format_type: str,
        download_url: str,
        file_size: str | None = None,
        expires_in: str | None = None,
    ) -> str:
        """Get plain text email body."""
        size_info = f"\nFile size: {file_size}" if file_size else ""
        expires_info = f"\n\nDownload link expires in {expires_in}" if expires_in else ""

        return f"""
Your export is ready!

Your export of "{resource_name}" as {format_type} is ready for download.{size_info}

Download: {download_url}{expires_info}
"""
