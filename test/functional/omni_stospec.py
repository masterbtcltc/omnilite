#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test STO spec."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal
from decimal import Decimal

class OmniSTOSpec(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

    def run_test(self):
        self.log.info("test STO spec")

        # Preparing some mature Bitcoins
        coinbase_address = self.nodes[0].getnewaddress()
        self.nodes[0].generatetoaddress(110, coinbase_address)

        # Obtaining a master address to work with
        address = self.nodes[0].getnewaddress()

        # Funding the address with some testnet BTC for fees
        self.nodes[0].sendtoaddress(address, 10)
        self.nodes[0].generatetoaddress(1, coinbase_address)

        NUM_OWNERS = "30" # Was 70 in OmniJ tests but very slow in python!
        params = [{"maxN": NUM_OWNERS, "amountStartPerOwner": "1", "amountDistributePerOwner": "1", "propertyType": 1},
                  {"maxN": NUM_OWNERS, "amountStartPerOwner": "1", "amountDistributePerOwner": "3", "propertyType": 1},
                  {"maxN": NUM_OWNERS, "amountStartPerOwner": "1", "amountDistributePerOwner": "100000000", "propertyType": 1},
                  {"maxN": NUM_OWNERS, "amountStartPerOwner": "100000000", "amountDistributePerOwner": "1", "propertyType": 1},
                  {"maxN": NUM_OWNERS, "amountStartPerOwner": "100000000", "amountDistributePerOwner": "3", "propertyType": 1},
                  {"maxN": NUM_OWNERS, "amountStartPerOwner": "0.00000001", "amountDistributePerOwner": "1.00000000", "propertyType": 2},
                  {"maxN": NUM_OWNERS, "amountStartPerOwner": "0.00000001", "amountDistributePerOwner": "2.00000000", "propertyType": 2},
                  {"maxN": NUM_OWNERS, "amountStartPerOwner": "1.00000000", "amountDistributePerOwner": "0.00000001", "propertyType": 2},
                  {"maxN": NUM_OWNERS, "amountStartPerOwner": "1.00000000", "amountDistributePerOwner": "0.00000002", "propertyType": 2},
                  {"maxN": NUM_OWNERS, "amountStartPerOwner": "1.00000000", "amountDistributePerOwner": "0.50000000", "propertyType": 2},
                  {"maxN": NUM_OWNERS, "amountStartPerOwner": "1.00000000", "amountDistributePerOwner": "3.00000000", "propertyType": 2},
                  {"maxN": "1", "amountStartPerOwner": "1", "amountDistributePerOwner": "9223372036854775806", "propertyType": 1},
                  {"maxN": "1", "amountStartPerOwner": "9223372036854775806", "amountDistributePerOwner": "1", "propertyType": 1},
                  {"maxN": "1", "amountStartPerOwner": "0.00000001", "amountDistributePerOwner": "92233720368.54775806", "propertyType": 2},
                  {"maxN": "1", "amountStartPerOwner": "92233720368.54775806", "amountDistributePerOwner": "0.00000001", "propertyType": 2}]

        for settings in params:
            maxN = Decimal(settings['maxN'])
            propertyType = settings['propertyType']
            amountStartPerOwner = Decimal(settings['amountStartPerOwner'])
            amountDistributePerOwner = Decimal(settings['amountDistributePerOwner'])

            if propertyType == 1:
                print("PropertyType:", propertyType, ": start with n *", amountStartPerOwner, "and send n *", amountDistributePerOwner, "to", maxN, "owners")
            else:
                print("PropertyType:", propertyType, ": start with n *", str(amountStartPerOwner), "and send n *", amountDistributePerOwner, "to", maxN, "owners")

            # Preparation
            fundingSPT = ((maxN * (maxN + 1)) / 2) * (amountStartPerOwner + amountDistributePerOwner)
            if propertyType == 1:
                actorSPT = ((maxN * (maxN + 1)) / 2) * amountDistributePerOwner
            else:
                actorSPT = "{:.8f}".format(((maxN * (maxN + 1)) / 2) * amountDistributePerOwner)

            # Create actor
            actorAddress = self.nodes[0].getnewaddress()
            self.nodes[0].sendtoaddress(actorAddress, "1")
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Create property
            txid = self.nodes[0].omni_sendissuancefixed(actorAddress, 1, settings['propertyType'], 0, "", "", "TST", "", "", str(fundingSPT))
            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Checking the transaction was valid...
            result = self.nodes[0].omni_gettransaction(txid)
            assert_equal(result['valid'], True)

            # Get currency ID
            currencySPT = result['propertyid']

            # Check funding balances of actor
            startingBalanceSPT = self.nodes[0].omni_getbalance(actorAddress, currencySPT)
            assert_equal(Decimal(startingBalanceSPT['balance']), fundingSPT)

            # Create owners
            owners = []
            for n in range(1, int(maxN) + 1):
                index = n - 1
                if propertyType == 1:
                    starting = n * amountStartPerOwner
                else:
                    starting = "{:.8f}".format(n * amountStartPerOwner)
                owners.append(self.nodes[0].getnewaddress())
                self.nodes[0].omni_send(actorAddress, owners[index], currencySPT, str(starting))
                if (index % 10 == 0):
                    self.nodes[0].generatetoaddress(1, coinbase_address)

            self.nodes[0].generatetoaddress(1, coinbase_address)

            # Check starting balances of actor
            reallyBalanceSPT = self.nodes[0].omni_getbalance(actorAddress, currencySPT)
            assert_equal(Decimal(reallyBalanceSPT['balance']), Decimal(actorSPT))

            # Check owner balances
            for n in range(1, int(maxN) + 1):
                index = n - 1
                expectedBalanceOwnerSPT = n * amountStartPerOwner
                startingBalanceOwnerSPT = self.nodes[0].omni_getbalance(owners[index], currencySPT)
                assert_equal(Decimal(startingBalanceOwnerSPT['balance']), expectedBalanceOwnerSPT)

            stoTxid = self.nodes[0].omni_sendsto(actorAddress, currencySPT, actorSPT)
            self.nodes[0].generatetoaddress(1, coinbase_address)

            stoTx = self.nodes[0].omni_gettransaction(stoTxid)
            assert_equal(stoTx['valid'], True)
            assert_equal(stoTx['confirmations'], 1)

            # Check updated owner balances
            for n in range(1, int(maxN) + 1):
                index = n - 1
                expectedFinalBalanceOwnerSPT = n * (amountStartPerOwner + amountDistributePerOwner)
                finalBalanceOwnerSPT = self.nodes[0].omni_getbalance(owners[index], currencySPT)
                assert_equal(Decimal(finalBalanceOwnerSPT['balance']), expectedFinalBalanceOwnerSPT)

            # Check final balances of actor
            finalBalanceSPT = self.nodes[0].omni_getbalance(actorAddress, currencySPT)
            assert_equal(Decimal(finalBalanceSPT['balance']), 0)

if __name__ == '__main__':
    OmniSTOSpec().main()
