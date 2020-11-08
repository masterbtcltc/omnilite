#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test grace period."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

class OmniGracePeriod(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True
        self.extra_args = [['-omniactivationallowsender=any']]

    def sendactivation(self, address, coinbase_address, heights, expected):
         # Min client version for feature activation
        minClientVersion = 0

        for height in heights:
            activation_block = self.nodes[0].getblockcount() + height + 1
            txid = self.nodes[0].omni_sendactivation(address, 3, activation_block, minClientVersion)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], expected)

    def run_test(self):
        self.log.info("test grace period")

        # Preparing some mature Bitcoins
        coinbase_address = self.nodes[0].getnewaddress()
        self.nodes[0].generatetoaddress(101, coinbase_address)

        # Obtaining a master address to work with
        address = self.nodes[0].getnewaddress()

        # Funding the address with some testnet BTC for fees
        self.nodes[0].sendtoaddress(address, 0.1)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # A relative activation height of blocks is smaller than the grace period and not allowed
        self.sendactivation(address, coinbase_address, [-100, 0, 1, 2, 4], False)

        # A relative activation height of blocks is too far in the future and not allowed
        self.sendactivation(address, coinbase_address, [11, 288, 12289, 999999], False)

        # A relative activation height of blocks is within the grace period and accepted
        activationMinBlocks = 5
        activationMaxBlocks = 10
        self.sendactivation(address, coinbase_address, [activationMinBlocks, activationMinBlocks + 1, activationMaxBlocks - 1, activationMaxBlocks], True)

if __name__ == '__main__':
    OmniGracePeriod().main()
