import os
from flask import Flask, request, jsonify
from database import db
from models import Account, License, Device
from utils import is_valid_key, parse_expiration_date, is_account_expired
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///auth.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

ADMIN_KEY = os.getenv('ADMIN_KEY')
CLIENT_KEY = os.getenv('CLIENT_KEY')

# ---------------------------
# Initialize DB automatically
# ---------------------------
@app.before_first_request
def initialize_database():
    db.create_all()

# ---------------------------
# LOGIN ENDPOINT
# ---------------------------
@app.route('/login', methods=['GET'])
def login():
    username = request.args.get('Username')
    password = request.args.get('Password')
    client_key = request.args.get('Key')
    ip_address = request.remote_addr

    if not is_valid_key(client_key, CLIENT_KEY):
        return jsonify({"status": "failure", "reason": "invalid client key"}), 401

    account = Account.query.filter_by(username=username, password=password).first()
    if not account:
        return jsonify({"status": "failure", "reason": "account not found"}), 404
    if is_account_expired(account):
        return jsonify({"status": "failure", "reason": "account expired"}), 403

    device = Device.query.filter_by(account_id=account.id, ip_address=ip_address).first()
    if not device:
        if len(account.devices) >= account.max_users:
            return jsonify({"status": "failure", "reason": "device limit reached"}), 403
        new_device = Device(ip_address=ip_address, account_id=account.id)
        db.session.add(new_device)
        db.session.commit()

    return jsonify({
        "status": "success",
        "username": account.username,
        "created_date": account.created_date,
        "expiration_date": account.expiration_date,
        "devices": [d.ip_address for d in account.devices]
    }), 200

# ---------------------------
# SHOW ACCOUNT DETAIL
# ---------------------------
@app.route('/ShowAccountDetail', methods=['GET'])
def show_account_detail():
    username = request.args.get('Username')
    password = request.args.get('Password')
    admin_key = request.args.get('Key')

    if not is_valid_key(admin_key, ADMIN_KEY):
        return jsonify({"status": "unauthorized"}), 401

    account = Account.query.filter_by(username=username, password=password).first()
    if not account:
        return jsonify({"status": "account not found"}), 404

    devices = [{"ip": d.ip_address, "last_login": d.last_login} for d in account.devices]
    return jsonify({
        "username": account.username,
        "created_date": account.created_date,
        "expiration_date": account.expiration_date,
        "max_users": account.max_users,
        "devices": devices
    }), 200

# ---------------------------
# SHOW ALL ACCOUNTS
# ---------------------------
@app.route('/ShowAvailableAccounts', methods=['GET'])
def show_available_accounts():
    admin_key = request.args.get('Key')
    if not is_valid_key(admin_key, ADMIN_KEY):
        return jsonify({"status": "unauthorized"}), 401

    accounts = Account.query.all()
    result = []
    for acc in accounts:
        result.append({
            "account_name": f"Account{acc.id}",
            "username": acc.username,
            "expiration_date": acc.expiration_date,
            "devices": len(acc.devices)
        })
    return jsonify({"accounts": result}), 200

# ---------------------------
# DELETE ACCOUNT
# ---------------------------
@app.route('/delete', methods=['DELETE'])
def delete_account():
    account_name = request.args.get('AccountName')  # e.g., "Account1"
    admin_key = request.args.get('Key')
    
    if not is_valid_key(admin_key, ADMIN_KEY):
        return jsonify({"status": "unauthorized"}), 401

    account_id = int(account_name.replace("Account", ""))
    account = Account.query.get(account_id)
    if not account:
        return jsonify({"status": "account not found"}), 404
    
    db.session.delete(account)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200

# ---------------------------
# CREATE ACCOUNT
# ---------------------------
@app.route('/CreateAccount', methods=['POST'])
def create_account():
    username = request.args.get('Username')
    password = request.args.get('Password')
    expiration_date = request.args.get('ExpirationDate')
    max_users = int(request.args.get('MaxUser', 1))
    admin_key = request.args.get('Key')

    if not is_valid_key(admin_key, ADMIN_KEY):
        return jsonify({"status": "unauthorized"}), 401

    exp_date = parse_expiration_date(expiration_date)
    if not exp_date:
        return jsonify({"status": "invalid expiration date"}), 400

    new_account = Account(
        username=username,
        password=password,
        expiration_date=exp_date,
        max_users=max_users
    )
    db.session.add(new_account)
    db.session.commit()
    return jsonify({"status": "created", "account_name": f"Account{new_account.id}"}), 201

# ---------------------------
# CREATE LICENSE
# ---------------------------
@app.route('/CreateLicense', methods=['POST'])
def create_license():
    license_key = request.args.get('Licence')
    expiration_date = request.args.get('ExpirationDate')
    max_users = 1 if request.args.get('MAXUSER') == 'ALWAYS' else int(request.args.get('MAXUSER', 1))
    admin_key = request.args.get('AdminKey')

    if not is_valid_key(admin_key, ADMIN_KEY):
        return jsonify({"status": "unauthorized"}), 401

    exp_date = parse_expiration_date(expiration_date)
    if not exp_date:
        return jsonify({"status": "invalid expiration date"}), 400

    new_license = License(
        license_key=license_key,
        expiration_date=exp_date,
        max_users=max_users
    )
    db.session.add(new_license)
    db.session.commit()
    return jsonify({"status": "license created"}), 201

# ---------------------------
# DELETE LICENSE
# ---------------------------
@app.route('/DeleteLicense', methods=['DELETE'])
def delete_license():
    license_key = request.args.get('Licence')
    admin_key = request.args.get('Key')

    if not is_valid_key(admin_key, ADMIN_KEY):
        return jsonify({"status": "unauthorized"}), 401

    license = License.query.filter_by(license_key=license_key).first()
    if not license:
        return jsonify({"status": "license not found"}), 404
    
    db.session.delete(license)
    db.session.commit()
    return jsonify({"status": "license deleted"}), 200

# ---------------------------
# RUN APP
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
