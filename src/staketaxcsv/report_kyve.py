"""
usage: python3 staketaxcsv/report_bld.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/BLD*.csv
"""

import logging

import staketaxcsv.kyve.processor
from staketaxcsv.kyve.config_kyve import localconfig
from staketaxcsv.kyve.progress_kyve import SECONDS_PER_PAGE, ProgressKYVE
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import KYVE_NODE, TICKER_KYVE
from staketaxcsv.common.ibc import api_lcd


def main():
    report_util.main_default(TICKER_KYVE)


def read_options(options):
    report_util.read_common_options(localconfig, options)
    logging.info("localconfig: %s", localconfig.__dict__)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(KYVE_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = api_lcd.make_lcd_api(KYVE_NODE).get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_KYVE)
    txinfo = staketaxcsv.kyve.processor.process_tx(wallet_address, elem, exporter)

    return exporter


def estimate_duration(wallet_address):
    max_txs = localconfig.limit
    return SECONDS_PER_PAGE * api_lcd.get_txs_pages_count(KYVE_NODE, wallet_address, max_txs)


def txhistory(wallet_address):
    """ Configure localconfig based on options dictionary. """
    if localconfig.cache:
        localconfig.ibc_addresses = Cache().get_ibc_addresses()
        logging.info("Loaded ibc_addresses from cache ...")

    max_txs = localconfig.limit
    progress = ProgressKYVE()
    exporter = Exporter(wallet_address, localconfig, TICKER_KYVE)

    # Fetch count of transactions to estimate progress more accurately
    count_pages = api_lcd.get_txs_pages_count(KYVE_NODE, wallet_address, max_txs,
                                                                     debug=localconfig.debug)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = api_lcd.get_txs_all(KYVE_NODE, wallet_address, progress, max_txs,
                                                       debug=localconfig.debug)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.kyve.processor.process_txs(wallet_address, elems, exporter)

    if localconfig.cache:
        Cache().set_ibc_addresses(localconfig.ibc_addresses)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
