import pytest

from wallet import HoldStatus, WalletService


def test_available_subtracts_active_holds() -> None:
    wallet = WalletService()
    wallet.open_account("account-1", 10_000)

    wallet.authorize("account-1", 3_000)

    assert wallet.available("account-1") == 7_000


def test_authorize_rejects_amount_above_available_balance() -> None:
    wallet = WalletService()
    wallet.open_account("account-1", 10_000)
    wallet.authorize("account-1", 3_000)

    with pytest.raises(ValueError, match="insufficient available funds"):
        wallet.authorize("account-1", 8_000)

    assert wallet.available("account-1") == 7_000


def test_duplicate_capture_returns_captured_hold_without_recapturing() -> None:
    wallet = WalletService()
    wallet.open_account("account-1", 10_000)
    hold = wallet.authorize("account-1", 3_000)

    captured_hold = wallet.capture(hold.hold_id)
    balance_after_capture = wallet.balance("account-1")
    repeated_hold = wallet.capture(hold.hold_id)

    assert captured_hold is hold
    assert repeated_hold is captured_hold
    assert hold.status == HoldStatus.CAPTURED
    assert wallet.balance("account-1") == balance_after_capture


def test_duplicate_void_returns_already_voided_hold() -> None:
    wallet = WalletService()
    wallet.open_account("account-1", 10_000)
    hold = wallet.authorize("account-1", 3_000)

    voided_hold = wallet.void(hold.hold_id)
    repeated_hold = wallet.void(hold.hold_id)

    assert voided_hold is hold
    assert repeated_hold is voided_hold
    assert hold.status == HoldStatus.VOIDED


def test_capture_rejects_voided_hold() -> None:
    wallet = WalletService()
    wallet.open_account("account-1", 10_000)
    hold = wallet.authorize("account-1", 3_000)
    wallet.void(hold.hold_id)

    with pytest.raises(ValueError):
        wallet.capture(hold.hold_id)

    assert hold.status == HoldStatus.VOIDED


def test_void_rejects_captured_hold() -> None:
    wallet = WalletService()
    wallet.open_account("account-1", 10_000)
    hold = wallet.authorize("account-1", 3_000)
    wallet.capture(hold.hold_id)

    with pytest.raises(ValueError):
        wallet.void(hold.hold_id)

    assert hold.status == HoldStatus.CAPTURED


def test_capture_updates_balance_and_keeps_other_holds_reserved() -> None:
    wallet = WalletService()
    wallet.open_account("account-1", 10_000)
    hold_to_capture = wallet.authorize("account-1", 3_000)
    wallet.authorize("account-1", 2_000)

    wallet.capture(hold_to_capture.hold_id)

    assert wallet.balance("account-1") == 7_000
    assert wallet.available("account-1") == 5_000


def test_void_releases_hold_without_changing_balance() -> None:
    wallet = WalletService()
    wallet.open_account("account-1", 10_000)
    hold = wallet.authorize("account-1", 3_000)

    wallet.void(hold.hold_id)

    assert wallet.balance("account-1") == 10_000
    assert wallet.available("account-1") == 10_000
