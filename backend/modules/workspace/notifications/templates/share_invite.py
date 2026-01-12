"""Share invite notification template."""


class ShareInviteTemplate:
    """Template for share invitation notifications."""

    @staticmethod
    def get_title(actor_name: str, resource_name: str) -> str:
        """Get notification title."""
        return f"{actor_name} shared {resource_name} with you"

    @staticmethod
    def get_body(actor_name: str, resource_name: str, permission: str) -> str:
        """
        Get notification body.

        Args:
            actor_name: Name of the user who shared
            resource_name: Name of the shared resource
            permission: Permission level granted (viewer/commenter/editor/owner)

        Returns:
            Notification body text
        """
        return f"{actor_name} shared '{resource_name}' with you as {permission}"

    @staticmethod
    def get_email_subject(actor_name: str, resource_name: str) -> str:
        """Get email subject."""
        return f"{actor_name} shared {resource_name} with you"

    @staticmethod
    def get_email_html(
        actor_name: str, resource_name: str, permission: str, link_url: str
    ) -> str:
        """
        Get HTML email body.

        Args:
            actor_name: Name of the user who shared
            resource_name: Name of the shared resource
            permission: Permission level
            link_url: URL to the shared resource

        Returns:
            HTML email body
        """
        return f"""
        <html>
            <body>
                <h2>New shared resource</h2>
                <p>{actor_name} has shared <strong>{resource_name}</strong> with you.</p>
                <p>You have been granted <strong>{permission}</strong> access.</p>
                <p><a href="{link_url}">Open {resource_name}</a></p>
            </body>
        </html>
        """

    @staticmethod
    def get_email_text(
        actor_name: str, resource_name: str, permission: str, link_url: str
    ) -> str:
        """Get plain text email body."""
        return f"""
{actor_name} has shared "{resource_name}" with you.

You have been granted {permission} access.

Open resource: {link_url}
"""
