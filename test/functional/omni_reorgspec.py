#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test basic omni spec."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal

class OmniReorgSpec(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

    def run_test(self):
        self.log.info("test basic omni spec")

        # Preparing some mature Bitcoins
        coinbase_address = self.nodes[0].getnewaddress()
        new_coinbase_address = self.nodes[0].getnewaddress() # To avoid duplicate block hash
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
        currencyID = result['propertyid']

        # Setup variables
        startBTC = "1.0"
        sendAmount = "0.1"
        startOMNI = "0.20000000"
        receiverAddress = self.nodes[0].getnewaddress()
        senderAddress = self.nodes[0].getnewaddress()

        # Fund new address
        txid = self.nodes[0].omni_send(address, senderAddress, currencyID, startOMNI)
        self.nodes[0].sendtoaddress(senderAddress, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get height to use later
        blockCountBeforeSend = self.nodes[0].getblockcount()

        # broadcasting and confirming a simple send
        txid = self.nodes[0].omni_send(senderAddress, receiverAddress, currencyID, sendAmount)
        blockHashOfSend = self.nodes[0].generatetoaddress(1, coinbase_address)[0]

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # invalidating the block with the send transaction
        self.nodes[0].invalidateblock(blockHashOfSend)

        # the send transaction is no longer confirmed
        assert_equal(self.nodes[0].getblockcount(), blockCountBeforeSend)
        result = self.nodes[0].gettransaction(txid)
        assert_equal(result['confirmations'], 0)

        # a new block is mined
        self.nodes[0].clearmempool()
        self.nodes[0].generatetoaddress(1, new_coinbase_address)

        # the send transaction is no longer valid
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        # After invalidating a simple send, the original balances are restored
        blockHashBeforeFunding = self.nodes[0].generatetoaddress(1, coinbase_address)[0]
        receiverAddress = self.nodes[0].getnewaddress()
        senderAddress = self.nodes[0].getnewaddress()

        # Fund new address
        txid = self.nodes[0].omni_send(address, senderAddress, currencyID, startOMNI)
        self.nodes[0].sendtoaddress(senderAddress, startBTC)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get values to compare later
        balanceBeforeSendActor = self.nodes[0].omni_getbalance(senderAddress, currencyID)
        balanceBeforeSendReceiver = self.nodes[0].omni_getbalance(receiverAddress, currencyID)

        # broadcasting and confirming a simple send
        txid = self.nodes[0].omni_send(senderAddress, receiverAddress, currencyID, sendAmount)
        blockHashOfSend = self.nodes[0].generatetoaddress(1, coinbase_address)[0]

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # the transaction is valid and the tokens were transferred
        assert_equal(float(self.nodes[0].omni_getbalance(senderAddress, currencyID)['balance']), float(balanceBeforeSendActor['balance']) - float(sendAmount))
        assert_equal(float(self.nodes[0].omni_getbalance(receiverAddress, currencyID)['balance']), float(balanceBeforeSendReceiver['balance']) + float(sendAmount))

        # the transaction is valid and the tokens were transferred
        self.nodes[0].invalidateblock(blockHashOfSend)
        self.nodes[0].clearmempool()
        self.nodes[0].generatetoaddress(1, new_coinbase_address)

        # the send transaction is no longer valid and the balances before the send are restored
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)
        assert_equal(self.nodes[0].omni_getbalance(senderAddress, currencyID), balanceBeforeSendActor)
        assert_equal(self.nodes[0].omni_getbalance(receiverAddress, currencyID), balanceBeforeSendReceiver)

        # rolling back all blocks until before the initial funding
        self.nodes[0].invalidateblock(blockHashBeforeFunding)
        self.nodes[0].clearmempool()
        self.nodes[0].generatetoaddress(1, new_coinbase_address)

        # the actors have zero balances
        assert_equal(self.nodes[0].omni_getbalance(senderAddress, currencyID)['balance'], "0.00000000")
        assert_equal(self.nodes[0].omni_getbalance(receiverAddress, currencyID)['balance'], "0.00000000")

        # After invalidating the creation tokens, the transaction and the tokens are invalid

        # Obtaining a master address to work with
        actorAddress = self.nodes[0].getnewaddress()

        # Funding the address with some testnet BTC for fees
        self.nodes[0].sendtoaddress(actorAddress, 1.0)
        self.nodes[0].sendtoaddress(actorAddress, 1.0)
        self.nodes[0].sendtoaddress(actorAddress, 1.0)
        self.nodes[0].sendtoaddress(actorAddress, 1.0)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        params = [{"ecosystem": 1, "value": "150", "indivisible": 1, "extraBlocks": 51, "expectedCurrencyID": str(int(currencyID) + 1)},
                  {"ecosystem": 1, "value": "1.00000000", "indivisible": 2, "extraBlocks": 51, "expectedCurrencyID": str(int(currencyID) + 1)},
                  {"ecosystem": 2, "value": "350", "indivisible": 1, "extraBlocks": 51, "expectedCurrencyID": str(2147483651)},
                  {"ecosystem": 2, "value": "2.50000000", "indivisible": 2, "extraBlocks": 51, "expectedCurrencyID": str(2147483651)}]

        for settings in params:
            # Note number of properties at start
            propertyListAtStart = len(self.nodes[0].omni_listproperties())

            # Create a fixed property
            txid = self.nodes[0].omni_sendissuancefixed(actorAddress, settings["ecosystem"], settings["indivisible"], 0, "Test Category", "Test Subcategory", "TST2", "http://www.omnilayer.org", "", settings["value"])
            blockHashOfCreation = self.nodes[0].generatetoaddress(1, coinbase_address)[0]

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)

            # a new property was created
            assert_equal(len(self.nodes[0].omni_listproperties()), propertyListAtStart + 1)

            # the created property is in the correct ecosystem
            newCurrencyID = int(result['propertyid'])
            if newCurrencyID <= 2147483650:
                ecosystem = 1
            else:
                ecosystem = 2
            assert_equal(settings["ecosystem"], ecosystem)

            # it has the expected next currency identifier
            assert_equal(int(settings["expectedCurrencyID"]), newCurrencyID)

            # the creator was credited with the correct amount of created tokens
            assert_equal(self.nodes[0].omni_getbalance(actorAddress, newCurrencyID)['balance'], settings["value"])

            # invalidating the block and property creation transaction after zero or more blocks
            for i in range(0, settings["extraBlocks"]):
                self.nodes[0].generatetoaddress(1, coinbase_address)
            self.nodes[0].invalidateblock(blockHashOfCreation)
            self.nodes[0].generatetoaddress(1, new_coinbase_address)

            # the transaction is no longer valid
            result = self.nodes[0].gettransaction(txid)
            assert_equal(result['confirmations'], 0)

            # the created property is no longer listed
            assert_equal(len(self.nodes[0].omni_listproperties()), propertyListAtStart)

            # no information about the property is available
            error = False
            try:
                self.nodes[0].omni_getproperty(newCurrencyID) # Expect JSON exception when currency not found
            except:
                error = True
            assert_equal(error, True)

            # no balance information for the property
            error = False
            try:
                self.nodes[0].omni_getbalance(actorAddress, newCurrencyID) # Expect JSON exception when currency not found
            except:
                error = True
            assert_equal(error, True)

        # After invalidating a send to owners transaction, the transaction is invalid

        # Funding the master address with some testnet BTC for fees
        self.nodes[0].sendtoaddress(address, 10)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Obtaining a new address to work with
        senderAddress = self.nodes[0].getnewaddress()

        # Import exodus address
        self.nodes[0].importprivkey("cV35DD5QsWnFDF9B3tAaZjFgC8FRXBuTpLSE1wf734MgKiJFDLtx")

        # Funding the exodus and senderAddress
        txid = self.nodes[0].omni_send(address, senderAddress, currencyID, startOMNI)
        self.nodes[0].sendtoaddress("mgimY5b4MTXRdc9LgQk9KYQtB37W4UmKwT", 1.0)
        self.nodes[0].generatetoaddress(1, coinbase_address)
        self.nodes[0].sendtoaddress(senderAddress, 1.0)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Send some FEATHER to senderAddress to pay STO fees
        txid = self.nodes[0].omni_send("mgimY5b4MTXRdc9LgQk9KYQtB37W4UmKwT", senderAddress, 3, "0.2")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Setup variables
        sendAmount = "0.1"

        # broadcasting and confirming a send to owners transaction
        txid = self.nodes[0].omni_sendsto(senderAddress, currencyID, sendAmount)
        blockHashOfSend = self.nodes[0].generatetoaddress(1, coinbase_address)[0]

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # invalidating the block and send to owners transaction
        self.nodes[0].invalidateblock(blockHashOfSend)
        self.nodes[0].clearmempool()
        self.nodes[0].generatetoaddress(1, new_coinbase_address)

        # Checking the transaction was not valid...
        result = self.nodes[0].gettransaction(txid)
        assert_equal(result['confirmations'], 0)

        # After invalidating a send to owners transaction, the original balances are restored

        # Obtaining a new addresses to work with
        senderAddress = self.nodes[0].getnewaddress()
        dummyOwnerA = self.nodes[0].getnewaddress()
        dummyOwnerB = self.nodes[0].getnewaddress()
        dummyOwnerC = self.nodes[0].getnewaddress()

        # Funding the senderAddress with some FTC and FEATHER for fees
        txid = self.nodes[0].omni_send("mgimY5b4MTXRdc9LgQk9KYQtB37W4UmKwT", senderAddress, 3, "0.2")
        self.nodes[0].sendtoaddress(senderAddress, 1.0)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Create a fixed property
        txid = self.nodes[0].omni_sendissuancefixed(senderAddress, 1, 1, 0, "Test Category", "Test Subcategory", "TST3", "http://www.omnilayer.org", "", "153")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get currency ID
        newCurrencyID = result['propertyid']

        # funding the owners with a new property
        self.nodes[0].omni_send(senderAddress, dummyOwnerA, newCurrencyID, "1")
        self.nodes[0].omni_send(senderAddress, dummyOwnerB, newCurrencyID, "1")
        self.nodes[0].omni_send(senderAddress, dummyOwnerC, newCurrencyID, "1")
        blockHashOfOwnerFunding = self.nodes[0].generatetoaddress(1, coinbase_address)[0]

        # the owners have some balance
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerA, newCurrencyID)['balance'], "1")
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerB, newCurrencyID)['balance'], "1")
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerC, newCurrencyID)['balance'], "1")

        # the sender has less
        assert_equal(self.nodes[0].omni_getbalance(senderAddress, newCurrencyID)['balance'], "150")

        # sending to the owners
        txid = self.nodes[0].omni_sendsto(senderAddress, newCurrencyID, "150")
        blockHashOfSend = self.nodes[0].generatetoaddress(1, coinbase_address)[0]

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        print(result)
        assert_equal(result['valid'], True)

        # the owners have some balance
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerA, newCurrencyID)['balance'], "51")
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerB, newCurrencyID)['balance'], "51")
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerC, newCurrencyID)['balance'], "51")

        # the sender has less
        assert_equal(self.nodes[0].omni_getbalance(senderAddress, newCurrencyID)['balance'], "0")

        # invalidating the block and send to owners transaction
        self.nodes[0].invalidateblock(blockHashOfSend)
        self.nodes[0].clearmempool()
        self.nodes[0].generatetoaddress(1, new_coinbase_address)

        # Checking the transaction was not valid...
        result = self.nodes[0].gettransaction(txid)
        assert_equal(result['confirmations'], 0)

        # the owners no longer have the tokens they received
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerA, newCurrencyID)['balance'], "1")
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerB, newCurrencyID)['balance'], "1")
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerC, newCurrencyID)['balance'], "1")

        # the sender has the balance from before the send to owners transaction
        assert_equal(self.nodes[0].omni_getbalance(senderAddress, newCurrencyID)['balance'], "150")

        # rolling back until before the funding of the owners
        self.nodes[0].invalidateblock(blockHashOfOwnerFunding)
        self.nodes[0].clearmempool()
        self.nodes[0].generatetoaddress(1, new_coinbase_address)

        # the owners have no tokens
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerA, newCurrencyID)['balance'], "0")
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerB, newCurrencyID)['balance'], "0")
        assert_equal(self.nodes[0].omni_getbalance(dummyOwnerC, newCurrencyID)['balance'], "0")

        # the sender has less
        assert_equal(self.nodes[0].omni_getbalance(senderAddress, newCurrencyID)['balance'], "153")

        # Historical STO transactions are not affected by reorganizations

        # Obtaining a new addresses to work with
        actorAddress = self.nodes[0].getnewaddress()
        ownerA = self.nodes[0].getnewaddress()
        ownerB = self.nodes[0].getnewaddress()

        # Send some FEATHER to actorAddress to pay STO fees
        txid = self.nodes[0].omni_send("mgimY5b4MTXRdc9LgQk9KYQtB37W4UmKwT", actorAddress, 3, "0.2")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Funding the actorAddress with some testnet BTC for fees
        self.nodes[0].sendtoaddress(actorAddress, 1.0)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Create a fixed property
        txid = self.nodes[0].omni_sendissuancefixed(actorAddress, 1, 2, 0, "Test Category", "Test Subcategory", "TST4", "http://www.omnilayer.org", "", "100")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checking the transaction was valid...
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], True)

        # Get currency ID
        newCurrencyID = result['propertyid']

        # funding the owners with a new property
        self.nodes[0].omni_send(actorAddress, ownerA, newCurrencyID, "10")
        self.nodes[0].omni_send(actorAddress, ownerB, newCurrencyID, "10")
        self.nodes[0].generatetoaddress(1, coinbase_address)

        # Checks
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, newCurrencyID)['balance'], "80.00000000")
        assert_equal(self.nodes[0].omni_getbalance(ownerA, newCurrencyID)['balance'], "10.00000000")
        assert_equal(self.nodes[0].omni_getbalance(ownerB, newCurrencyID)['balance'], "10.00000000")

        # sending the first STO transaction
        firstTxid = self.nodes[0].omni_sendsto(actorAddress, newCurrencyID, "30")
        blockHashOfSend = self.nodes[0].generatetoaddress(1, coinbase_address)[0]

        # Checking the transaction was valid...
        result = self.nodes[0].omni_getsto(firstTxid)
        assert_equal(result['txid'], firstTxid)
        assert_equal(result['sendingaddress'], actorAddress)
        assert_equal(result['valid'], True)
        assert_equal(result['version'], 0)
        assert_equal(result['type_int'], 3)
        assert_equal(result['propertyid'], newCurrencyID)
        assert_equal(result['divisible'], True)
        assert_equal(result['totalstofee'], "0.00000002")
        assert_equal(result['amount'], "30.00000000")
        assert_equal(len(result['recipients']), 2)
        found = False
        for recipient in result['recipients']:
            if recipient['address'] == ownerA:
                found = True
            elif recipient['address'] == ownerB:
                found = True
            assert_equal(found, True)
        assert_equal(result['recipients'][0]['amount'], "15.00000000")
        assert_equal(result['recipients'][1]['amount'], "15.00000000")

        # two owners received tokens
        assert_equal(self.nodes[0].omni_getbalance(ownerA, newCurrencyID)['balance'], "25.00000000")
        assert_equal(self.nodes[0].omni_getbalance(ownerB, newCurrencyID)['balance'], "25.00000000")

        # the actor was charged
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, newCurrencyID)['balance'], "50.00000000")

        # sending a second STO transaction
        txid = self.nodes[0].omni_sendsto(actorAddress, newCurrencyID, "30")
        blockHashOfSecond = self.nodes[0].generatetoaddress(1, coinbase_address)[0]

        # invalidating the block with the second STO transaction
        self.nodes[0].invalidateblock(blockHashOfSecond)
        self.nodes[0].clearmempool()
        self.nodes[0].generatetoaddress(1, new_coinbase_address)

        # the send to owners transaction is no longer valid
        result = self.nodes[0].omni_gettransaction(txid)
        assert_equal(result['valid'], False)

        # creating a third STO transaction
        self.nodes[0].sendtoaddress(actorAddress, 1.0)
        self.nodes[0].generatetoaddress(1, coinbase_address)
        txid = self.nodes[0].omni_sendsto(actorAddress, newCurrencyID, "50")
        self.nodes[0].generatetoaddress(1, coinbase_address)
        result = self.nodes[0].omni_getsto(txid)

        # the third STO transaction is valid
        assert_equal(result['amount'], "50.00000000")
        assert_equal(result['valid'], True)
        assert_equal(len(result['recipients']), 2)
        found = False
        for recipient in result['recipients']:
            if recipient['address'] == ownerA:
                found = True
            elif recipient['address'] == ownerB:
                found = True
            assert_equal(found, True)
        assert_equal(result['recipients'][0]['amount'], "25.00000000")
        assert_equal(result['recipients'][1]['amount'], "25.00000000")

        # checking the first STO transaction once more
        result = self.nodes[0].omni_getsto(firstTxid)

        # the information for the first transaction is still the same
        assert_equal(result['valid'], True)
        assert_equal(result['amount'], "30.00000000")
        assert_equal(len(result['recipients']), 2)
        found = False
        for recipient in result['recipients']:
            if recipient['address'] == ownerA:
                found = True
            elif recipient['address'] == ownerB:
                found = True
            assert_equal(found, True)
        assert_equal(result['recipients'][0]['amount'], "15.00000000")
        assert_equal(result['recipients'][1]['amount'], "15.00000000")

        # the final balances as expected
        assert_equal(self.nodes[0].omni_getbalance(actorAddress, newCurrencyID)['balance'], "0.00000000")
        assert_equal(self.nodes[0].omni_getbalance(ownerA, newCurrencyID)['balance'], "50.00000000")
        assert_equal(self.nodes[0].omni_getbalance(ownerB, newCurrencyID)['balance'], "50.00000000")

if __name__ == '__main__':
    OmniReorgSpec().main()
