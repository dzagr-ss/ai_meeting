#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from database import SessionLocal
import models
import crud
import schemas

def test_tags():
    db = SessionLocal()
    
    try:
        print("Testing tags functionality...")
        
        # Create a test tag
        tag_data = schemas.TagCreate(name="test meeting", color="#ff5722")
        tag = crud.create_tag(db, tag_data)
        print(f"Created tag: {tag.name} (ID: {tag.id})")
        
        # Create another tag
        tag_data2 = schemas.TagCreate(name="project planning", color="#4caf50")
        tag2 = crud.create_tag(db, tag_data2)
        print(f"Created tag: {tag2.name} (ID: {tag2.id})")
        
        # Get all tags
        all_tags = crud.get_tags(db)
        print(f"Total tags: {len(all_tags)}")
        for t in all_tags:
            print(f"  - {t.name} ({t.color})")
        
        # Test creating tags from names
        tag_names = ["weekly sync", "budget review", "client meeting"]
        created_tags = crud.create_tags_from_names(db, tag_names)
        print(f"Created {len(created_tags)} tags from names")
        
        print("Tags functionality test completed successfully!")
        
    except Exception as e:
        print(f"Error testing tags: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_tags() 