### Take some code from a fork

"""
Helpers for the subpackage brother_ql.backends

* device discovery
* printing
"""

import logging
import sys
import time

from brother_ql.backends import guess_backend
from brother_ql.reader import interpret_response
from typing import List, Dict, Union, Optional, Any

logger = logging.getLogger(__name__)

logger.info("sys.executable %s" % sys.executable)
def discover(backend_identifier: str = 'linux_kernel') -> List[Dict[str, Union[str, None]]]:
    # This points to our locally defined copy of this function, so we can change the behaivor
    be = backend_factory(backend_identifier)
    list_available_devices = be['list_available_devices']
    BrotherQLBackend       = be['backend_class']

    available_devices = list_available_devices()
    return available_devices

def send(instructions: bytes, printer_identifier: Optional[str] = None, backend_identifier: Optional[str] = None, blocking: bool = True) -> Dict[str, Union[bool, str, Optional[Dict[str, Any]]]]:
    """
    Send instruction bytes to a printer.

    :param bytes instructions: The instructions to be sent to the printer.
    :param str printer_identifier: Identifier for the printer.
    :param str backend_identifier: Can enforce the use of a specific backend.
    :param bool blocking: Indicates whether the function call should block while waiting for the completion of the printing.
    """

    status = {
        'instructions_sent': True, # The instructions were sent to the printer.
        'outcome': 'unknown', # String description of the outcome of the sending operation like: 'unknown', 'sent', 'printed', 'error'
        'printer_state': None, # If the selected backend supports reading back the printer state, this key will contain it.
        'did_print': False, # If True, a print was produced. It defaults to False if the outcome is uncertain (due to a backend without read-back capability).
        'ready_for_next_job': False, # If True, the printer is ready to receive the next instructions. It defaults to False if the state is unknown.
    }
    selected_backend = None
    if backend_identifier:
        selected_backend = backend_identifier
    else:
        try:
            selected_backend = guess_backend(printer_identifier)
        except:
            logger.info("No backend stated. Selecting the default linux_kernel backend.")
            selected_backend = 'linux_kernel'

    be = backend_factory(selected_backend)
    list_available_devices = be['list_available_devices']
    BrotherQLBackend       = be['backend_class']

    printer = BrotherQLBackend(printer_identifier)

    start = time.time()
    logger.info('Sending instructions to the printer. Total: %d bytes.', len(instructions))
    printer.write(instructions)
    status['outcome'] = 'sent'

    if not blocking:
        return status

    while time.time() - start < 10:
        data = printer.read()
        if not data:
            time.sleep(0.005)
            continue
        try:
            result = interpret_response(data)
        except ValueError:
            logger.error("TIME %.3f - Couln't understand response: %s", time.time()-start, data)
            continue
        status['printer_state'] = result
        logger.debug('TIME %.3f - result: %s', time.time()-start, result)
        if result['errors']:
            logger.error('Errors occured: %s', result['errors'])
            status['outcome'] = 'error'
            break
        if result['status_type'] in ('Printing completed', 'Reply to status request'):
            status['did_print'] = True
            status['outcome'] = 'printed'
        if result['status_type'] in ('Phase change', 'Reply to status request') and result['phase_type'] == 'Waiting to receive':
            status['ready_for_next_job'] = True
        if status['did_print'] and status['ready_for_next_job']:
            break

    if not status['did_print']:
        logger.warning("'printing completed' status not received.")
    if not status['ready_for_next_job']:
        logger.warning("'waiting to receive' status not received.")
    if (not status['did_print']) or (not status['ready_for_next_job']):
        logger.warning('Printing potentially not successful?')
    if status['did_print'] and status['ready_for_next_job']:
        logger.info("Printing was successful. Waiting for the next job.")

    return status


def backend_factory(backend_name: str) -> Dict[str, Any]:

    logging.info("sys.executable %s" % sys.executable)

    if backend_name == 'pyusb':
        print("BUTT!")
        from brother_ql.backends import pyusb        as pyusb_backend
        list_available_devices = pyusb_backend.list_available_devices
        backend_class          = pyusb_backend.BrotherQLBackendPyUSB
    elif backend_name == 'linux_kernel':
        print("BUTTFART")
        from brother_ql.backends import linux_kernel as linux_kernel_backend
        list_available_devices = linux_kernel_backend.list_available_devices
        backend_class          = linux_kernel_backend.BrotherQLBackendLinuxKernel
    elif backend_name == 'network':
        print("NETWORK!!!!")
        from label_bro.utils import backends_network      as network_backend
        list_available_devices = network_backend.list_available_devices
        backend_class          = network_backend.BrotherQLBackendNetwork
    else:
        raise NotImplementedError('Backend %s not implemented.' % backend_name)

    return {'list_available_devices': list_available_devices, 'backend_class': backend_class}
