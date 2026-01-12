"""Discussion mention notification template."""


class DiscussionMentionTemplate:
    """Template for @mention notifications in discussions."""

    @staticmethod
    def get_title(actor_name: str) -> str:
        """Get notification title."""
        return f"{actor_name} mentioned you"

    @staticmethod
    def get_body(actor_name: str, target_type: str, excerpt: str) -> str:
        """
        Get notification body.

        Args:
            actor_name: Name of the user who mentioned you
            target_type: Type of target (thread/reply)
            excerpt: Text excerpt containing the mention

        Returns:
            Notification body text
        """
        return f"{actor_name} mentioned you in a {target_type}: {excerpt[:100]}..."

    @staticmethod
    def get_email_subject(actor_name: str) -> str:
        """Get email subject."""
        return f"{actor_name} mentioned you in a discussion"

    @staticmethod
    def get_email_html(
        actor_name: str, target_type: str, excerpt: str, link_url: str
    ) -> str:
        """
        Get HTML email body.

        Args:
            actor_name: Name of the user who mentioned you
            target_type: Type of target (thread/reply)
            excerpt: Text excerpt
            link_url: URL to the discussion

        Returns:
            HTML email body
        """
        return f"""
        <html>
            <body>
                <h2>{actor_name} mentioned you</h2>
                <p>{actor_name} mentioned you in a {target_type}:</p>
                <blockquote>{excerpt}</blockquote>
                <p><a href="{link_url}">View discussion</a></p>
            </body>
        </html>
        """

    @staticmethod
    def get_email_text(actor_name: str, target_type: str, excerpt: str, link_url: str) -> str:
        """Get plain text email body."""
        return f"""
{actor_name} mentioned you in a {target_type}:

{excerpt}

View discussion: {link_url}
"""
