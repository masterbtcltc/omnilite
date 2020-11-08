#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test basic omni spec."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

class OmniBasicSpec(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True
        self.extra_args = [['-omniactivationallowsender=any']]

    def run_test(self):
        self.log.info("test basic omni spec")

        faucetBTC = "10"
        faucetOMNI = "1000.00000000"

        # Preparing some mature Bitcoins
        coinbase_address = self.nodes[0].getnewaddress()
        self.nodes[0].generatetoaddress(110, coinbase_address)

        # Obtaining a master address to work with
        address = self.nodes[0].getnewaddress()

        # Funding the address with some testnet BTC for fees
        self.nodes[0].sendtoaddress(address, 10)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Create a fixed property
        txid = self.nodes[0].omni_sendissuancefixed(address, 1, 2, 0, "Test Category", "Test Subcategory", "TST", "http://www.omnilayer.org", "", "100000")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get currency ID
        currencyOffered = result['propertyid']

        # Activating Free DEx...
        activation_block = self.nodes[0].getblockcount() + 8
        txid = self.nodes[0].omni_sendactivation(address, 15, activation_block, 0)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Mining 10 blocks to forward past the activation block
        self.nodes[0].generatetoaddress(10, coinbase_address)

        # Checking the activation went live as expected...
        featureid = self.nodes[0].omni_getactivations()['completedactivations']
        freeDEx = False
        for ids in featureid:
            if ids['featureid'] == 15:
                freeDEx = True
        assert_equal(freeDEx, True)

        # Created funded address for test
        fundedAddress = self.nodes[0].getnewaddress()

        # We call omni_getbalance on a newly generated address
        balance = self.nodes[0].omni_getbalance(fundedAddress, currencyOffered)['balance']
        assert_equal(balance, "0.00000000")

        # Fund new address
        txid = self.nodes[0].omni_send(address, fundedAddress, currencyOffered, faucetOMNI)
        self.nodes[0].sendtoaddress(fundedAddress, faucetBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # omniGetBalance returns correct balances
        mscBalance = self.nodes[0].omni_getbalance(fundedAddress, currencyOffered)
        assert_equal(mscBalance['balance'], faucetOMNI)
        assert_equal(mscBalance['reserved'], "0.00000000")

        # omniGetAllBalancesForId returns correct balances
        mscBalances = self.nodes[0].omni_getallbalancesforid(currencyOffered)

        found = False
        for balance in mscBalances:
            if balance['address'] == fundedAddress:
                found = True
                assert_equal(balance['balance'], faucetOMNI)
                assert_equal(balance['reserved'], "0.00000000")

        assert_equal(found, True)

        # omniGetAllBalancesForAddress returns correct balances"
        balances = self.nodes[0].omni_getallbalancesforaddress(fundedAddress)

        found = False
        for balance in balances:
            if balance['name'] == "TST":
                found = True
                assert_equal(balance['balance'], faucetOMNI)
                assert_equal(balance['reserved'], "0.00000000")

        assert_equal(found, True)

        # Create raw transaction with reference address

        # Set variables
        passiveAddress = self.nodes[0].getnewaddress()
        payload = "00000000000000040000000000000001" # Simple Send: transfer  0.00000001 TST

        # We submit a raw transaction
        txid = self.nodes[0].omni_sendrawtx(fundedAddress, payload, passiveAddress)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)
        assert_equal(result['sendingaddress'], fundedAddress)
        assert_equal(result['referenceaddress'], passiveAddress)

        # Create raw transaction without reference address

        payloads = {"00010014000000040000000005f5e1000000000059682f000a00000000000003e801",# Tx 20: Offer 1,0 TST for 0.15 BTC on the traditional exchange
                   "000000320200020000000000005444697600000000000000000f4240", # Tx 50: Create property in test ecosystem, 1000000 divisible "TDiv
                   "000000320100010000000000004d496e6469760000000003fde42988fa35"} # Tx 50: Create property in main ecosystem, 1123581321345589 indivisible "MIndiv"

        for payload in payloads:
            # We submit a raw transaction
            txid = self.nodes[0].omni_sendrawtx(fundedAddress, payload)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['confirmations'], 1)
            assert_equal(result['valid'], True)

if __name__ == '__main__':
    OmniBasicSpec().main()
