#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test sendall spec."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

class OmniSendallSpec(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True
        self.extra_args = [['-omniactivationallowsender=any']]

    def run_test(self):
        self.log.info("test basic omni spec")

        # Preparing some mature Bitcoins
        coinbase_address = self.nodes[0].getnewaddress()
        self.nodes[0].generatetoaddress(110, coinbase_address)

        # Obtaining a master address to work with
        address = self.nodes[0].getnewaddress()

        # Funding the address with some testnet BTC for fees
        self.nodes[0].sendtoaddress(address, 10)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Create a fixed property
        txidA = self.nodes[0].omni_sendissuancefixed(address, 1, 2, 0, "Test Category", "Test Subcategory", "TST", "http://www.omnilayer.org", "", "100000")
        txidB = self.nodes[0].omni_sendissuancefixed(address, 2, 2, 0, "Test Category", "Test Subcategory", "TST2", "http://www.omnilayer.org", "", "100000")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        resultA = self.nodes[0].omni_gettransaction(txidA)
        resultB = self.nodes[0].omni_gettransaction(txidB)
        assert_equal(resultA['valid'], True)
        assert_equal(resultB['valid'], True)

        # Get currency ID
        currencyA = resultA['propertyid']
        currencyB = resultB['propertyid']

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

        # Setup variables
        startBTC = "0.10000000"
        startMSC = "0.10000000"
        zeroAmount = "0.00000000"

        # In all ecosystems all available tokens can be transferred with transaction type 4

        for ecosystem in [1 ,2]:
            # Created funded address for test
            if ecosystem == 1:
                ecosystemStr = "main"
            else:
                ecosystemStr = "test"
            actorAddress = self.nodes[0].getnewaddress()
            otherAddress = self.nodes[0].getnewaddress()
            txidA = self.nodes[0].omni_send(address, actorAddress, currencyA, startMSC)
            txidB = self.nodes[0].omni_send(address, actorAddress, currencyB, startMSC)
            self.nodes[0].sendtoaddress(actorAddress, startBTC)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            resultA = self.nodes[0].omni_gettransaction(txidA)
            resultB = self.nodes[0].omni_gettransaction(txidB)
            assert_equal(resultA['valid'], True)
            assert_equal(resultB['valid'], True)

            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyA)['balance'], startMSC)
            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyB)['balance'], startMSC)
            assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyA)['balance'], zeroAmount)
            assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyB)['balance'], zeroAmount)

            txid = self.nodes[0].omni_sendall(actorAddress, otherAddress, ecosystem)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)
            assert_equal(result['txid'], txid)
            assert_equal(result['sendingaddress'], actorAddress)
            assert_equal(result['referenceaddress'], otherAddress)
            assert_equal(result['type_int'], 4)
            assert_equal(result['ecosystem'], ecosystemStr)
            found = False
            if 'subsends' in result:
                found = True
            assert_equal(found, True)

            subSends = result['subsends']
            assert_equal(len(subSends), 1)
            if ecosystem == 1:
                assert_equal(subSends[0]['propertyid'], currencyA)
            else:
                assert_equal(subSends[0]['propertyid'], currencyB)
            assert_equal(subSends[0]['divisible'], True)
            assert_equal(subSends[0]['amount'], startMSC)

            if ecosystem == 1:
                assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyA)['balance'], zeroAmount)
                assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyB)['balance'], startMSC)
                assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyA)['balance'], startMSC)
                assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyB)['balance'], zeroAmount)
            else:
                assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyA)['balance'], startMSC)
                assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyB)['balance'], zeroAmount)
                assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyA)['balance'], zeroAmount)
                assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyB)['balance'], startMSC)

        # In all ecosystems sending all tokens is only valid, if at least one unit was transferred
        for ecosystem in [1 ,2]:
            actorAddress = self.nodes[0].getnewaddress()
            otherAddress = self.nodes[0].getnewaddress()
            txidA = self.nodes[0].omni_send(address, actorAddress, currencyA, startMSC)
            txidB = self.nodes[0].omni_send(address, actorAddress, currencyB, startMSC)
            self.nodes[0].sendtoaddress(actorAddress, startBTC)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            resultA = self.nodes[0].omni_gettransaction(txidA)
            resultB = self.nodes[0].omni_gettransaction(txidB)
            assert_equal(resultA['valid'], True)
            assert_equal(resultB['valid'], True)

            txidA = self.nodes[0].omni_send(actorAddress, otherAddress, currencyA, startMSC)
            txidB = self.nodes[0].omni_send(actorAddress, otherAddress, currencyB, startMSC)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            resultA = self.nodes[0].omni_gettransaction(txidA)
            resultB = self.nodes[0].omni_gettransaction(txidB)
            assert_equal(resultA['valid'], True)
            assert_equal(resultB['valid'], True)

            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyA)['balance'], zeroAmount)
            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyB)['balance'], zeroAmount)
            assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyA)['balance'], startMSC)
            assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyB)['balance'], startMSC)

            txid = self.nodes[0].omni_sendall(actorAddress, otherAddress, ecosystem)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], False)

            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyA)['balance'], zeroAmount)
            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyB)['balance'], zeroAmount)
            assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyA)['balance'], startMSC)
            assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyB)['balance'], startMSC)

        # In all ecosystems only available, unreserved balances are transferred, when sending all tokens
        for ecosystem in [1 ,2]:
            actorAddress = self.nodes[0].getnewaddress()
            otherAddress = self.nodes[0].getnewaddress()
            self.nodes[0].sendtoaddress(actorAddress, startBTC)
            self.nodes[0].sendtoaddress(otherAddress, startBTC)
            self.nodes[0].generatetoaddress(1, coinbase_address)
            txid = self.nodes[0].omni_sendissuancefixed(actorAddress, ecosystem, 2, 0, "Test Category", "Test Subcategory", "TST" + str(2 + ecosystem), "http://www.omnilayer.org", "", "10")
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)

            # Get currency ID
            currencyID = result['propertyid']

            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['balance'], "10.00000000")
            assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyID)['balance'], zeroAmount)

            txid = self.nodes[0].omni_senddexsell(actorAddress, currencyID, "4", "4", 10, "0.00001", 1)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)
            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['balance'], "6.00000000")
            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['reserved'], "4.00000000")

            txid = self.nodes[0].omni_sendall(actorAddress, otherAddress, ecosystem)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)
            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['balance'], zeroAmount)
            assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['reserved'], "4.00000000")
            assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyID)['balance'], "6.00000000")

if __name__ == '__main__':
    OmniSendallSpec().main()
