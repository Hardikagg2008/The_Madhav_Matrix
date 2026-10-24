from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logic # This imports your teammate's logic.py file

app = Flask(__name__)

# 1. Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///streetsignal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 2. The Model
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    group_id = db.Column(db.Integer, nullable=True) # Links complaints to a group
    department = db.Column(db.String(100), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template('index.html', complaints=complaints)

@app.route('/submit', methods=['POST'])
def submit():
    text = request.form.get('complaint')
    if text:
        # --- AI INTEGRATION START ---
        
        # 1. Get all existing complaint texts for the AI to compare against
        all_complaints = Complaint.query.all()
        existing_texts = [c.text for c in all_complaints]
        
        # 2. Use logic.py to find a match
        match_text = logic.group_complaints(text, existing_texts)
        
        group_id = None
        if match_text:
            # Find the ID of the original complaint that matched
            original = Complaint.query.filter_by(text=match_text).first()
            if original:
                group_id = original.id
        
        # 3. Use logic.py to suggest a department
        dept = logic.suggest_department(text)
        
        # --- AI INTEGRATION END ---

        new_complaint = Complaint(text=text, group_id=group_id, department=dept)
        db.session.add(new_complaint)
        db.session.commit()
        
        # If this was a new issue, its own ID becomes the group_id for future matches
        if group_id is None:
            new_complaint.group_id = new_complaint.id
            db.session.commit()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True,port=5001)
