"""
Created at: 2026-07-09 01:05 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:58 EDT
Last Modified by: Codex

Image linking utilities for extracting article image URLs and keeping
`blog_images` plus `blog_article_images` synchronized.
"""
import re
from datetime import datetime
from typing import List, Set
from uuid import UUID, uuid4
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from sqlalchemy.orm import Session
from sqlalchemy import or_, select

from modules.blogs.db.image_models import BlogImage
from modules.blogs.db.models import BlogArticleImage


def extract_image_urls(markdown_content: str) -> List[str]:
    """
    Extract all image URLs from Markdown content

    Matches pattern: ![alt text](https://cdn.example.com/image.jpg)

    Args:
        markdown_content: Markdown text content

    Returns:
        List of image URLs found in the content
    """
    if not markdown_content:
        return []

    # Pattern matches: ![...](url)
    pattern = r'!\[.*?\]\((https?://[^\)]+)\)'
    urls = re.findall(pattern, markdown_content)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def normalize_image_url(url: str) -> str:
    """Normalize URL variants so encoded and unencoded image URLs match."""
    if not url:
        return ""
    stripped = url.strip()
    try:
        parts = urlsplit(stripped)
        normalized_path = unquote(parts.path)
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), normalized_path, parts.query, parts.fragment))
    except Exception:
        return unquote(stripped)


def image_url_variants(url: str) -> Set[str]:
    """Return URL forms that may exist in legacy rows."""
    normalized = normalize_image_url(url)
    encoded = ""
    if normalized:
        parts = urlsplit(normalized)
        encoded = urlunsplit((parts.scheme, parts.netloc, quote(parts.path, safe="/"), parts.query, parts.fragment))
    return {candidate for candidate in {url.strip(), normalized, encoded, unquote(url.strip())} if candidate}


def find_image_by_url(db: Session, url: str) -> BlogImage | None:
    """Find a BlogImage by exact or normalized URL forms."""
    variants = image_url_variants(url)
    if not variants:
        return None
    image = db.execute(
        select(BlogImage)
        .where(BlogImage.url.in_(variants))
        .order_by(BlogImage.created_at.desc())
    ).scalars().first()
    if image:
        return image
    normalized = normalize_image_url(url)
    if not normalized:
        return None
    candidates = db.execute(
        select(BlogImage).where(
            or_(BlogImage.url.ilike("%" + normalized.rsplit("/", 1)[-1]), BlogImage.storage_path.ilike("%" + normalized.rsplit("/", 1)[-1]))
        )
    ).scalars().all()
    for candidate in candidates:
        if normalize_image_url(candidate.url) == normalized:
            return candidate
    return None


def get_current_linked_images(article_id: UUID, db: Session) -> Set[UUID]:
    """
    Get set of image IDs currently linked to an article

    Args:
        article_id: Article UUID
        db: Database session

    Returns:
        Set of image UUIDs linked to this article
    """
    stmt = select(BlogArticleImage.image_id).where(
        BlogArticleImage.article_id == article_id
    )
    result = db.execute(stmt).scalars().all()
    return set(result)


def link_images_to_article(
    article_id: UUID,
    content: str,
    cover_url: str | None,
    db: Session,
    verbose: bool = False
) -> dict:
    """
    Link images to article based on Markdown content

    This function:
    1. Extracts image URLs from Markdown content
    2. Finds corresponding BlogImage records
    3. Creates BlogArticleImage associations
    4. Updates image metadata (is_orphan, last_referenced_at)

    Args:
        article_id: Article UUID
        content: Markdown content
        cover_url: Cover image URL (optional)
        db: Database session
        verbose: Print debug info

    Returns:
        {
            "linked": int,        # Number of images linked
            "not_found": int,     # Number of URLs not found in database
            "urls": List[str]     # All URLs extracted
        }
    """
    # Extract image URLs
    content_urls = extract_image_urls(content)
    all_urls = content_urls.copy()

    if cover_url:
        all_urls.append(cover_url)

    if verbose:
        print(f"📸 Found {len(all_urls)} image URLs in article")

    linked_count = 0
    not_found_count = 0

    for position, url in enumerate(all_urls, start=1):
        # Determine usage context
        is_cover = (url == cover_url)
        usage_context = "cover" if is_cover else "content"

        # Find image in database
        image = find_image_by_url(db, url)

        if not image:
            not_found_count += 1
            if verbose:
                print(f"⚠️  Image not found in DB: {url}")
            continue

        # Check if association already exists
        existing = db.execute(
            select(BlogArticleImage).where(
                BlogArticleImage.article_id == article_id,
                BlogArticleImage.image_id == image.id
            )
        ).scalar_one_or_none()

        if existing:
            # Update existing association
            existing.usage_context = usage_context
            existing.position = position if usage_context == "content" else None
        else:
            # Create new association
            assoc = BlogArticleImage(
                id=uuid4(),
                article_id=article_id,
                image_id=image.id,
                position=position if usage_context == "content" else None,
                usage_context=usage_context,
                created_at=datetime.utcnow()
            )
            db.add(assoc)

        # Update image metadata. blog_article_images is canonical; article_id is
        # kept as a legacy primary-reference field for admin/cleanup visibility.
        image.article_id = article_id
        image.is_orphan = False
        image.last_referenced_at = datetime.utcnow()
        image.marked_for_deletion_at = None  # Clear deletion mark if any

        linked_count += 1
        if verbose:
            print(f"✅ Linked image: {image.filename} ({usage_context})")

    return {
        "linked": linked_count,
        "not_found": not_found_count,
        "urls": all_urls
    }


def unlink_removed_images(
    article_id: UUID,
    current_urls: List[str],
    db: Session,
    verbose: bool = False
) -> dict:
    """
    Unlink images that were removed from article content

    Args:
        article_id: Article UUID
        current_urls: List of image URLs currently in the article
        db: Database session
        verbose: Print debug info

    Returns:
        {
            "unlinked": int,      # Number of images unlinked
            "marked_orphan": int  # Number of images marked as orphan
        }
    """
    # Get currently linked images
    stmt = (
        select(BlogArticleImage, BlogImage)
        .join(BlogImage, BlogArticleImage.image_id == BlogImage.id)
        .where(BlogArticleImage.article_id == article_id)
    )
    associations = db.execute(stmt).all()

    unlinked_count = 0
    marked_orphan_count = 0

    for assoc, image in associations:
        if not any(normalize_image_url(image.url) == normalize_image_url(url) for url in current_urls):
            # This image is no longer in the article
            if verbose:
                print(f"🗑️  Unlinking removed image: {image.filename}")

            # Delete association
            db.delete(assoc)
            unlinked_count += 1

            # Check if image is used by other articles
            other_uses = db.execute(
                select(BlogArticleImage).where(
                    BlogArticleImage.image_id == image.id,
                    BlogArticleImage.article_id != article_id
                )
            ).scalars().first()

            if not other_uses:
                # No other articles use this image - mark as orphan
                image.article_id = None
                image.is_orphan = True
                marked_orphan_count += 1
                if verbose:
                    print(f"🏴 Marked as orphan: {image.filename}")
            else:
                image.article_id = other_uses.article_id

    return {
        "unlinked": unlinked_count,
        "marked_orphan": marked_orphan_count
    }


def sync_article_images(
    article_id: UUID,
    content: str,
    cover_url: str | None,
    db: Session,
    verbose: bool = False
) -> dict:
    """
    Complete sync: link new images and unlink removed ones

    This is the main function to call when creating/updating articles.

    Args:
        article_id: Article UUID
        content: Markdown content
        cover_url: Cover image URL (optional)
        db: Database session
        verbose: Print debug info

    Returns:
        {
            "linked": int,
            "unlinked": int,
            "marked_orphan": int,
            "not_found": int
        }
    """
    # Extract current URLs
    current_urls = extract_image_urls(content)
    if cover_url:
        current_urls.append(cover_url)

    # Link new/existing images
    link_result = link_images_to_article(
        article_id,
        content,
        cover_url,
        db,
        verbose
    )

    # Unlink removed images
    unlink_result = unlink_removed_images(
        article_id,
        current_urls,
        db,
        verbose
    )

    return {
        **link_result,
        **unlink_result
    }
