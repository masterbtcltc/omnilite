#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test crowdsale spec."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

class OmniCrowdSaleSpec(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

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

        # Setup closed crowdsale spec
        actorAddress = self.nodes[0].getnewaddress()
        otherAddress = self.nodes[0].getnewaddress()
        startBTC = "0.10000000"
        startMSC = "1.00000000"
        txidA = self.nodes[0].omni_send(address, actorAddress, currencyB, startMSC)
        txidB = self.nodes[0].omni_send(address, otherAddress, currencyB, startMSC)
        self.nodes[0].sendtoaddress(actorAddress, startBTC)
        self.nodes[0].sendtoaddress(otherAddress, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        resultA = self.nodes[0].omni_gettransaction(txidA)
        resultB = self.nodes[0].omni_gettransaction(txidB)
        assert_equal(resultA['valid'], True)
        assert_equal(resultB['valid'], True)

        txid = self.nodes[0].omni_sendissuancecrowdsale(actorAddress, 2, 2, 0, "", "", "CS", "", "", currencyB, "5", 2147483648, 0, 0)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get currency ID
        currencyID = result['propertyid']

        # Check crowdsale active
        assert_equal(self.nodes[0].omni_getcrowdsale(currencyID)['active'], True)

        txid = self.nodes[0].omni_sendissuancefixed(actorAddress, 2, 2, 0, "Test Category", "Test Subcategory", "TST3", "http://www.omnilayer.org", "", "500")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get currency ID
        nonCrowdsaleID = result['propertyid']

        # Closing a non-existing crowdsale is invalid
        closeSaleRawTx = "00000035" + format(2147483647, '08x')
        txid = self.nodes[0].omni_sendrawtx(actorAddress, closeSaleRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        # Closing a non-crowdsale is invalid
        closeSaleRawTx = "00000035" + format(nonCrowdsaleID, '08x')
        txid = self.nodes[0].omni_sendrawtx(actorAddress, closeSaleRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        # A crowdsale can not be closed by a non-issuer
        closeSaleRawTx = "00000035" + format(currencyID, '08x')
        txid = self.nodes[0].omni_sendrawtx(otherAddress, closeSaleRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        assert_equal(self.nodes[0].omni_getcrowdsale(currencyID)['active'], True)

        # Before closing a crowdsale, tokens can be purchased
        txid = self.nodes[0].omni_send(otherAddress, actorAddress, currencyB, "0.5")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # the transaction is valid
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyB)['balance'], "1.50000000")
        assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyB)['balance'], "0.50000000")

        # tokens were credited to the participant
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['balance'], "0.00000000")
        assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyID)['balance'], "2.50000000")

        # A crowdsale can be closed with transaction type 53
        closeSaleRawTx = "00000035" + format(currencyID, '08x')
        txid = self.nodes[0].omni_sendrawtx(actorAddress, closeSaleRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        assert_equal(self.nodes[0].omni_getcrowdsale(currencyID)['active'], False)

        # A crowdsale can only be closed once
        txid = self.nodes[0].omni_sendrawtx(actorAddress, closeSaleRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        # Sending tokens, after a crowdsale was closed, does not grant tokens
        actorAddressBalance = self.nodes[0].omni_getbalance(actorAddress, currencyID)['balance']
        otherAddressBalance = self.nodes[0].omni_getbalance(otherAddress, currencyID)['balance']

        txid = self.nodes[0].omni_send(otherAddress, actorAddress, currencyB, "0.5")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # the transaction is valid
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyB)['balance'], "2.00000000")
        assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyB)['balance'], "0.00000000")

        # tokens were credited to the participant
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['balance'], actorAddressBalance)
        assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyID)['balance'], otherAddressBalance)

        # Investing TST in a crowdsale with 0.00000001 MDiv per unit

        #    {
        #        "version" : 0,
        #        "type" : 51,
        #        "name" : "MDiv",
        #        "category" : "",
        #        "subcategory" : "",
        #        "data" : "",
        #        "url" : "",
        #        "divisible" : true,
        #        "data" : "",
        #        "propertyiddesired" : 4,
        #        "tokensperunit" : "0.00000001",
        #        "deadline" : 7731414000,
        #        "earlybonus" : 0,
        #        "percenttoissuer" : 0
        #    }

        rawTx = "000000330100020000000000004d44697600000000000004000000000000000100000001ccd403f00000"

        params = [{"amountToInvest": "0.00000001", "expectedBalance": "0.00000000"},
                  {"amountToInvest": "1.00000000", "expectedBalance": "0.00000001"},
                  {"amountToInvest": "2.99999999", "expectedBalance": "0.00000002"}]

        for settings in params:
            issuerAddress = self.nodes[0].getnewaddress()
            investorAddress = self.nodes[0].getnewaddress()
            txid = self.nodes[0].omni_send(address, investorAddress, currencyA, settings['amountToInvest'])
            self.nodes[0].sendtoaddress(issuerAddress, startBTC)
            self.nodes[0].sendtoaddress(investorAddress, startBTC)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)

            # creating a new crowdsale with 0.00000001 MDiv per unit invested
            txid = self.nodes[0].omni_sendrawtx(issuerAddress, rawTx)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # the crowdsale is valid
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)
            assert_equal(result['confirmations'], 1)

            # the crowdsale is active
            propertyId = result['propertyid']
            assert_equal(self.nodes[0].omni_getcrowdsale(propertyId)['active'], True)

            # participant invests
            txid = self.nodes[0].omni_send(investorAddress, issuerAddress, currencyA, settings['amountToInvest'])
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # the investor should get the expected balance MDiv
            assert_equal(self.nodes[0].omni_getbalance(investorAddress, propertyId)['balance'], settings['expectedBalance'])

            # the issuer receives the invested amount
            assert_equal(self.nodes[0].omni_getbalance(issuerAddress, currencyA)['balance'], settings['amountToInvest'])

            # it's a valid crowdsale participation transaction
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['txid'], txid)
            assert_equal(result['sendingaddress'], investorAddress)
            assert_equal(result['referenceaddress'], issuerAddress)
            assert_equal(result['version'], 0)
            assert_equal(result['type_int'], 0)
            assert_equal(result['type'], "Crowdsale Purchase")
            assert_equal(result['propertyid'], currencyA)
            assert_equal(result['divisible'], True)
            assert_equal(result['amount'], settings['amountToInvest'])
            assert_equal(result['purchasedpropertyid'], propertyId)
            assert_equal(result['purchasedpropertyname'], "MDiv")
            assert_equal(result['purchasedpropertydivisible'], True)
            assert_equal(result['purchasedtokens'], settings['expectedBalance'])
            assert_equal(result['issuertokens'], "0.00000000")
            assert_equal(result['valid'], True)

            # retrieving information about the crowdsale
            crowdsale = self.nodes[0].omni_getcrowdsale(propertyId)

            # the information matches the initial creation
            assert_equal(crowdsale['propertyid'], propertyId)
            assert_equal(crowdsale['name'], "MDiv")
            assert_equal(crowdsale['active'], True)
            assert_equal(crowdsale['issuer'], issuerAddress)
            assert_equal(crowdsale['propertyiddesired'], currencyA)
            assert_equal(crowdsale['tokensperunit'], "0.00000001")
            assert_equal(crowdsale['earlybonus'], 0)
            assert_equal(crowdsale['percenttoissuer'], 0)
            assert_equal(crowdsale['deadline'], 7731414000)
            assert_equal(crowdsale['tokensissued'], settings['expectedBalance'])
            assert_equal(crowdsale['addedissuertokens'], "0.00000000")

            closeSaleRawTx = "00000035" + format(propertyId, '08x')
            txid = self.nodes[0].omni_sendrawtx(issuerAddress, closeSaleRawTx)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)

        # Investing TST in a crowdsale with 92233720368.54775807 MDiv per unit

        #    {
        #        "version" : 0,
        #        "type" : 51,
        #        "name" : "MDiv",
        #        "category" : "",
        #        "subcategory" : "",
        #        "data" : "",
        #        "url" : "",
        #        "divisible" : true,
        #        "data" : "",
        #        "propertyiddesired" : 4,
        #        "tokensperunit" : "92233720368.54775807",
        #        "deadline" : 7731414000,
        #        "earlybonus" : 0,
        #        "percenttoissuer" : 0
        #    }

        rawTx = "000000330100020000000000004d446976000000000000047fffffffffffffff00000001ccd403f00000"

        params = [{"amountToInvest": "0.01000000", "expectedBalance": "922337203.68547758", "crowdsaleMaxed": False},
                  {"amountToInvest": "1.00000000", "expectedBalance": "92233720368.54775807", "crowdsaleMaxed": False},
                  {"amountToInvest": "2.00000000", "expectedBalance": "92233720368.54775807", "crowdsaleMaxed": True}]

        for settings in params:
            issuerAddress = self.nodes[0].getnewaddress()
            investorAddress = self.nodes[0].getnewaddress()
            txid = self.nodes[0].omni_send(address, investorAddress, currencyA, settings['amountToInvest'])
            self.nodes[0].sendtoaddress(issuerAddress, startBTC)
            self.nodes[0].sendtoaddress(investorAddress, startBTC)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)

            # creating a new crowdsale with 0.00000001 MDiv per unit invested
            txid = self.nodes[0].omni_sendrawtx(issuerAddress, rawTx)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # the crowdsale is valid
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)
            assert_equal(result['confirmations'], 1)

            # the crowdsale is active
            propertyId = result['propertyid']
            assert_equal(self.nodes[0].omni_getcrowdsale(propertyId)['active'], True)

            # participant invests
            txid = self.nodes[0].omni_send(investorAddress, issuerAddress, currencyA, settings['amountToInvest'])
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # the investor should get the expected balance MDiv
            assert_equal(self.nodes[0].omni_getbalance(investorAddress, propertyId)['balance'], settings['expectedBalance'])

            # the issuer receives the invested amount
            assert_equal(self.nodes[0].omni_getbalance(issuerAddress, currencyA)['balance'], settings['amountToInvest'])

            # it's a valid crowdsale participation transaction
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['txid'], txid)
            assert_equal(result['sendingaddress'], investorAddress)
            assert_equal(result['referenceaddress'], issuerAddress)
            assert_equal(result['version'], 0)
            assert_equal(result['type_int'], 0)
            assert_equal(result['type'], "Crowdsale Purchase")
            assert_equal(result['propertyid'], currencyA)
            assert_equal(result['divisible'], True)
            assert_equal(result['amount'], settings['amountToInvest'])
            assert_equal(result['purchasedpropertyid'], propertyId)
            assert_equal(result['purchasedpropertyname'], "MDiv")
            assert_equal(result['purchasedpropertydivisible'], True)
            assert_equal(result['purchasedtokens'], settings['expectedBalance'])
            assert_equal(result['issuertokens'], "0.00000000")
            assert_equal(result['valid'], True)

            # retrieving information about the crowdsale
            crowdsale = self.nodes[0].omni_getcrowdsale(propertyId)

            # the information matches the initial creation
            assert_equal(crowdsale['propertyid'], propertyId)
            assert_equal(crowdsale['name'], "MDiv")
            assert_equal(crowdsale['active'], not settings['crowdsaleMaxed'])
            assert_equal(crowdsale['issuer'], issuerAddress)
            assert_equal(crowdsale['propertyiddesired'], currencyA)
            assert_equal(crowdsale['tokensperunit'], "92233720368.54775807")
            assert_equal(crowdsale['earlybonus'], 0)
            assert_equal(crowdsale['percenttoissuer'], 0)
            assert_equal(crowdsale['deadline'], 7731414000)
            if (settings['crowdsaleMaxed']):
                assert_equal(crowdsale['closedearly'], True)
                assert_equal(crowdsale['maxtokens'], True)
            assert_equal(crowdsale['tokensissued'], settings['expectedBalance'])
            assert_equal(crowdsale['addedissuertokens'], "0.00000000")

            closeSaleRawTx = "00000035" + format(propertyId, '08x')
            txid = self.nodes[0].omni_sendrawtx(issuerAddress, closeSaleRawTx)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], not settings['crowdsaleMaxed'])

        # Investing TMSC in a crowdsale with 3400 TIndiv per unit yields #expectedBalance TIndiv

        #    {
        #        "version" : 0,
        #        "type" : 51,
        #        "name" : "TIndiv",
        #        "category" : "",
        #        "subcategory" : "",
        #        "data" : "",
        #        "url" : "",
        #        "divisible" : false,
        #        "data" : "",
        #        "propertyiddesired" : 2147483651,
        #        "tokensperunit" : "3400",
        #        "deadline" : 7731414000,
        #        "earlybonus" : 0,
        #        "percenttoissuer" : 0
        #    }

        rawTx = "0000003302000100000000000054496e646976000000800000030000000000000d4800000001ccd403f00000"

        params = [{"amountToInvest": "0.00250000", "expectedBalance": "8"},
                  {"amountToInvest": "0.00500000", "expectedBalance": "17"}]

        for settings in params:
            issuerAddress = self.nodes[0].getnewaddress()
            investorAddress = self.nodes[0].getnewaddress()
            txid = self.nodes[0].omni_send(address, investorAddress, currencyB, settings['amountToInvest'])
            self.nodes[0].sendtoaddress(issuerAddress, startBTC)
            self.nodes[0].sendtoaddress(investorAddress, startBTC)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)

            # creating a new crowdsale with 0.00000001 MDiv per unit invested
            txid = self.nodes[0].omni_sendrawtx(issuerAddress, rawTx)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # the crowdsale is valid
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)
            assert_equal(result['confirmations'], 1)

            # the crowdsale is active
            propertyId = result['propertyid']
            assert_equal(self.nodes[0].omni_getcrowdsale(propertyId)['active'], True)

            # participant invests
            txid = self.nodes[0].omni_send(investorAddress, issuerAddress, currencyB, settings['amountToInvest'])
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # the investor should get the expected balance MDiv
            assert_equal(self.nodes[0].omni_getbalance(investorAddress, propertyId)['balance'], settings['expectedBalance'])

            # the issuer receives the invested amount
            assert_equal(self.nodes[0].omni_getbalance(issuerAddress, currencyB)['balance'], settings['amountToInvest'])

            # it's a valid crowdsale participation transaction
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['txid'], txid)
            assert_equal(result['sendingaddress'], investorAddress)
            assert_equal(result['referenceaddress'], issuerAddress)
            assert_equal(result['version'], 0)
            assert_equal(result['type_int'], 0)
            assert_equal(result['type'], "Crowdsale Purchase")
            assert_equal(result['propertyid'], currencyB)
            assert_equal(result['divisible'], True)
            assert_equal(result['amount'], settings['amountToInvest'])
            assert_equal(result['purchasedpropertyid'], propertyId)
            assert_equal(result['purchasedpropertyname'], "TIndiv")
            assert_equal(result['purchasedpropertydivisible'], False)
            assert_equal(result['purchasedtokens'], settings['expectedBalance'])
            assert_equal(result['issuertokens'], "0")
            assert_equal(result['valid'], True)

            # retrieving information about the crowdsale
            crowdsale = self.nodes[0].omni_getcrowdsale(propertyId)

            # the information matches the initial creation
            assert_equal(crowdsale['propertyid'], propertyId)
            assert_equal(crowdsale['name'], "TIndiv")
            assert_equal(crowdsale['active'], True)
            assert_equal(crowdsale['issuer'], issuerAddress)
            assert_equal(crowdsale['propertyiddesired'], currencyB)
            assert_equal(crowdsale['tokensperunit'], "3400")
            assert_equal(crowdsale['earlybonus'], 0)
            assert_equal(crowdsale['percenttoissuer'], 0)
            assert_equal(crowdsale['deadline'], 7731414000)
            assert_equal(crowdsale['tokensissued'], settings['expectedBalance'])
            assert_equal(crowdsale['addedissuertokens'], "0")

            closeSaleRawTx = "00000035" + format(propertyId, '08x')
            txid = self.nodes[0].omni_sendrawtx(issuerAddress, closeSaleRawTx)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)

if __name__ == '__main__':
    OmniCrowdSaleSpec().main()
