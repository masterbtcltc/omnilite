#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test smart and managed properties."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

class OmniSmartManagedSpec(BitcoinTestFramework):
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

        # Create smart property with divisible units
        txid = self.nodes[0].omni_sendissuancefixed(address, 1, 2, 0, "Test Category", "Test Subcategory", "TST", "http://www.omnilayer.org", "", "3.14159265")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)
        assert_equal(result['confirmations'], 1)
        assert_equal(result['divisible'], True)
        assert_equal(result['amount'], "3.14159265")

        # Get currency ID
        currencyID = result['propertyid']

        # is in the main ecosystem
        if currencyID <= 2147483650:
            ecosystem = 1
        else:
            ecosystem = 2
        assert_equal(ecosystem, 1)

        # this amount was credited to the issuer
        balance = self.nodes[0].omni_getbalance(address, currencyID)['balance']
        assert_equal(balance, "3.14159265")

        # Create test property with indivisible units
        txid = self.nodes[0].omni_sendissuancefixed(address, 2, 1, 0, "Test Category", "Test Subcategory", "TST", "http://www.omnilayer.org", "", "4815162342")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)
        assert_equal(result['confirmations'], 1)
        assert_equal(result['divisible'], False)
        assert_equal(result['amount'], "4815162342")

        # Get currency ID
        currencyID = result['propertyid']

        # is in the main ecosystem
        if currencyID <= 2147483650:
            ecosystem = 1
        else:
            ecosystem = 2
        assert_equal(ecosystem, 2)

        # this amount was credited to the issuer
        balance = self.nodes[0].omni_getbalance(address, currencyID)['balance']
        assert_equal(balance, "4815162342")

        # Setup variables for managed tests
        startBTC = "0.1"
        zeroAmount = "0"
        actorAddress = self.nodes[0].getnewaddress()
        otherAddress = self.nodes[0].getnewaddress()
        self.nodes[0].sendtoaddress(actorAddress, startBTC)
        self.nodes[0].sendtoaddress(otherAddress, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Create a fixed property
        txid = self.nodes[0].omni_sendissuancefixed(actorAddress, 1, 2, 0, "Test Category", "Test Subcategory", "TST", "http://www.omnilayer.org", "", "10")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get currency ID
        nonManagedID = result['propertyid']

        # A managed property can be created with transaction type 54
        numProperties = len(self.nodes[0].omni_listproperties())
        txid = self.nodes[0].omni_sendissuancemanaged(actorAddress, 1, 1, 0, "Test Category", "Test Subcategory", "ManagedTokens", "http://www.omnilayer.org", "This is a test for managed properties")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)
        assert_equal(result['txid'], txid)
        assert_equal(result['type_int'], 54)
        assert_equal(result['divisible'], False)
        assert_equal(result['propertyname'], "ManagedTokens")
        assert_equal(result['amount'], "0")
        assert_equal(len(self.nodes[0].omni_listproperties()), numProperties + 1)

        # Get currency ID
        currencyID = result['propertyid']

        # A managed property has a category, subcategory, name, website and description
        propertyInfo = self.nodes[0].omni_getproperty(currencyID)
        assert_equal(propertyInfo['propertyid'], currencyID)
        assert_equal(propertyInfo['divisible'], False)
        assert_equal(propertyInfo['name'], "ManagedTokens")
        assert_equal(propertyInfo['category'], "Test Category")
        assert_equal(propertyInfo['subcategory'], "Test Subcategory")
        assert_equal(propertyInfo['url'], "http://www.omnilayer.org")
        assert_equal(propertyInfo['data'], "This is a test for managed properties")

        # A managed property has no fixed supply and starts with 0 tokens
        assert_equal(propertyInfo['fixedissuance'], False)
        assert_equal(propertyInfo['totaltokens'], "0")

        balanceForId = self.nodes[0].omni_getallbalancesforid(currencyID)
        balanceForAddress = self.nodes[0].omni_getbalance(actorAddress, currencyID)

        assert_equal(len(balanceForId), 0)
        assert_equal(balanceForAddress['balance'], zeroAmount)
        assert_equal(balanceForAddress['reserved'], zeroAmount)

        # A reference to the issuer and creation transaction is available
        assert_equal(propertyInfo['issuer'], actorAddress)
        assert_equal(propertyInfo['creationtxid'], txid)

        # New tokens can be granted with transaction type 55
        txid = self.nodes[0].omni_sendgrant(actorAddress, "", currencyID, "100")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['txid'], txid)
        assert_equal(result['valid'], True)
        assert_equal(result['type_int'], 55)
        assert_equal(result['propertyid'], currencyID)
        assert_equal(result['divisible'], False)
        assert_equal(result['amount'], "100")

        # Granting tokens increases the total number of tokens
        propertyInfo = self.nodes[0].omni_getproperty(currencyID)
        assert_equal(propertyInfo['totaltokens'], "100")

        # Granting tokens increases the issuer's balance
        balance = self.nodes[0].omni_getbalance(actorAddress, currencyID)

        assert_equal(balance['balance'], "100")
        assert_equal(balance['reserved'], zeroAmount)

        # Tokens can be granted several times
        txid = self.nodes[0].omni_sendgrant(actorAddress, "", currencyID, "170")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['txid'], txid)
        assert_equal(result['valid'], True)
        assert_equal(result['type_int'], 55)
        assert_equal(result['propertyid'], currencyID)
        assert_equal(result['divisible'], False)
        assert_equal(result['amount'], "170")

        propertyInfo = self.nodes[0].omni_getproperty(currencyID)
        assert_equal(propertyInfo['totaltokens'], "270")
        balance = self.nodes[0].omni_getbalance(actorAddress, currencyID)
        assert_equal(balance['balance'], "270")

        # It's impossible to grant tokens for an non-existing property
        grantRawTx = "00000037" + format(2147483647, '08x') + format(1, '016x') + "00"
        txid = self.nodes[0].omni_sendrawtx(actorAddress, grantRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was invalid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        # Granting tokens for a property with fixed supply is invalid
        oldTotalTokens = self.nodes[0].omni_getproperty(nonManagedID)['totaltokens']
        oldBalance = self.nodes[0].omni_getbalance(actorAddress, nonManagedID)

        # Granting tokens for a property with fixed supply is invalid
        oldTotalTokens = self.nodes[0].omni_getproperty(nonManagedID)['totaltokens']
        oldBalance = self.nodes[0].omni_getbalance(actorAddress, nonManagedID)

        grantRawTx = "00000037" + format(nonManagedID, '08x') + format(1, '016x') + "00"
        txid = self.nodes[0].omni_sendrawtx(actorAddress, grantRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was invalid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        assert_equal(self.nodes[0].omni_getproperty(nonManagedID)['totaltokens'], oldTotalTokens)
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, nonManagedID), oldBalance)

        # Tokens can only be granted by the issuer on record
        grantRawTx = "00000037" + format(currencyID, '08x') + format(500, '016x') + "00"
        txid = self.nodes[0].omni_sendrawtx(otherAddress, grantRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was invalid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        propertyInfo = self.nodes[0].omni_getproperty(currencyID)
        assert_equal(propertyInfo['totaltokens'], "270")
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['balance'], "270")
        assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyID)['balance'], zeroAmount)

        # Up to a total of 9223372036854775807 tokens can be granted
        txid = self.nodes[0].omni_sendgrant(actorAddress, "", currencyID, "9223372036854775537")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)
        assert_equal(result['amount'], "9223372036854775537")

        assert_equal(self.nodes[0].omni_getproperty(currencyID)['totaltokens'], "9223372036854775807")
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['balance'], "9223372036854775807")

        # Granted tokens can be transfered as usual
        txid = self.nodes[0].omni_send(actorAddress, otherAddress, currencyID, "1")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        assert_equal(self.nodes[0].omni_getproperty(currencyID)['totaltokens'], "9223372036854775807")
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['balance'], "9223372036854775806")
        assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyID)['balance'], "1")

        # Tokens of managed properties can be revoked with transaction type 56
        txid = self.nodes[0].omni_sendrevoke(actorAddress, currencyID, "9223372036854775805")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['txid'], txid)
        assert_equal(result['valid'], True)
        assert_equal(result['type_int'], 56)
        assert_equal(result['propertyid'], currencyID)
        assert_equal(result['divisible'], False)
        assert_equal(result['amount'], "9223372036854775805")

        # Revoking tokens decreases the total number of tokens
        assert_equal(self.nodes[0].omni_getproperty(currencyID)['totaltokens'], "2")

        # Revoking tokens decreases the issuer's balance
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID)['balance'], "1")

        # It's impossible to revoke tokens for an non-existing property
        revokeRawTx = "00000038" + format(2147483647, '08x') + format(500, '016x') + "00"
        txid = self.nodes[0].omni_sendrawtx(actorAddress, revokeRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        # Revoking tokens for a property with fixed supply is invalid
        oldTotalTokens = self.nodes[0].omni_getproperty(nonManagedID)['totaltokens']
        oldBalance = self.nodes[0].omni_getbalance(actorAddress, nonManagedID)

        revokeRawTx = "00000038" + format(nonManagedID, '08x') + format(1, '016x') + "00"
        txid = self.nodes[0].omni_sendrawtx(actorAddress, revokeRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        assert_equal(self.nodes[0].omni_getproperty(nonManagedID)['totaltokens'], oldTotalTokens)
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, nonManagedID), oldBalance)

        # Revoking more tokens than available is not possible
        oldTotalTokens = self.nodes[0].omni_getproperty(currencyID)['totaltokens']
        oldActorBalance = self.nodes[0].omni_getbalance(actorAddress, currencyID)
        oldOtherBalance = self.nodes[0].omni_getbalance(otherAddress, currencyID)

        revokeRawTx = "00000038" + format(currencyID, '08x') + format(100, '016x') + "00"
        txid = self.nodes[0].omni_sendrawtx(actorAddress, revokeRawTx)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        assert_equal(self.nodes[0].omni_getproperty(currencyID)['totaltokens'], oldTotalTokens)
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, currencyID), oldActorBalance)
        assert_equal(self.nodes[0].omni_getbalance(otherAddress, currencyID), oldOtherBalance)

if __name__ == '__main__':
    OmniSmartManagedSpec().main()
