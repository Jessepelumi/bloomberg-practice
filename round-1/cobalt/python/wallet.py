from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class HoldStatus(str, Enum):
    HELD = "held"
    CAPTURED = "captured"
    VOIDED = "voided"


@dataclass
class Hold:
    hold_id: str
    account_id: str
    amount: int
    status: HoldStatus


class WalletService:
    """A wallet with authorization holds. Funds are authorized (reserved), then
    either captured (settled out of the balance) or voided (released). All amounts
    are integer cents. Available funds are the balance minus active holds."""

    def __init__(self) -> None:
        self._balance: dict[str, int] = {}
        self._holds: dict[str, Hold] = {}
        self._seq = 0

    def open_account(self, account_id: str, cents: int) -> None:
        if cents < 0:
            raise ValueError("opening balance must be non-negative")
        self._balance[account_id] = cents

    def balance(self, account_id: str) -> int:
        return self._require(account_id)

    def available(self, account_id: str) -> int:
        bal = self._require(account_id)
        return bal - self._active_holds(account_id)

    def authorize(self, account_id: str, cents: int) -> Hold:
        self._require(account_id)
        if cents <= 0:
            raise ValueError("amount must be positive")
        if self.available(account_id) < cents:
            raise ValueError("insufficient available funds")
        self._seq += 1
        hid = f"H{self._seq}"
        h = Hold(hid, account_id, cents, HoldStatus.HELD)
        self._holds[hid] = h
        return h

    def capture(self, hold_id: str) -> Hold:
        h = self._get(hold_id)
        if h.status == HoldStatus.VOIDED:
            raise ValueError("cannot capture a voided hold")
        if h.status == HoldStatus.CAPTURED:
            return h
        self._balance[h.account_id] -= h.amount
        h.status = HoldStatus.CAPTURED
        return h

    def void(self, hold_id: str) -> Hold:
        h = self._get(hold_id)
        if h.status == HoldStatus.CAPTURED:
            raise ValueError("cannot void a captured hold")
        h.status = HoldStatus.VOIDED
        return h

    def _active_holds(self, account_id: str) -> int:
        return sum(h.amount for h in self._holds.values()
                   if h.account_id == account_id and h.status == HoldStatus.HELD)

    def _require(self, account_id: str) -> int:
        if account_id not in self._balance:
            raise ValueError("unknown account")
        return self._balance[account_id]

    def _get(self, hold_id: str) -> Hold:
        h = self._holds.get(hold_id)
        if h is None:
            raise ValueError("hold not found")
        return h
