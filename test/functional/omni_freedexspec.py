#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test DEx spec using free DEx."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

class OmniFreeDExSpec(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True
        self.extra_args = [['-omniactivationallowsender=any']]

    def run_test(self):
        self.log.info("test dex spec using free dex")

        # Create varaibles that will remain unchanged
        stdBlockSpan = 10
        stdCommitFee = "0.00010000"
        actionNew = 1
        actionUpdate = 2
        actionCancel = 3

        # Preparing some mature Bitcoins
        coinbase_address = self.nodes[0].getnewaddress()
        self.nodes[0].generatetoaddress(110, coinbase_address)

        # Obtaining a master address to work with
        address = self.nodes[0].getnewaddress()

        # Funding the address with some testnet BTC for fees
        self.nodes[0].sendtoaddress(address, 10)
        self.nodes[0].generatetoaddress(1, coinbase_address)

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

        # Create a fixed property
        txid = self.nodes[0].omni_sendissuancefixed(address, 1, 2, 0, "Test Category", "Test Subcategory", "TST", "http://www.omnilayer.org", "", "100000")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get currency ID
        currencyOffered = result['propertyid']

        # A new sell offer can be created with action = 1 (new)
        activeOffersAtTheStart = self.nodes[0].omni_getactivedexsells()
        startBTC = 0.1
        startMSC = "2.5"
        amountOffered = "1.00000000"
        desiredBTC = "0.20000000"

        # Created funded address for test
        fundedAddress = self.nodes[0].getnewaddress()
        txid = self.nodes[0].omni_send(address, fundedAddress, currencyOffered, startMSC)
        self.nodes[0].sendtoaddress(fundedAddress, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # creating an offer with action = 1
        txid = self.nodes[0].omni_senddexsell(fundedAddress, currencyOffered, amountOffered, desiredBTC, stdBlockSpan, stdCommitFee, actionNew)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get and check the offer
        offerTx = self.nodes[0].omni_gettransaction(txid)
        assert_equal(offerTx['txid'], txid)
        assert_equal(offerTx['sendingaddress'], fundedAddress)
        assert_equal(offerTx['version'], 1)
        assert_equal(offerTx['type_int'], 20)
        assert_equal(offerTx['type'], "DEx Sell Offer")
        assert_equal(offerTx['propertyid'], currencyOffered)
        assert_equal(offerTx['divisible'], True)
        assert_equal(offerTx['amount'], amountOffered)
        assert_equal(offerTx['feathercoindesired'], desiredBTC)
        assert_equal(offerTx['timelimit'], stdBlockSpan)
        assert_equal(offerTx['feerequired'], stdCommitFee)
        assert_equal(offerTx['action'], "new")
        assert_equal(offerTx['valid'], True)
        assert_equal(offerTx['confirmations'], 1)

        # A new offer is created on the distributed exchange
        assert_equal(len(self.nodes[0].omni_getactivedexsells()), len(activeOffersAtTheStart) + 1)

        # Offering more tokens than available.
        # This will fail in OmniFeather due to FEATURE_DEXMATH being hard coded, the same is not true for Omnicore itself.

        # Created new funded address for test
        fundedAddress = self.nodes[0].getnewaddress()
        txid = self.nodes[0].omni_send(address, fundedAddress, currencyOffered, startMSC)
        self.nodes[0].sendtoaddress(fundedAddress, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Setup variables
        amountAvailableAtStart = self.nodes[0].omni_getbalance(fundedAddress, currencyOffered)['balance']
        amountOffered = float(amountAvailableAtStart) + 100
        desiredBTC = "50.00000000"

        # the amount offered for sale exceeds the sending address's available balance
        payload = self.nodes[0].omni_createpayload_dexsell(currencyOffered, str(amountOffered), desiredBTC, stdBlockSpan, stdCommitFee, actionNew)
        txid = self.nodes[0].omni_sendrawtx(fundedAddress, payload)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was invalid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)
        assert_equal(result['invalidreason'], "Sender has insufficient balance")

        # The amount offered for sale is reserved from the available balance

        # Setup varaibles
        startBTC = 0.1
        startMSC = "100"
        amountOffered = "90.00000000"
        desiredBTC = "45.00000000"

        # Created new funded address for test
        fundedAddress = self.nodes[0].getnewaddress()
        txid = self.nodes[0].omni_send(address, fundedAddress, currencyOffered, startMSC)
        self.nodes[0].sendtoaddress(fundedAddress, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get balance to compare later
        balanceAtStart = self.nodes[0].omni_getbalance(fundedAddress, currencyOffered)

        # an amount is offered for sale
        txid = self.nodes[0].omni_senddexsell(fundedAddress, currencyOffered, amountOffered, desiredBTC, stdBlockSpan, stdCommitFee, actionNew)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get and check the offer
        offerTx = self.nodes[0].omni_gettransaction(txid)
        offerAmount = offerTx['amount']
        balanceNow = self.nodes[0].omni_getbalance(fundedAddress, currencyOffered)

        assert_equal(float(balanceNow['balance']), float(balanceAtStart['balance']) - float(offerAmount))
        assert_equal(float(balanceNow['reserved']), float(balanceAtStart['reserved']) + float(offerAmount))

        # There can be only one active offer that accepts BTC

        # Setup varaibles
        startBTC = 0.1
        startMSC = "2.5"
        firstOfferMSC = "1"
        firstOfferBTC = "0.2"
        secondOfferMSC = "1.5"
        secondOfferBTC = "0.3"

        # Created new funded address for test
        fundedAddress = self.nodes[0].getnewaddress()
        txid = self.nodes[0].omni_send(address, fundedAddress, currencyOffered, startMSC)
        self.nodes[0].sendtoaddress(fundedAddress, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # there is already an active offer accepting BTC
        txid = self.nodes[0].omni_senddexsell(fundedAddress, currencyOffered, firstOfferMSC, firstOfferBTC, stdBlockSpan, stdCommitFee, actionNew)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # and another offer accepting BTC is made
        payload = self.nodes[0].omni_createpayload_dexsell(currencyOffered, secondOfferMSC, secondOfferBTC, stdBlockSpan, stdCommitFee, actionNew)
        txid = self.nodes[0].omni_sendrawtx(fundedAddress, payload)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        # An offer can be updated with action = 2 (update), and cancelled with action = 3 (cancel)

        # Setup varaibles
        startBTC = 0.1
        startMSC = "1.0"
        offeredMSC = "0.50000000"
        desiredBTC = "0.5"
        updatedMSC = "1.00000000"
        updatedBTC = "2.0"

        # Created new funded address for test
        fundedAddress = self.nodes[0].getnewaddress()
        txid = self.nodes[0].omni_send(address, fundedAddress, currencyOffered, startMSC)
        self.nodes[0].sendtoaddress(fundedAddress, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get balance to compare later
        balanceAtStart = self.nodes[0].omni_getbalance(fundedAddress, currencyOffered)

        # Get offers
        offersAtStart = self.nodes[0].omni_getactivedexsells()

        # creating an offer with action 1
        txid = self.nodes[0].omni_senddexsell(fundedAddress, currencyOffered, offeredMSC, desiredBTC, stdBlockSpan, stdCommitFee, actionNew)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        balanceNow = self.nodes[0].omni_getbalance(fundedAddress, currencyOffered)
        assert_equal(result['valid'], True)
        assert_equal(result['amount'], offeredMSC)
        assert_equal(float(balanceNow['balance']), float(balanceAtStart['balance']) - float(offeredMSC))
        assert_equal(float(balanceNow['reserved']), float(balanceAtStart['reserved']) + float(offeredMSC))
        assert_equal(len(self.nodes[0].omni_getactivedexsells()), len(offersAtStart) + 1)

        # updating an offer with action = 2
        payload = self.nodes[0].omni_createpayload_dexsell(currencyOffered, updatedMSC, updatedBTC, stdBlockSpan, stdCommitFee, actionUpdate)
        txid = self.nodes[0].omni_sendrawtx(fundedAddress, payload)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        balanceNow = self.nodes[0].omni_getbalance(fundedAddress, currencyOffered)
        assert_equal(result['valid'], True)
        assert_equal(result['action'], "update")
        assert_equal(result['amount'], updatedMSC)
        assert_equal(float(balanceNow['balance']), float(balanceAtStart['balance']) - float(updatedMSC))
        assert_equal(float(balanceNow['reserved']), float(balanceAtStart['reserved']) + float(updatedMSC))

        # cancelling an offer with action = 3
        txid = self.nodes[0].omni_senddexsell(fundedAddress, currencyOffered, "0", "0", 0, "0", actionCancel)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        balanceNow = self.nodes[0].omni_getbalance(fundedAddress, currencyOffered)
        assert_equal(result['valid'], True)
        assert_equal(result['action'], "cancel")
        assert_equal(balanceNow['balance'], balanceAtStart['balance'])
        assert_equal(balanceNow['reserved'], balanceAtStart['reserved'])
        assert_equal(len(self.nodes[0].omni_getactivedexsells()), len(offersAtStart))

        # An offer can be accepted with an accept transaction of type 22

        # Setup varaibles
        startBTC = 0.1
        startMSC = "0.1"
        offeredMSC = "0.05000000"
        desiredBTC = "0.07"

        # Created new funded address for test
        actorA = self.nodes[0].getnewaddress()
        txid = self.nodes[0].omni_send(address, actorA, currencyOffered, startMSC)
        self.nodes[0].sendtoaddress(actorA, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # A offers MSC
        txid = self.nodes[0].omni_senddexsell(actorA, currencyOffered, offeredMSC, desiredBTC, stdBlockSpan, stdCommitFee, actionNew)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        actorB = self.nodes[0].getnewaddress()
        self.nodes[0].sendtoaddress(actorB, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # B accepts the offer
        txid = self.nodes[0].omni_senddexaccept(actorB, actorA, currencyOffered, offeredMSC, False)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)
        assert_equal(result['txid'], txid)
        assert_equal(result['sendingaddress'], actorB)
        assert_equal(result['referenceaddress'], actorA)
        assert_equal(result['version'], 0)
        assert_equal(result['type_int'], 22)
        assert_equal(result['type'], "DEx Accept Offer")
        assert_equal(result['propertyid'], currencyOffered)
        assert_equal(result['divisible'], True)
        assert_equal(result['amount'], offeredMSC)
        assert_equal(result['confirmations'], 1)

if __name__ == '__main__':
    OmniFreeDExSpec().main()
