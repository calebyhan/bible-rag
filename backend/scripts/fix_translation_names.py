"""Fix translation names in the database to match books_metadata.py."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Translation
from data.books_metadata import TRANSLATIONS


def fix_translation_names():
    """Update translation names in database to match metadata."""
    db = SessionLocal()

    try:
        # Build a mapping of abbreviation -> correct name
        correct_names = {t["abbreviation"]: t["name"] for t in TRANSLATIONS}

        print("Checking translation names in database...")

        # Get all translations from database
        db_translations = db.query(Translation).all()

        fixes_made = 0
        for trans in db_translations:
            if trans.abbreviation in correct_names:
                correct_name = correct_names[trans.abbreviation]
                if trans.name != correct_name:
                    print(f"  Fixing {trans.abbreviation}: '{trans.name}' -> '{correct_name}'")
                    trans.name = correct_name
                    fixes_made += 1
                else:
                    print(f"  {trans.abbreviation}: '{trans.name}' (OK)")
            else:
                print(f"  {trans.abbreviation}: '{trans.name}' (not in metadata)")

        if fixes_made > 0:
            db.commit()
            print(f"\nFixed {fixes_made} translation name(s)")
        else:
            print("\nNo fixes needed - all names are correct")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix_translation_names()
