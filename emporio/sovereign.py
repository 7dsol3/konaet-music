"""Receipt commitments compatible with KONAET Sovereign; no validator submission."""
import secrets

from .storage import canonical
from .vendor.sovereign_receipt import process


def opening(receipt, server_seal):
    value = {"receipt": receipt, "server_seal": server_seal}
    document = canonical(value).encode("utf-8")
    salt = secrets.token_hex(32)
    frame = (salt + "\n" + document.hex() + "\n-\n").encode("ascii")
    result = process(frame)
    return {"schema": "konaet.music.sovereign-opening.v1", "salt": salt, "document_hex": document.hex(),
            "private_opening": {"schema":"konaet.social-receipt-opening.v1", "document":value, "salt":salt},
            "commitment": result["commitment"], "args": result["args"], "network_finalized": False,
            "notice": "Private opening for SocialReceiptRegistry.ko. No chain submission, certificate or money transfer has occurred."}


def verify_opening(value):
    private = value["private_opening"]
    if set(private) != {"schema","document","salt"} or private["schema"] != "konaet.social-receipt-opening.v1" or private["salt"] != value["salt"] or canonical(private["document"]).encode().hex() != value["document_hex"]:
        return False
    frame = (value["salt"] + "\n" + value["document_hex"] + "\n" + value["commitment"] + "\n").encode("ascii")
    result = process(frame)
    return result["matches"] is True and result["args"] == value["args"]
