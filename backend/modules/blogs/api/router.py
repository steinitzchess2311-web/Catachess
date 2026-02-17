"""
Blog API Router

Public Endpoints:
- GET /api/blogs/categories - Get all categories
- GET /api/blogs/articles - Get article list with pagination
- GET /api/blogs/articles/pinned - Get pinned articles
- GET /api/blogs/articles/:id - Get article detail

Management Endpoints (Editor/Admin):
- GET /api/blogs/articles/my-drafts - Get user's draft articles
- GET /api/blogs/articles/my-published - Get user's published articles
- POST /api/blogs/upload-image - Upload image
- POST /api/blogs/articles - Create article
- PUT /api/blogs/articles/:id - Update article (author or admin)
- DELETE /api/blogs/articles/:id - Delete article (author or admin)
- POST /api/blogs/articles/:id/pin - Pin/unpin article (admin only)
"""
import os
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from sqlalchemy import create_engine, select, func, and_, or_, text
from sqlalchemy.orm import Session

from modules.blogs.db.models import BlogArticle, BlogCategory
from modules.blogs.db.image_models import BlogImage
from modules.blogs.schemas import (
    CategoryResponse,
    ArticleListResponse,
    ArticleResponse,
    ArticleListItem,
    ArticleCreate,
    ArticleUpdate
)
from modules.blogs.services.cache_service import get_blog_cache, BlogCacheService
from modules.blogs.services.image_service import get_image_service
from modules.blogs.auth import require_editor, require_admin
from modules.blogs.utils.image_linker import sync_article_images

router = APIRouter(prefix="/api/blogs", tags=["Blogs"])


# ==================== Database Dependency ====================

def get_blog_db():
    """
    Get blog database session (BLOG_DATABASE_URL - 独立数据库)

    Blog articles, categories, and images use a separate database.
    User authentication queries the main database via auth.py::get_current_user.
    """
    db_url = os.getenv("BLOG_DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=500, detail="BLOG_DATABASE_URL not configured")

    engine = create_engine(db_url)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


# ==================== Categories ====================

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    cache: BlogCacheService = Depends(get_blog_cache),
    db: Session = Depends(get_blog_db)
):
    """
    Get all active categories (cached for 1 hour)

    **Public endpoint** - No authentication required
    """
    # Try cache first
    cached = await cache.get_categories()
    if cached:
        return [CategoryResponse(**item) for item in cached]

    # Query database
    stmt = (
        select(BlogCategory)
        .where(BlogCategory.is_active == True)
        .order_by(BlogCategory.order_index)
    )
    categories = db.execute(stmt).scalars().all()

    # Convert to dict for caching
    result = [
        {
            "id": str(cat.id),
            "name": cat.name,
            "display_name": cat.display_name,
            "description": cat.description,
            "icon": cat.icon,
            "order_index": cat.order_index,
            "is_active": cat.is_active,
            "created_at": cat.created_at.isoformat(),
        }
        for cat in categories
    ]

    # Cache for 1 hour
    await cache.set_categories(result)

    return [CategoryResponse(**item) for item in result]


# ==================== Article List ====================

@router.get("/articles", response_model=ArticleListResponse)
async def get_articles(
    category: Optional[str] = Query(None, description="Filter by category (about/function/allblogs/user)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title/content"),
    year: Optional[int] = Query(None, ge=2020, le=2100, description="Filter by year (e.g., 2024)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month (1-12, requires year)"),
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    cache: BlogCacheService = Depends(get_blog_cache),
    db: Session = Depends(get_blog_db)
):
    """
    Get article list with pagination (cached for 5 minutes)

    **Public endpoint** - No authentication required

    **Filters:**
    - category: Filter by category name
    - search: Full-text search in title and content
    - year: Filter by publication year (e.g., 2024)
    - month: Filter by publication month (1-12, must specify year)
    - start_date: Filter from date (YYYY-MM-DD format)
    - end_date: Filter to date (YYYY-MM-DD format)

    **Time filtering examples:**
    - `/articles?year=2024` - All articles in 2024
    - `/articles?year=2024&month=3` - All articles in March 2024
    - `/articles?start_date=2024-01-01&end_date=2024-12-31` - Custom date range

    **Returns:**
    - Pinned articles appear first
    - Then sorted by published_at DESC
    - Hidden articles are excluded
    """
    # Build cache key with time filters
    cache_key_parts = [category or "all"]
    if year:
        cache_key_parts.append(f"y{year}")
    if month:
        cache_key_parts.append(f"m{month}")
    if start_date:
        cache_key_parts.append(f"s{start_date}")
    if end_date:
        cache_key_parts.append(f"e{end_date}")
    cache_key = "_".join(cache_key_parts)

    # Try cache first (only for non-search queries)
    if not search:
        cached = await cache.get_article_list(cache_key, page)
        if cached:
            return ArticleListResponse(**cached)

    # Build query - exclude hidden articles
    stmt = select(BlogArticle).where(
        and_(
            BlogArticle.status == "published",
            BlogArticle.is_hidden == False
        )
    )

    # Filter by category
    if category and category != "allblogs":
        stmt = stmt.where(BlogArticle.category == category)

    # Time filtering by year/month
    if year:
        if month:
            # Specific month in year
            import calendar
            from datetime import datetime
            _, last_day = calendar.monthrange(year, month)
            month_start = datetime(year, month, 1)
            month_end = datetime(year, month, last_day, 23, 59, 59)
            stmt = stmt.where(
                and_(
                    BlogArticle.published_at >= month_start,
                    BlogArticle.published_at <= month_end
                )
            )
        else:
            # Entire year
            from datetime import datetime
            year_start = datetime(year, 1, 1)
            year_end = datetime(year, 12, 31, 23, 59, 59)
            stmt = stmt.where(
                and_(
                    BlogArticle.published_at >= year_start,
                    BlogArticle.published_at <= year_end
                )
            )

    # Time filtering by custom date range
    if start_date:
        from datetime import datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        stmt = stmt.where(BlogArticle.published_at >= start_dt)
    if end_date:
        from datetime import datetime
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        # Include the entire end date (23:59:59)
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        stmt = stmt.where(BlogArticle.published_at <= end_dt)

    # Search
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                BlogArticle.title.ilike(search_pattern),
                BlogArticle.content.ilike(search_pattern)
            )
        )

    # Order by pinned first, then by published date
    stmt = stmt.order_by(
        BlogArticle.is_pinned.desc(),
        BlogArticle.pin_order.desc(),
        BlogArticle.published_at.desc()
    )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar()

    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    articles = db.execute(stmt).scalars().all()

    # Build response
    items = [
        ArticleListItem(
            id=article.id,
            title=article.title,
            subtitle=article.subtitle,
            cover_image_url=article.cover_image_url,
            author_name=article.author_name,
            author_type=article.author_type,
            category=article.category,
            tags=article.tags,
            is_pinned=article.is_pinned,
            view_count=article.view_count,
            like_count=article.like_count,
            comment_count=article.comment_count,
            created_at=article.created_at,
            published_at=article.published_at,
        )
        for article in articles
    ]

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    result = {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

    # Cache result (only for non-search queries)
    if not search:
        await cache.set_article_list(cache_key, page, result)

    return ArticleListResponse(**result)


# ==================== Pinned Articles ====================

@router.get("/articles/pinned", response_model=List[ArticleListItem])
async def get_pinned_articles(
    cache: BlogCacheService = Depends(get_blog_cache),
    db: Session = Depends(get_blog_db)
):
    """
    Get all pinned articles (cached for 5 minutes)

    **Public endpoint** - No authentication required
    """
    # Try cache first
    cached = await cache.get_pinned_articles()
    if cached:
        return [ArticleListItem(**item) for item in cached]

    # Query database - exclude hidden articles
    stmt = (
        select(BlogArticle)
        .where(and_(
            BlogArticle.status == "published",
            BlogArticle.is_pinned == True,
            BlogArticle.is_hidden == False
        ))
        .order_by(BlogArticle.pin_order.desc(), BlogArticle.published_at.desc())
    )

    articles = db.execute(stmt).scalars().all()

    # Convert to list
    result = [
        {
            "id": str(article.id),
            "title": article.title,
            "subtitle": article.subtitle,
            "cover_image_url": article.cover_image_url,
            "author_name": article.author_name,
            "author_type": article.author_type,
            "category": article.category,
            "tags": article.tags,
            "is_pinned": article.is_pinned,
            "view_count": article.view_count,
            "like_count": article.like_count,
            "comment_count": article.comment_count,
            "created_at": article.created_at.isoformat(),
            "published_at": article.published_at.isoformat() if article.published_at else None,
        }
        for article in articles
    ]

    # Cache for 5 minutes
    await cache.set_pinned_articles(result)

    return [ArticleListItem(**item) for item in result]


# ==================== My Drafts (Editor/Admin) ====================

@router.get("/articles/my-drafts", response_model=List[ArticleListItem])
async def get_my_drafts(
    current_user = Depends(require_editor),
    db: Session = Depends(get_blog_db)
):
    """
    Get current user's draft articles (Editor/Admin only)

    **Requires:** editor or admin role

    **Returns:** List of user's draft articles (status='draft')
    """
    # Query user's drafts
    stmt = (
        select(BlogArticle)
        .where(and_(
            BlogArticle.author_id == current_user.id,
            BlogArticle.status == "draft"
        ))
        .order_by(BlogArticle.updated_at.desc())
    )

    drafts = db.execute(stmt).scalars().all()

    # Convert to list
    return [
        ArticleListItem(
            id=article.id,
            title=article.title,
            subtitle=article.subtitle,
            cover_image_url=article.cover_image_url,
            author_name=article.author_name,
            author_type=article.author_type,
            category=article.category,
            tags=article.tags,
            is_pinned=article.is_pinned,
            view_count=article.view_count,
            like_count=article.like_count,
            comment_count=article.comment_count,
            created_at=article.created_at,
            published_at=article.published_at,
        )
        for article in drafts
    ]


# ==================== My Published Articles (Editor/Admin) ====================

@router.get("/articles/my-published", response_model=List[ArticleListItem])
async def get_my_published(
    current_user = Depends(require_editor),
    db: Session = Depends(get_blog_db)
):
    """
    Get current user's published articles (Editor/Admin only)

    **Requires:** editor or admin role

    **Returns:** List of user's published articles (status='published')
    """
    # Query user's published articles
    stmt = (
        select(BlogArticle)
        .where(and_(
            BlogArticle.author_id == current_user.id,
            BlogArticle.status == "published"
        ))
        .order_by(BlogArticle.updated_at.desc())
    )

    published = db.execute(stmt).scalars().all()

    # Convert to list
    return [
        ArticleListItem(
            id=article.id,
            title=article.title,
            subtitle=article.subtitle,
            cover_image_url=article.cover_image_url,
            author_name=article.author_name,
            author_type=article.author_type,
            category=article.category,
            tags=article.tags,
            is_pinned=article.is_pinned,
            view_count=article.view_count,
            like_count=article.like_count,
            comment_count=article.comment_count,
            created_at=article.created_at,
            published_at=article.published_at,
        )
        for article in published
    ]


# ==================== Article Detail ====================

@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: UUID,
    cache: BlogCacheService = Depends(get_blog_cache),
    db: Session = Depends(get_blog_db)
):
    """
    Get article detail by ID (cached for 10 minutes)

    **Public endpoint** - No authentication required

    **Side effect:** Increments view count
    """
    # Try cache first
    cached = await cache.get_article(str(article_id))
    if cached:
        # Increment view count in background
        await cache.increment_view(str(article_id))
        return ArticleResponse(**cached)

    # Query database
    stmt = select(BlogArticle).where(BlogArticle.id == article_id)
    article = db.execute(stmt).scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if article.status != "published":
        raise HTTPException(status_code=404, detail="Article not published")

    if article.is_hidden:
        raise HTTPException(status_code=404, detail="Article not found")

    # Convert to dict
    result = {
        "id": str(article.id),
        "title": article.title,
        "subtitle": article.subtitle,
        "content": article.content,
        "cover_image_url": article.cover_image_url,
        "author_id": str(article.author_id) if article.author_id else None,
        "author_name": article.author_name,
        "author_type": article.author_type,
        "category": article.category,
        "sub_category": article.sub_category,
        "tags": article.tags,
        "status": article.status,
        "is_pinned": article.is_pinned,
        "pin_order": article.pin_order,
        "view_count": article.view_count,
        "like_count": article.like_count,
        "comment_count": article.comment_count,
        "created_at": article.created_at.isoformat(),
        "updated_at": article.updated_at.isoformat(),
        "published_at": article.published_at.isoformat() if article.published_at else None,
    }

    # Cache for 10 minutes
    await cache.set_article(str(article_id), result)

    # Increment view count
    await cache.increment_view(str(article_id))

    return ArticleResponse(**result)


# ==================== Cache Stats (Debug) ====================

@router.get("/cache/stats")
async def get_cache_stats(cache: BlogCacheService = Depends(get_blog_cache)):
    """Get cache statistics (for monitoring)"""
    return await cache.get_cache_stats()


# ==================== Image Upload (Editor/Admin) ====================

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    resize_mode: str = Form("adaptive_width", pattern="^(original|adaptive_width)$"),
    image_type: str = Form("content", pattern="^(cover|content)$"),
    current_user = Depends(require_editor),
    db: Session = Depends(get_blog_db)
):
    """
    Upload image for blog article (Editor/Admin only)

    **Parameters:**
    - file: Image file (max 5MB)
    - resize_mode: "original" or "adaptive_width"
    - image_type: "cover" or "content"

    **Returns:**
    - Image metadata with CDN URL
    """
    try:
        # Step 1: Read file data
        print(f"📤 [Upload] Starting upload for file: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
        file_data = await file.read()
        print(f"📤 [Upload] File read successfully, data size: {len(file_data)} bytes")

        # Step 2: Process and upload to R2
        print(f"📤 [Upload] Processing image with resize_mode: {resize_mode}")
        image_service = get_image_service()
        result = image_service.process_and_upload(
            file_data,
            file.filename,
            resize_mode
        )
        print(f"📤 [Upload] Image uploaded to R2: {result['url']}")

        # Step 3: Save metadata to database
        print(f"📤 [Upload] Saving metadata to database")
        blog_image = BlogImage(
            id=uuid4(),
            filename=result["filename"],
            storage_path=result["storage_path"],
            url=result["url"],
            content_type=result["content_type"],
            size_bytes=result["size_bytes"],
            width=result["width"],
            height=result["height"],
            resize_mode=result["resize_mode"],
            image_type=image_type,
            uploaded_by=current_user.id if current_user else None,
            created_at=datetime.utcnow()
        )
        db.add(blog_image)
        db.commit()
        print(f"✅ [Upload] Image saved successfully: {blog_image.id}")

        return {
            "id": str(blog_image.id),
            "url": blog_image.url,
            "filename": blog_image.filename,
            "size_bytes": blog_image.size_bytes,
            "width": blog_image.width,
            "height": blog_image.height,
            "resize_mode": blog_image.resize_mode,
            "image_type": blog_image.image_type
        }

    except ValueError as e:
        import traceback
        error_detail = f"Validation error: {str(e)}"
        print(f"❌ [Upload] {error_detail}")
        print(f"❌ [Upload] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        import traceback
        error_detail = f"Upload failed: {type(e).__name__}: {str(e)}"
        traceback_str = traceback.format_exc()
        print(f"❌ [Upload] {error_detail}")
        print(f"❌ [Upload] Full traceback:\n{traceback_str}")
        # Return detailed error to frontend for debugging
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_detail,
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback_str.split('\n')[-10:]  # Last 10 lines
            }
        )


# ==================== Article Management (Editor/Admin) ====================

@router.post("/articles", response_model=ArticleResponse)
async def create_article(
    article: ArticleCreate,
    current_user = Depends(require_editor),
    cache: BlogCacheService = Depends(get_blog_cache),
    db: Session = Depends(get_blog_db)
):
    """
    Create new article (Editor/Admin only)

    **Requires:** editor or admin role
    """
    # Create article
    new_article = BlogArticle(
        id=uuid4(),
        title=article.title,
        subtitle=article.subtitle,
        content=article.content,
        cover_image_url=article.cover_image_url,
        author_id=current_user.id if current_user else None,
        author_name=article.author_name,
        author_type=article.author_type,
        category=article.category,
        sub_category=article.sub_category,
        tags=article.tags,
        status=article.status,
        is_pinned=article.is_pinned,
        pin_order=article.pin_order,
        view_count=0,
        like_count=0,
        comment_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        published_at=datetime.utcnow() if article.status == "published" else None
    )

    db.add(new_article)
    db.commit()
    db.refresh(new_article)

    # Link images to article
    try:
        sync_result = sync_article_images(
            article_id=new_article.id,
            content=article.content,
            cover_url=article.cover_image_url,
            db=db,
            verbose=False
        )
        print(f"✅ Linked {sync_result['linked']} images to new article")
    except Exception as e:
        print(f"⚠️  Failed to link images: {e}")

    # Invalidate caches
    await cache.invalidate_article_list(article.category)
    await cache.invalidate_article_list("all")
    if article.is_pinned:
        await cache.invalidate_pinned_articles()
    await cache.invalidate_categories()

    # Return response
    return ArticleResponse.model_validate(new_article)


@router.put("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: UUID,
    updates: ArticleUpdate,
    current_user = Depends(require_editor),
    cache: BlogCacheService = Depends(get_blog_cache),
    db: Session = Depends(get_blog_db)
):
    """
    Update article (Editor/Admin only)

    **Requires:** editor or admin role

    **Permission:**
    - Users can only edit their own articles
    - Admins can edit any article
    """
    # Find article
    stmt = select(BlogArticle).where(BlogArticle.id == article_id)
    article = db.execute(stmt).scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Permission check: only article author or admin can edit
    if current_user.role != "admin" and article.author_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only edit your own articles"
        )

    # Track if category or pin status changed
    old_category = article.category
    old_is_pinned = article.is_pinned

    # Update fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)

    # Update timestamps
    article.updated_at = datetime.utcnow()
    if updates.status == "published" and not article.published_at:
        article.published_at = datetime.utcnow()

    db.commit()
    db.refresh(article)

    # Re-sync images if content or cover changed
    if updates.content is not None or updates.cover_image_url is not None:
        try:
            sync_result = sync_article_images(
                article_id=article.id,
                content=article.content,
                cover_url=article.cover_image_url,
                db=db,
                verbose=False
            )
            print(f"✅ Synced images: linked={sync_result['linked']}, unlinked={sync_result['unlinked']}")
        except Exception as e:
            print(f"⚠️  Failed to sync images: {e}")

    # Invalidate caches
    await cache.invalidate_article(str(article_id))
    await cache.invalidate_article_list(old_category)
    if updates.category and updates.category != old_category:
        await cache.invalidate_article_list(updates.category)
    await cache.invalidate_article_list("all")
    if old_is_pinned or article.is_pinned:
        await cache.invalidate_pinned_articles()

    return ArticleResponse.model_validate(article)


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: UUID,
    current_user = Depends(require_editor),
    cache: BlogCacheService = Depends(get_blog_cache),
    db: Session = Depends(get_blog_db)
):
    """
    Delete article (Editor/Admin)

    **Permission:**
    - Users can only delete their own articles
    - Admins can delete any article
    """
    # Find article
    stmt = select(BlogArticle).where(BlogArticle.id == article_id)
    article = db.execute(stmt).scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Permission check: only article author or admin can delete
    if current_user.role != "admin" and article.author_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own articles"
        )

    category = article.category
    is_pinned = article.is_pinned

    # Delete article
    db.delete(article)
    db.commit()

    # Invalidate caches
    await cache.invalidate_article(str(article_id))
    await cache.invalidate_article_list(category)
    await cache.invalidate_article_list("all")
    if is_pinned:
        await cache.invalidate_pinned_articles()

    return {"success": True, "message": "Article deleted successfully"}


@router.post("/articles/{article_id}/pin")
async def toggle_pin_article(
    article_id: UUID,
    pin_order: int = 0,
    current_user = Depends(require_admin),
    cache: BlogCacheService = Depends(get_blog_cache),
    db: Session = Depends(get_blog_db)
):
    """
    Pin or unpin article (Admin only)

    **Requires:** admin role

    **Parameters:**
    - pin_order: Order for pinned article (higher = appears first). Set to 0 to unpin.
    """

    # Find article
    stmt = select(BlogArticle).where(BlogArticle.id == article_id)
    article = db.execute(stmt).scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Toggle pin
    if pin_order > 0:
        article.is_pinned = True
        article.pin_order = pin_order
        message = f"Article pinned with order {pin_order}"
    else:
        article.is_pinned = False
        article.pin_order = 0
        message = "Article unpinned"

    article.updated_at = datetime.utcnow()
    db.commit()

    # Invalidate caches
    await cache.invalidate_article(str(article_id))
    await cache.invalidate_article_list(article.category)
    await cache.invalidate_article_list("all")
    await cache.invalidate_pinned_articles()

    return {
        "success": True,
        "message": message,
        "is_pinned": article.is_pinned,
        "pin_order": article.pin_order
    }


@router.post("/articles/{article_id}/hide")
async def toggle_hide_article(
    article_id: UUID,
    hide: bool = True,
    current_user = Depends(require_admin),
    cache: BlogCacheService = Depends(get_blog_cache),
    db: Session = Depends(get_blog_db)
):
    """
    Hide or unhide article (Admin only)

    **Requires:** admin role

    **Parameters:**
    - hide: true to hide, false to unhide (default: true)

    **Description:**
    Hidden articles are not deleted from the database but are invisible
    to regular users. They won't appear in:
    - Article lists (/articles)
    - Category views
    - Search results
    - Pinned articles

    Only admins can access hidden articles through the admin dashboard.
    """

    # Find article
    stmt = select(BlogArticle).where(BlogArticle.id == article_id)
    article = db.execute(stmt).scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Update hidden status
    article.is_hidden = hide
    article.updated_at = datetime.utcnow()
    db.commit()

    message = "Article hidden" if hide else "Article visible"

    # Invalidate caches
    await cache.invalidate_article(str(article_id))
    await cache.invalidate_article_list(article.category)
    await cache.invalidate_article_list("all")
    if article.is_pinned:
        await cache.invalidate_pinned_articles()

    return {
        "success": True,
        "message": message,
        "is_hidden": article.is_hidden
    }


@router.get("/debug/r2-config")
async def debug_r2_config(
    current_user = Depends(require_admin)
):
    """
    Debug endpoint to check R2 configuration (Admin only)

    Returns R2 configuration status and environment variables (redacted)
    """
    import os
    from modules.blogs.services.image_service import get_image_service

    try:
        # Check the actual variables that image_service.py reads
        r2_blog_access_key = os.getenv("R2_BLOG_ACCESS_KEY")
        r2_blog_secret_key = os.getenv("R2_BLOG_SECRET_KEY")
        r2_endpoint = os.getenv("R2_ENDPOINT")
        r2_blog_bucket = os.getenv("R2_BLOG_BUCKET")
        r2_cdn_url = os.getenv("R2_CDN_URL")

        config = {
            "R2_BLOG_ACCESS_KEY": "✓ Set" if r2_blog_access_key else "✗ Missing",
            "R2_BLOG_SECRET_KEY": "✓ Set" if r2_blog_secret_key else "✗ Missing",
            "R2_ENDPOINT": r2_endpoint if r2_endpoint else "✗ Missing",
            "R2_BLOG_BUCKET": r2_blog_bucket if r2_blog_bucket else "✗ Missing (will default to 'Blog-Photo')",
            "R2_CDN_URL": r2_cdn_url if r2_cdn_url else "✗ Missing (will fallback to R2_ENDPOINT)",
        }

        missing = [k for k, v in config.items() if "✗" in str(v)]
        all_required_set = not any("✗" in str(v) for v in [
            config["R2_BLOG_ACCESS_KEY"],
            config["R2_BLOG_SECRET_KEY"],
            config["R2_ENDPOINT"],
        ])

        # Try a real connection to R2
        connection_test = None
        if all_required_set:
            try:
                import boto3
                s3 = boto3.client(
                    "s3",
                    endpoint_url=r2_endpoint,
                    aws_access_key_id=r2_blog_access_key,
                    aws_secret_access_key=r2_blog_secret_key,
                    region_name="auto",
                )
                bucket = r2_blog_bucket or "Blog-Photo"
                s3.head_bucket(Bucket=bucket)
                connection_test = f"✓ Connected to bucket '{bucket}'"
            except Exception as e:
                connection_test = f"✗ Connection failed: {type(e).__name__}: {str(e)}"
        else:
            connection_test = "✗ Skipped (missing required variables)"

        return {
            "status": "success" if all_required_set else "misconfigured",
            "config": config,
            "connection_test": connection_test,
            "missing_variables": missing,
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
