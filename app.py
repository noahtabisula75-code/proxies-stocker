import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fallback.db')
db = SQLAlchemy(app)

# Models
class Proxy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proxy_string = db.Column(db.String(300), unique=True, nullable=False)

class Stats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Integer)
    valid = db.Column(db.Integer)
    invalid = db.Column(db.Integer)
    clean = db.Column(db.Integer)
    not_clean = db.Column(db.Integer)
    has_codm = db.Column(db.Integer)
    no_codm = db.Column(db.Integer)

with app.app_context():
    db.create_all()

# Web dashboard
@app.route('/')
def dashboard():
    proxies = Proxy.query.all()
    total = db.session.query(db.func.sum(Stats.total)).scalar() or 0
    valid = db.session.query(db.func.sum(Stats.valid)).scalar() or 0
    invalid = db.session.query(db.func.sum(Stats.invalid)).scalar() or 0
    clean = db.session.query(db.func.sum(Stats.clean)).scalar() or 0
    not_clean = db.session.query(db.func.sum(Stats.not_clean)).scalar() or 0
    has_codm = db.session.query(db.func.sum(Stats.has_codm)).scalar() or 0
    no_codm = db.session.query(db.func.sum(Stats.no_codm)).scalar() or 0
    stats = (total, valid, invalid, clean, not_clean, has_codm, no_codm)
    return render_template('dashboard.html', proxies=proxies, stats=stats)

@app.route('/add_proxy', methods=['POST'])
def add_proxy():
    p = request.form.get('proxy_string')
    if p:
        try:
            db.session.add(Proxy(proxy_string=p))
            db.session.commit()
        except:
            db.session.rollback()
    return redirect(url_for('dashboard'))

@app.route('/delete_proxy/<int:proxy_id>')
def delete_proxy(proxy_id):
    Proxy.query.filter_by(id=proxy_id).delete()
    db.session.commit()
    return redirect(url_for('dashboard'))

# API for the checker
@app.route('/proxy/api/proxies')
def api_proxies():
    proxies = Proxy.query.all()
    return jsonify([p.proxy_string for p in proxies])

@app.route('/proxy/api/submit', methods=['POST'])
def api_submit():
    data = request.get_json()
    db.session.add(Stats(
        total=data.get('total', 0),
        valid=data.get('valid', 0),
        invalid=data.get('invalid', 0),
        clean=data.get('clean', 0),
        not_clean=data.get('not_clean', 0),
        has_codm=data.get('has_codm', 0),
        no_codm=data.get('no_codm', 0)
    ))
    db.session.commit()
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
