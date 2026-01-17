"""Add composite index for verse lookups.

This migration adds a composite index on (book_id, chapter, verse)
to significantly speed up exact verse lookups.

Run this after the database schema is created.
"""

from sqlalchemy import text

from database import SessionLocal


def upgrade():
    """Add the composite index."""
    from database import engine

    print("Adding composite index idx_verses_book_chapter_verse...")

    # Use raw connection to avoid transaction for CONCURRENT index
    with engine.connect() as conn:
        # Set autocommit mode for CONCURRENT index creation
        conn.execution_options(isolation_level="AUTOCOMMIT")

        # Check if index already exists
        result = conn.execute(
            text(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND indexname = 'idx_verses_book_chapter_verse'
                """
            )
        )

        if result.fetchone():
            print("Index already exists, skipping...")
            return

        # Create the index (CONCURRENTLY allows reads/writes during creation)
        try:
            conn.execute(
                text(
                    """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verses_book_chapter_verse
                    ON verses (book_id, chapter, verse)
                    """
                )
            )
            print("✓ Composite index created successfully!")
        except Exception as e:
            print(f"✗ Error creating index: {e}")
            # Try without CONCURRENTLY as fallback
            print("Retrying without CONCURRENTLY...")
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_verses_book_chapter_verse
                    ON verses (book_id, chapter, verse)
                    """
                )
            )
            print("✓ Composite index created successfully (non-concurrent)!")


def downgrade():
    """Remove the composite index."""
    db = SessionLocal()
    try:
        print("Removing composite index idx_verses_book_chapter_verse...")

        db.execute(
            text(
                """
                DROP INDEX IF EXISTS idx_verses_book_chapter_verse
                """
            )
        )
        db.commit()
        print("✓ Composite index removed successfully!")

    except Exception as e:
        db.rollback()
        print(f"✗ Error removing index: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
