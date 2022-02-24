import enum
from re import S
import uuid
from xmlrpc.client import boolean
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
db = SQLAlchemy()
from datetime import datetime

def generate_uuid():
    return str(uuid.uuid4())

class WalletStatus(enum.Enum):
    enabled = "enabled"
    disabled = "disabled"

class WalletHistoryType(enum.Enum):
    debit = "debit"
    credit = "credit"

class Wallet(db.Model, SerializerMixin):
    __table_args__ = (
        db.UniqueConstraint('owned_by', name='unique_owned_by'),
    )
    id = db.Column(db.String(40), unique=True, primary_key=True, default=generate_uuid)
    owned_by = db.Column(db.String(40))
    status = db.Column(db.Enum(WalletStatus), default=WalletStatus.disabled)
    enabled_at = db.Column(db.DateTime())
    disabled_at = db.Column(db.DateTime(), default=datetime.now)
    balance = db.Column(db.Integer, default=0)

    def __init__(self, owned_by):
        self.owned_by = owned_by
        db.session.add(self)
        db.session.commit()
    
    def enable(self):
        self.status = WalletStatus.enabled
        self.enabled_at = datetime.now()
        self.disabled_at = None
        db.session.commit()
    
    def disable(self):
        self.status = WalletStatus.disabled
        self.disabled_at = datetime.now()
        self.enabled_at = None
        db.session.commit()

    def is_enabled(self) -> bool:
        if self.status == WalletStatus.enabled:
            return True
        return False
    
    def deposit(self, reference_id, amount: int):
        self.balance += amount
    
    def withdrawal(self, reference_id, amount: int):
        self.balance -= amount

class WalletHistory(db.Model, SerializerMixin):
    id = db.Column(db.String(40), unique=True, primary_key=True, default=generate_uuid)
    reference_id = db.Column(db.String(40))
    wallet_id = db.Column(db.String(40), db.ForeignKey('wallet.id'), nullable=False)
    type = db.Column(db.Enum(WalletHistoryType))
    balance_before = db.Column(db.Integer, default=0)
    balance_after = db.Column(db.Integer, default=0)
    amount = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(), default=datetime.now)

    def __init__(self, reference_id, wallet_id, type, amount, balance_before, balance_after):
        self.reference_id = reference_id
        self.wallet_id = wallet_id
        self.type = type
        self.amount = amount
        self.balance_before = balance_before
        self.balance_after = balance_after
    
    def parse_to_dict(self, owned_by: str) -> dict:
        wallet_history_dict = self.to_dict()
        for i in ["balance_before", "balance_after", "type", "id"]:
            del wallet_history_dict[i]
        if self.type == WalletHistoryType.debit:
            wallet_history_dict["deposited_at"] = wallet_history_dict.pop("created_at")
            wallet_history_dict["deposited_by"] = owned_by

        if self.type == WalletHistoryType.credit:
            wallet_history_dict["deposited_at"] = wallet_history_dict.pop("created_at")
            wallet_history_dict["deposited_by"] = owned_by
            
        wallet_history_dict["id"] = wallet_history_dict.pop("wallet_id")
        wallet_history_dict["status"] = "success"
        return wallet_history_dict
        

def IsReferenceIDEverUse(reference_id: str, transaction_type: str) -> bool:
    if transaction_type == "deposit":
        transaction_type = WalletHistoryType.debit
    else:
        transaction_type = WalletHistoryType.credit 
    wallet_history = WalletHistory.query.filter(WalletHistory.reference_id == reference_id, WalletHistory.type == transaction_type).first()
    if wallet_history:
        return True
    return False