from util import create_response
from flask import Blueprint, jsonify, request, g
from werkzeug import exceptions
from model import Wallet, WalletHistory, WalletHistoryType, IsReferenceIDEverUse
from __init__ import db
import auth

init_blueprint = Blueprint('init_blueprint', 'init_blueprint', url_prefix='/api/v1/init')

@init_blueprint.route('', methods=["POST"])
def init():
    # Get customer xid
    customer_xid = request.form.get('customer_xid')

    # Check is customer xid exists
    if not customer_xid:
        return jsonify(create_response("fail", {"error": {"customer_xid": ["Missing data for required field."]}})), 401
    
    # Check is wallet already exists 
    wallet = Wallet.query.filter(Wallet.owned_by == customer_xid).first()
    if not wallet:
        # Create new wallet
        wallet = Wallet(customer_xid)

    # Create token
    token = auth.encode_auth_token(customer_xid)
    return jsonify(create_response("success", {"token": token}))
    
wallet_blueprint = Blueprint('wallet_blueprint', 'wallet_blueprint', url_prefix='/api/v1/wallet')

# define wallet_blueprint middleware/hook
@wallet_blueprint.before_request
def get_customer_xid():
    # Get auth header
    auth_header = request.headers.get('Authorization')
    if auth_header:
        # get token and its name
        token = auth_header.split(" ")[:2]
    else:
        return jsonify(create_response("fail", {"error": "No header found"})), 401

    # Check token name
    if token[0] != "Token":
        return jsonify(create_response("fail", {"error": "Token must be something like Token w623t7e..."})), 401
    # 
    if not token[1]:
        return jsonify(create_response("fail", {"error": "Token is empty"})), 401

    customer_xid = auth.decode_auth_token(token[1])
    if customer_xid == 'expired':
        print("pass this")
        return jsonify(create_response("fail", {"error": "Token is expired"})), 401
    if customer_xid == 'invalid':
        return jsonify(create_response("fail", {"error": "Token is invalid"})), 401
    g.customer_xid = customer_xid


@wallet_blueprint.route('', methods=["POST"])
def enable():
    # Check is wallet exists 
    wallet = Wallet.query.filter(Wallet.owned_by == g.customer_xid).first()
    if not wallet:
        return jsonify(create_response("fail", {"error": "No wallet data found"})), 401

    # Check is wallet already enabled
    if wallet.is_enabled():
        return jsonify(create_response("fail", {"error": "Already enabled"})), 401

    # Enabled wallet
    wallet.enable()

    # Make response
    wallet = wallet.to_dict()
    del wallet['disabled_at']

    return jsonify(create_response("success", {"wallet": wallet}))

@wallet_blueprint.route('', methods=["GET"])
def view():
    # Check is wallet exists 
    wallet = Wallet.query.filter(Wallet.owned_by == g.customer_xid).first()
    if not wallet:
        return jsonify(create_response("fail", {"error": "No wallet data found"})), 401
    
    # Check is wallet disabled
    if not wallet.is_enabled():
        return jsonify(create_response("fail", {"error": "Wallet is disabled"})), 401

    wallet = wallet.to_dict()
    del wallet['disabled_at']

    return jsonify(create_response("success", {"wallet": wallet}))

@wallet_blueprint.route('/deposits', methods=["POST"])
def deposit():
    # Check is wallet exists 
    wallet = Wallet.query.filter(Wallet.owned_by == g.customer_xid).first()
    if not wallet:
        return jsonify(create_response("fail", {"error": "No wallet data found"})), 401

    # Check is wallet disabled
    if not wallet.is_enabled():
        return jsonify(create_response("fail", {"error": "Wallet is disabled"})), 401

    # Define error
    error = []

    # Get ammount
    amount = request.form.get("amount")
    if not amount:
        error.append("Require amount form data")
    amount = int(amount)

    # Get reference id
    reference_id = request.form.get("reference_id")
    if not reference_id:
        error.append("Require reference id form data")
    
    # Check error
    if len(error)>0:
        return jsonify(create_response("fail", {"error": error})), 401

    # Check is reference id has been used before
    if IsReferenceIDEverUse(reference_id, "deposit"):
        return jsonify(create_response("fail", {"error": "reference id has been used before"})), 401
    
    # Get balance before
    balance_before = wallet.balance
    wallet.balance += amount

    # Get balance after
    balance_after = wallet.balance

    # Create wallet history
    wallet_history = WalletHistory(reference_id, wallet.id, WalletHistoryType.debit, amount, balance_before, balance_after)
    db.session.add(wallet_history)
    db.session.commit()

    wallet_history = wallet_history.parse_to_dict(wallet.owned_by)

    return jsonify(create_response("success", {"deposit": wallet_history}))


@wallet_blueprint.route('/withdrawals', methods=["POST"])
def withdrawal():
    # Check is wallet exists 
    wallet = Wallet.query.filter(Wallet.owned_by == g.customer_xid).first()
    if not wallet:
        return jsonify(create_response("fail", {"error": "No wallet data found"})), 401
    
    # Check is wallet disabled
    if not wallet.is_enabled():
        return jsonify(create_response("fail", {"error": "Wallet is disabled"})), 401


    # Define error
    error = []

    # Get ammount
    amount = request.form.get("amount")
    if not amount:
        error.append("Require amount form data")
    amount = int(amount)

    # Get reference id
    reference_id = request.form.get("reference_id")
    if not reference_id:
        error.append("Require reference id form data")
    
    # Check error
    if len(error)>0:
        return jsonify(create_response("fail", {"error": error})), 401

    # Check is reference id has been used before
    if IsReferenceIDEverUse(reference_id, "withdrawal"):
        return jsonify(create_response("fail", {"error": "reference id has been used before"})), 401
    # Get balance before
    balance_before = wallet.balance
    wallet.balance -= amount

    # Get balance after
    balance_after = wallet.balance

    # Create wallet history
    wallet_history = WalletHistory(reference_id, wallet.id, WalletHistoryType.credit, amount, balance_before, balance_after)
    db.session.add(wallet_history)
    db.session.commit()

    wallet_history = wallet_history.parse_to_dict(wallet.owned_by)

    return jsonify(create_response("success", {"deposit": wallet_history}))

@wallet_blueprint.route('', methods=["PATCH"])
def disable():
    is_disabled = request.form.get("is_disabled")
    if not is_disabled:
        return jsonify(create_response("fail", {"error": "Require is_disabled form data"})), 401

    # Check is desable not equal to false and true
    if is_disabled != "false" and is_disabled != "true":
        return jsonify(create_response("fail", {"error": "is_disabled form data must be equal to 'true' or 'false'"})), 401
    
    # Check is desable equal to true
    if is_disabled == "true":
        wallet = Wallet.query.filter(Wallet.owned_by == g.customer_xid).first()
        if not wallet:
            return jsonify(create_response("fail", {"error": "No wallet data found"})), 401
        if not wallet.is_enabled():
            return jsonify(create_response("fail", {"error": "Already disabled"})), 401
        wallet.disable()

        wallet = wallet.to_dict()
        del wallet['enabled_at']

        return jsonify(create_response("success", {"wallet": wallet}))

    # Check is desable equal to false
    if is_disabled == "false":
        wallet = Wallet.query.filter(Wallet.owned_by == g.customer_xid).first()
        if not wallet:
            return jsonify(create_response("fail", {"error": "No wallet data found"})), 401
        if wallet.is_enabled():
            return jsonify(create_response("fail", {"error": "Already enabled"})), 401
        wallet.disable()

        wallet = wallet.to_dict()
        del wallet['disabled_at']

        return jsonify(create_response("success", {"wallet": wallet}))
    