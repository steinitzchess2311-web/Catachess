"""Study update notification template."""


class StudyUpdateTemplate:
    """Template for study update notifications (for collaborators)."""

    @staticmethod
    def get_title(actor_name: str, study_name: str, action: str) -> str:
        """
        Get notification title.

        Args:
            actor_name: Name of the user who made the update
            study_name: Name of the study
            action: Type of action (added moves, created variation, etc.)

        Returns:
            Notification title
        """
        return f"{actor_name} {action} in {study_name}"

    @staticmethod
    def get_body(actor_name: str, study_name: str, action: str, details: str | None = None) -> str:
        """
        Get notification body.

        Args:
            actor_name: Name of the user who made the update
            study_name: Name of the study
            action: Type of action
            details: Additional details (optional)

        Returns:
            Notification body text
        """
        body = f"{actor_name} {action} in '{study_name}'"
        if details:
            body += f": {details}"
        return body

    @staticmethod
    def get_email_subject(actor_name: str, study_name: str) -> str:
        """Get email subject."""
        return f"Update in {study_name} by {actor_name}"

    @staticmethod
    def get_email_html(
        actor_name: str, study_name: str, action: str, link_url: str, details: str | None = None
    ) -> str:
        """
        Get HTML email body.

        Args:
            actor_name: Name of the user who made the update
            study_name: Name of the study
            action: Type of action
            link_url: URL to the study
            details: Additional details (optional)

        Returns:
            HTML email body
        """
        details_html = f"<p>{details}</p>" if details else ""

        return f"""
        <html>
            <body>
                <h2>Study update: {study_name}</h2>
                <p>{actor_name} {action} in <strong>{study_name}</strong></p>
                {details_html}
                <p><a href="{link_url}">View study</a></p>
            </body>
        </html>
        """

    @staticmethod
    def get_email_text(
        actor_name: str, study_name: str, action: str, link_url: str, details: str | None = None
    ) -> str:
        """Get plain text email body."""
        details_text = f"\n{details}\n" if details else ""

        return f"""
Study update: {study_name}

{actor_name} {action} in "{study_name}"{details_text}

View study: {link_url}
"""
