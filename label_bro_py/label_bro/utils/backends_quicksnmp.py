import asyncio
from typing import List, Dict, Any, Union
from pysnmp.hlapi.v3arch import UdpTransportTarget, set_cmd, get_cmd, bulk_cmd, CommunityData
from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity
from pysnmp.entity.engine import SnmpEngine
from pysnmp.hlapi.v3arch.asyncio.context import ContextData

def construct_object_types(list_of_oids: List[str]) -> List[ObjectType]:
    object_types = []
    for oid in list_of_oids:
        object_types.append(ObjectType(ObjectIdentity(oid)))
    return object_types


def construct_value_pairs(list_of_pairs: Dict[str, Any]) -> List[ObjectType]:
    pairs = []
    for key, value in list_of_pairs.items():
        pairs.append(ObjectType(ObjectIdentity(key), value))
    return pairs


def set(target: str, value_pairs: Dict[str, Any], credentials: CommunityData, port: int = 161, engine: SnmpEngine = SnmpEngine(), context: ContextData = ContextData()) -> Dict[str, Any]:
    handler = set_cmd(
        engine,
        credentials,
        UdpTransportTarget((target, port)),
        context,
        *construct_value_pairs(value_pairs)
    )
    return fetch(handler, 1)[0]


def get(target: str, oids: List[str], credentials: CommunityData, port: int = 161, engine: SnmpEngine = SnmpEngine(), context: ContextData = ContextData()) -> Dict[str, Any]:
    handler = get_cmd(
        engine,
        credentials,
        UdpTransportTarget((target, port)),
        context,
        *construct_object_types(oids)
    )
    return fetch(handler, 1)[0]


def get_bulk(target: str, oids: List[str], credentials: CommunityData, count: int, start_from: int = 0, port: int = 161,
             engine: SnmpEngine = SnmpEngine(), context: ContextData = ContextData()) -> List[Dict[str, Any]]:
    handler = bulk_cmd(
        engine,
        credentials,
        UdpTransportTarget((target, port)),
        context,
        start_from, count,
        *construct_object_types(oids)
    )
    return fetch(handler, count)


def get_bulk_auto(target: str, oids: List[str], credentials: CommunityData, count_oid: str, start_from: int = 0, port: int = 161,
                  engine: SnmpEngine = SnmpEngine(), context: ContextData = ContextData()) -> List[Dict[str, Any]]:
    count = get(target, [count_oid], credentials, port, engine, context)[count_oid]
    return get_bulk(target, oids, credentials, count, start_from, port, engine, context)


def cast(value: Any) -> Union[int, float, str, Any]:
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                return str(value, 'UTF-8')
            except (ValueError, TypeError):
                pass
    return value


def fetch(handler: Any, count: int) -> List[Dict[str, Any]]:
    result = []
    for i in range(count):
        try:
            error_indication, error_status, error_index, var_binds = next(handler)
            if not error_indication and not error_status:
                items = {}
                for var_bind in var_binds:
                    items[str(var_bind[0])] = cast(var_bind[1])
                result.append(items)
            else:
                raise RuntimeError('Got SNMP error: {0}'.format(error_indication))
        except StopIteration:
            break
    return result


async def broadcastSNMPReq(reqMsg: Any, cbRecvFun: Any, cbTimerFun: Any, max_number_of_responses: int = 10) -> None:
    transportDispatcher = SnmpEngine()
    transportTarget = UdpTransportTarget(('255.255.255.255', 161), timeout=1, retries=0)

    # Construct the SNMP GET command
    handler = get_cmd(
        transportDispatcher,
        CommunityData('public'),
        transportTarget,
        ContextData(),
        *construct_object_types(reqMsg)  # Assuming reqMsg is a list of OIDs
    )

    # Fetch the response
    async for errorIndication, errorStatus, errorIndex, varBinds in handler:
        if errorIndication:
            raise RuntimeError(f'SNMP error: {errorIndication}')

        # Process received messages
        for varBind in varBinds:
            cbRecvFun(varBind)

    # Call timer function
    cbTimerFun()

    # Close the transport dispatcher
    transportDispatcher.transportDispatcher.closeDispatcher()
