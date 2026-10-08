"""Pure transport ordering controls; no numerical reference or worker."""

from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[1]/"scripts"/"pirc25"
sys.path.insert(0, str(SCRIPTS))
from calibrated_study import require_original_event_order


def test_filtered_original_events_allow_gaps_but_preserve_append_order():
    require_original_event_order([{"sequence": i} for i in (1, 3, 8)])


@pytest.mark.parametrize("values", [(2, 1), (1, 1), (0, 1), (True, 2), (1., 2), ()])
def test_reordered_duplicated_or_noncanonical_sequences_refuse(values):
    with pytest.raises(ValueError):
        require_original_event_order([{"sequence": i} for i in values])
