"""
Database migration to add cascading deletes for user-report relationship.

This migration ensures that when a user is deleted, all their associated reports
are automatically deleted as well, preventing orphaned records.

Benefits:
- Data integrity: No orphaned reports without users
- Automatic cleanup: No need for manual cleanup scripts
- Foreign key enforcement at database level
"""

from app.database import engine
from sqlalchemy import text


def migrate():
    """Add cascading delete to user-report relationship"""
    print("[MIGRATION] Adding cascading delete for user-report relationship...")

    try:
        with engine.connect() as conn:
            # 1. Find existing foreign key constraint name
            print("[1/3] Finding existing foreign key constraint...")

            result = conn.execute(text("""
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'reports'::regclass
                AND contype = 'f'
                AND confrelid = 'users'::regclass
            """))

            existing_constraint = result.fetchone()

            if existing_constraint:
                constraint_name = existing_constraint[0]
                print(f"  ✓ Found existing constraint: {constraint_name}")

                # 2. Drop existing foreign key
                print("\n[2/3] Dropping existing foreign key constraint...")

                conn.execute(text(f"""
                    ALTER TABLE reports
                    DROP CONSTRAINT IF EXISTS {constraint_name}
                """))
                conn.commit()
                print(f"  ✓ Dropped constraint: {constraint_name}")
            else:
                print("  ⊕ No existing foreign key constraint found")

            # 3. Add new foreign key with CASCADE
            print("\n[3/3] Adding new foreign key with ON DELETE CASCADE...")

            conn.execute(text("""
                ALTER TABLE reports
                ADD CONSTRAINT reports_user_id_fkey
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
            """))
            conn.commit()
            print("  ✓ Added foreign key with ON DELETE CASCADE")

            # Verify the new constraint
            result = conn.execute(text("""
                SELECT
                    conname,
                    pg_get_constraintdef(oid) as definition
                FROM pg_constraint
                WHERE conrelid = 'reports'::regclass
                AND contype = 'f'
                AND confrelid = 'users'::regclass
            """))

            constraint_info = result.fetchone()

            if constraint_info:
                name, definition = constraint_info
                print(f"\n  ✓ Verified constraint: {name}")
                print(f"    Definition: {definition}")

                if "ON DELETE CASCADE" in definition:
                    print("    ✓ CASCADE behavior confirmed")
                else:
                    print("    ⚠ Warning: CASCADE not found in definition")

            print("\n[MIGRATION COMPLETE] ✅")
            print("Summary:")
            print("  - Removed old foreign key constraint")
            print("  - Added new foreign key with ON DELETE CASCADE")
            print("  - When a user is deleted, all their reports will be automatically deleted")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        raise


def rollback():
    """Remove cascading delete from user-report relationship"""
    print("[ROLLBACK] Removing cascading delete from user-report relationship...")

    try:
        with engine.connect() as conn:
            # Drop CASCADE foreign key
            print("[1/2] Dropping CASCADE foreign key...")

            conn.execute(text("""
                ALTER TABLE reports
                DROP CONSTRAINT IF EXISTS reports_user_id_fkey
            """))
            conn.commit()
            print("  ✓ Dropped CASCADE foreign key")

            # Add back regular foreign key (no CASCADE)
            print("\n[2/2] Adding back regular foreign key (no CASCADE)...")

            conn.execute(text("""
                ALTER TABLE reports
                ADD CONSTRAINT reports_user_id_fkey
                FOREIGN KEY (user_id)
                REFERENCES users(id)
            """))
            conn.commit()
            print("  ✓ Added regular foreign key (no CASCADE)")

            print("\n[ROLLBACK COMPLETE] ✅")
            print("Warning: Deleting users will now fail if they have associated reports")

    except Exception as e:
        print(f"[ERROR] Rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback()
    else:
        migrate()
