import logging
import sys
from typing import List, Dict, Union

from brother_ql.backends.helpers import discover

# Monkeypatch!
import brother_ql.backends.helpers
from label_bro.utils.brother_ql_backends import backend_factory
brother_ql.backends.helpers.backend_factory = backend_factory


def discover_printers_backend() -> List[Dict[str, Union[str, None]]]:
    # Discover printers using both USB and network backends
    usb_devices = discover('pyusb')
    network_devices = discover('network')
    return usb_devices + network_devices

# discover_printers_backend()
