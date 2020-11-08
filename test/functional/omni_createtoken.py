#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test create token."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

class OmniCreateToken(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

    def run_test(self):
        self.log.info("test create token")

        # Preparing some mature Bitcoins
        coinbase_address = self.nodes[0].getnewaddress()
        self.nodes[0].generatetoaddress(101, coinbase_address)

        # Obtaining a master address to work with
        address = self.nodes[0].getnewaddress()

        # Funding the address with some testnet BTC for fees
        self.nodes[0].sendtoaddress(address, 1)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Create a managed property
        txid = self.nodes[0].omni_sendissuancemanaged(address, 1, 1, 0, "Test Category", "Test Subcategory", "ManagedTokens", "http://www.omnilayer.org", "")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Can Issue Tokens
        currency_id = result['propertyid']
        result = self.nodes[0].omni_sendgrant(address, address, currency_id, "100")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Can Send a newly issued token
        other_address = self.nodes[0].getnewaddress()
        result = self.nodes[0].omni_send(address, other_address, currency_id, "1")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Checks
        spt_info = self.nodes[0].omni_getproperty(currency_id)
        manager_spt = self.nodes[0].omni_getbalance(address, currency_id)
        other_spt = self.nodes[0].omni_getbalance(other_address, currency_id)
        assert_equal(spt_info['totaltokens'], "100")
        assert_equal(manager_spt['balance'], "99")
        assert_equal(other_spt['balance'], "1")

if __name__ == '__main__':
    OmniCreateToken().main()
