#!/usr/bin/env python3
"""
Cleanup script to remove transcription records with empty text fields
"""
import sys
sys.path.append('backend')

try:
    from database import SessionLocal
    import models
    
    db = SessionLocal()
    try:
        # Find and delete transcriptions with empty text
        empty_transcriptions = db.query(models.Transcription).filter(
            (models.Transcription.text == '') | 
            (models.Transcription.text.is_(None))
        ).all()
        
        print(f'Found {len(empty_transcriptions)} transcriptions with empty text')
        
        for t in empty_transcriptions:
            print(f'Deleting transcription ID {t.id}: speaker="{t.speaker}", text="{t.text}"')
            db.delete(t)
        
        db.commit()
        print('Cleanup completed successfully')
        
    except Exception as e:
        print(f'Error during cleanup: {e}')
        db.rollback()
    finally:
        db.close()
        
except ImportError as e:
    print(f'Database not available: {e}')
    print('This is expected in lightweight mode')
except Exception as e:
    print(f'Unexpected error: {e}') 