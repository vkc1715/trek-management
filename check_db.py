import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.index import create_app
from models import db, Trek

app = create_app()

with app.app_context():
    difficulties = db.session.query(Trek.difficulty).distinct().all()
    statuses = db.session.query(Trek.status).distinct().all()
    print("Difficulties:", [d[0] for d in difficulties])
    print("Statuses:", [s[0] for s in statuses])
