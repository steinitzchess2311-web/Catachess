"""
Created at: 2026-07-09 01:05 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:58 EDT
Last Modified by: Codex

Tests for blog image URL extraction and article-image relationship syncing.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from core.db.base import Base
from modules.blogs.db.image_models import BlogImage
from modules.blogs.db.models import BlogArticleImage
from modules.blogs.utils.image_linker import extract_image_urls, find_image_by_url, sync_article_images


def _make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[BlogImage.__table__, BlogArticleImage.__table__])
    return Session(engine)


def _image(url: str, image_type: str = "content") -> BlogImage:
    return BlogImage(
        id=uuid4(),
        filename="space image.webp",
        storage_path="blog/2026/07/space image.webp",
        url=url,
        content_type="image/webp",
        size_bytes=100,
        width=320,
        height=180,
        resize_mode="adaptive_width",
        image_type=image_type,
        uploaded_by=None,
        article_id=None,
        is_orphan=True,
        marked_for_deletion_at=None,
        created_at=datetime.utcnow(),
        last_referenced_at=None,
    )


def test_extract_image_urls_preserves_order_and_deduplicates():
    content = "A ![one](https://cdn.test/a.webp) B ![two](https://cdn.test/b.webp) C ![again](https://cdn.test/a.webp)"

    assert extract_image_urls(content) == [
        "https://cdn.test/a.webp",
        "https://cdn.test/b.webp",
    ]


def test_find_image_by_url_matches_encoded_and_unencoded_variants():
    db = _make_session()
    image = _image("https://cdn.test/blog/2026/07/space%20image.webp")
    db.add(image)
    db.commit()

    found = find_image_by_url(db, "https://cdn.test/blog/2026/07/space image.webp")

    assert found is not None
    assert found.id == image.id


def test_find_image_by_url_tolerates_duplicate_legacy_variants():
    db = _make_session()
    encoded = _image("https://cdn.test/blog/2026/07/space%20image.webp")
    plain = _image("https://cdn.test/blog/2026/07/space image.webp")
    db.add_all([encoded, plain])
    db.commit()

    found = find_image_by_url(db, "https://cdn.test/blog/2026/07/space image.webp")

    assert found is not None
    assert found.id in {encoded.id, plain.id}


def test_sync_article_images_links_cover_and_marks_removed_content_orphan():
    db = _make_session()
    article_id = uuid4()
    cover = _image("https://cdn.test/blog/cover.webp", "cover")
    content = _image("https://cdn.test/blog/content.webp", "content")
    removed = _image("https://cdn.test/blog/removed.webp", "content")
    db.add_all([cover, content, removed])
    db.commit()

    sync_article_images(
        article_id=article_id,
        content="![kept](https://cdn.test/blog/content.webp) ![old](https://cdn.test/blog/removed.webp)",
        cover_url="https://cdn.test/blog/cover.webp",
        db=db,
    )
    sync_article_images(
        article_id=article_id,
        content="![kept](https://cdn.test/blog/content.webp)",
        cover_url="https://cdn.test/blog/cover.webp",
        db=db,
    )
    db.commit()

    links = db.query(BlogArticleImage).filter(BlogArticleImage.article_id == article_id).all()
    assert {link.usage_context for link in links} == {"content", "cover"}
    assert cover.is_orphan is False
    assert content.is_orphan is False
    assert removed.is_orphan is True


def test_sync_article_images_keeps_shared_removed_image_referenced():
    db = _make_session()
    article_id = uuid4()
    other_article_id = uuid4()
    third_article_id = uuid4()
    shared = _image("https://cdn.test/blog/shared.webp", "content")
    db.add(shared)
    db.commit()

    sync_article_images(
        article_id=article_id,
        content="![shared](https://cdn.test/blog/shared.webp)",
        cover_url=None,
        db=db,
    )
    db.add_all([
        BlogArticleImage(id=uuid4(), article_id=other_article_id, image_id=shared.id, usage_context="content"),
        BlogArticleImage(id=uuid4(), article_id=third_article_id, image_id=shared.id, usage_context="content"),
    ])
    db.commit()

    sync_article_images(
        article_id=article_id,
        content="",
        cover_url=None,
        db=db,
    )
    db.commit()

    assert shared.is_orphan is False
    assert shared.article_id in {other_article_id, third_article_id}
