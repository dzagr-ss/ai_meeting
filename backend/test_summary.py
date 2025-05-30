import sys
sys.path.append('.')
from database import SessionLocal
from models import Summary
from datetime import datetime

db = SessionLocal()
test_summary = Summary(
    meeting_id=2,
    content='This is a test summary for meeting 2. It contains key discussion points and action items from the meeting.',
    generated_at=datetime.utcnow()
)
db.add(test_summary)
db.commit()
print('Test summary created successfully')
db.close() 