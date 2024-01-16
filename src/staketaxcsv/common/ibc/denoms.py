import logging
from staketaxcsv.common.ibc.api_lcd_v1 import LcdAPI_v1
import staketaxcsv.common.ibc.constants as co

# Add only if regular lcd api lookup is missing functional data
IBC_ADDRESSES_TO_DENOM = {
    "ibc/ED07A3391A112B175915CD8FAF43A2DA8E4790EDE12566649D0C2F97716B8518": "uosmo",
    "ibc/E6931F78057F7CC5DA0FD6CEF82FF39373A6E0452BF1FD76910B93292CF356C1": co.CUR_CRO,
    "ibc/8318B7E036E50C0CF799848F23ED84778AAA8749D9C0BCD4FF3F4AF73C53387F": "uloop",
}


def ibc_address_to_denom(node, ibc_address, ibc_addresses):
    if ibc_address in IBC_ADDRESSES_TO_DENOM:
        return IBC_ADDRESSES_TO_DENOM[ibc_address]
    if not node:
        return None
    if ibc_address in ibc_addresses:
        return ibc_addresses[ibc_address]

    denom = LcdAPI_v1(node).ibc_address_to_denom(ibc_address)

    ibc_addresses[ibc_address] = denom
    return denom


def amount_currency_from_raw(amount_raw, currency_raw, lcd_node, ibc_addresses):
    # example currency_raw:
    # 'ibc/B3504E092456BA618CC28AC671A71FB08C6CA0FD0BE7C8A5B5A3E2DD933CC9E4'
    # 'uluna'
    # 'aevmos'
    if currency_raw is None:
        return amount_raw, currency_raw
    elif currency_raw.startswith("ibc/"):
        # ibc address
        denom = None
        try:
            denom = ibc_address_to_denom(
                lcd_node, currency_raw, ibc_addresses)
            amount, currency = _amount_currency_convert(amount_raw, denom)
            return amount, currency
        except Exception as e:
            logging.warning("Unable to find symbol for ibc address %s, denom=%s, exception=%s",
                            currency_raw, denom, str(e))
            amount = float(amount_raw) / co.MILLION
            currency = "unknown_{}".format(denom if denom else currency_raw)
            return amount, currency
    else:
        return _amount_currency_convert(amount_raw, currency_raw)


def _amount_currency_convert(amount_raw, currency_raw):
    # Special cases for nonconforming denoms/assets
    # currency_raw -> (currency, exponent)
    CURRENCY_RAW_MAP = {
        co.CUR_CRO: (co.CUR_CRO, 8),
        co.CUR_MOBX: (co.CUR_MOBX, 9),
        "gravity0xfB5c6815cA3AC72Ce9F5006869AE67f18bF77006": (co.CUR_PSTAKE, 18),
        "inj": (co.CUR_INJ, 18),
        "OSMO": (co.CUR_OSMO, 6),
        "osmo": (co.CUR_OSMO, 6),
        "rowan": ("ROWAN", 18),
        "basecro": (co.CUR_CRO, 8),
        "uusd": (co.CUR_USTC, 6),
    }

    if currency_raw in CURRENCY_RAW_MAP:
        currency, exponent = CURRENCY_RAW_MAP[currency_raw]
        amount = float(amount_raw) / float(10 ** exponent)
        return amount, currency
    elif currency_raw.startswith("gamm/"):
        # osmosis lp currencies
        # i.e. "gamm/pool/6" -> "GAMM-6"
        amount = float(amount_raw) / co.EXP18
        _, _, num = currency_raw.split("/")
        currency = "GAMM-{}".format(num)
        return amount, currency
    elif currency_raw.endswith("-wei"):
        amount = float(amount_raw) / co.EXP18
        currency, _ = currency_raw.split("-wei")
        currency = currency.upper()
        return amount, currency
    elif currency_raw.startswith("a"):
        amount = float(amount_raw) / co.EXP18
        currency = currency_raw[1:].upper()
        return amount, currency
    elif currency_raw.startswith("nano"):
        amount = float(amount_raw) / co.EXP9
        currency = currency_raw[4:].upper()
        return amount, currency
    elif currency_raw.startswith("n"):
        amount = float(amount_raw) / co.EXP9
        currency = currency_raw[1:].upper()
        return amount, currency
    elif currency_raw.startswith("u"):
        amount = float(amount_raw) / co.MILLION
        currency = currency_raw[1:].upper()
        return amount, currency
    elif currency_raw.startswith("st"):
        # i.e. stinj, stujuno, staevmos
        amt, cur = _amount_currency_convert(amount_raw, currency_raw[2:])
        return amt, "st" + cur
    else:
        logging.error("_amount_currency_from_raw(): no case for amount_raw={}, currency_raw={}".format(
            amount_raw, currency_raw))
        amount = float(amount_raw) / co.MILLION
        currency = "unknown_{}".format(currency_raw)
        return amount, currency