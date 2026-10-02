"""Offline source grants are bound to the model protocol, owner and consumer."""

import pytest

from scripts.pirc25.admission import validate_model_permission


def inputs():
    model = {"study_id": "owner", "visibility": "restricted", "protocol_hash": "a" * 64}
    grant = {"authorization_id": "model-consumer", "study_id": "owner", "consumer_study_ids": ["consumer"],
             "protocol_hash": "a" * 64, "purposes": ["evaluate"], "visibilities": ["restricted"],
             "expires_at": "2026-10-03T00:00:00+00:00"}
    spec = {"study_id": "consumer", "admission": {"authorization_id": "execution",
                                                 "model_authorization_id": "model-consumer"}}
    return model, grant, spec


def test_valid_source_grant_and_same_study_grant():
    model, grant, spec = inputs()
    validate_model_permission(model, grant, spec, "2026-10-02T00:00:00+00:00")
    spec["study_id"] = "owner"
    grant["authorization_id"] = "execution"
    validate_model_permission(model, grant, spec, "2026-10-02T00:00:00+00:00")


@pytest.mark.parametrize("mutation", ["missing-protocol", "wrong-protocol", "wrong-owner", "wrong-consumer",
    "wrong-grant", "wrong-purpose", "wrong-visibility", "expired", "naive-expiry", "missing-grant-id"])
def test_invalid_model_source_grant_rejected(mutation):
    model, grant, spec = inputs()
    if mutation == "missing-protocol":
        grant.pop("protocol_hash")
    elif mutation == "wrong-protocol":
        grant["protocol_hash"] = "b" * 64
    elif mutation == "wrong-owner":
        grant["study_id"] = "unrelated"
    elif mutation == "wrong-consumer":
        grant["consumer_study_ids"] = []
    elif mutation == "wrong-grant":
        grant["authorization_id"] = "unrelated"
    elif mutation == "wrong-purpose":
        grant["purposes"] = ["preview"]
    elif mutation == "wrong-visibility":
        grant["visibilities"] = ["synthetic"]
    elif mutation == "expired":
        grant["expires_at"] = "2026-10-01T00:00:00+00:00"
    elif mutation == "naive-expiry":
        grant["expires_at"] = "2026-10-03T00:00:00"
    else:
        spec["admission"].pop("model_authorization_id")
    with pytest.raises(ValueError, match="admission evidence"):
        validate_model_permission(model, grant, spec, "2026-10-02T00:00:00+00:00")
