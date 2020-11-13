OmniFeather
=========================================

[![Build Status](https://travis-ci.org/OmniLayer/omnifeather.svg?branch=master)](https://travis-ci.org/OmniLayer/omnifeather)

What is the Omni Layer
----------------------

The Omni Layer is a communications protocol that uses the Feathercoin block chain to enable Smart Properties (tokens) and a Decentralized Exchange. A common analogy that is used to describe the relation of the Omni Layer to Feathercoin is that of HTTP to TCP/IP: HTTP, like the Omni Layer, is the application layer to the more fundamental transport and internet layer of TCP/IP, like Feathercoin.

What is OmniFeather
-----------------

OmniFeather is a fast, portable Omni Layer implementation that is based off the Feathercoin codebase (currently 0.18.1). This implementation requires no external dependencies extraneous to Feathercoin, and is native to the Feathercoin network just like other Feathercoin nodes. It currently supports a wallet mode and is seamlessly available on three platforms: Windows, Linux and MacOS. Omni Layer extensions are exposed via the JSON-RPC interface. Development has been consolidated on the OmniFeather product, and it is the reference client for the Omni Layer.

Telegram: https://t.me/FeathercoinOfficial  
Twitter: https://twitter.com/Feathercoin  
Forum: http://forum.feathercoin.com/

Current feature set:
--------------------

* Broadcasting of simple send (tx 0) [doc](src/omnicore/doc/rpc-api.md#omni_send), and send to owners (tx 3) [doc](src/omnicore/doc/rpc-api.md#omni_sendsto)

* Obtaining a Omni Layer balance [doc](src/omnicore/doc/rpc-api.md#omni_getbalance)

* Obtaining all balances (including smart property) for an address [doc](src/omnicore/doc/rpc-api.md#omni_getallbalancesforaddress)

* Obtaining all balances associated with a specific smart property [doc](src/omnicore/doc/rpc-api.md#omni_getallbalancesforid)

* Retrieving information about any Omni Layer transaction [doc](src/omnicore/doc/rpc-api.md#omni_gettransaction)

* Listing historical transactions of addresses in the wallet [doc](src/omnicore/doc/rpc-api.md#omni_listtransactions)

* Retrieving detailed information about a smart property [doc](src/omnicore/doc/rpc-api.md#omni_getproperty)

* Retrieving active and expired crowdsale information [doc](src/omnicore/doc/rpc-api.md#omni_getcrowdsale)

* Sending a specific FTC amount to a receiver with referenceamount in `omni_send`

* Creating and broadcasting transactions based on raw Omni Layer transactions with `omni_sendrawtx`

* Functional UI for balances, sending and historical transactions

* Creating any supported transaction type via RPC interface

* Support for class B (multisig) and class C (op-return) encoded transactions

* Support of unconfirmed transactions

* Creation of raw transactions with non-wallet inputs

Support:
--------

* [GitHub](https://github.com/FeatherCoin/Feathercoin/issues)
* [Telegram](https://t.me/FeathercoinOfficial)
* [Twitter](https://twitter.com/Feathercoin)
* [Forum](http://forum.feathercoin.com/)

Disclaimer, warning
-------------------

This software is EXPERIMENTAL software. USE ON MAINNET AT YOUR OWN RISK.

By default this software will use your existing Feathercoin wallet, including spending feathercoins contained therein (for example for transaction fees or trading).
The protocol and transaction processing rules for the Omni Layer are still under active development and are subject to change in future.
OmniFeather should be considered an beta product, and you use it at your own risk. Neither the Feathercoin Developers, Omni Foundation nor the OmniFeather developers assumes any responsibility for funds misplaced, mishandled, lost, or misallocated.

Further, please note that this installation of OmniFeather should be viewed as EXPERIMENTAL. Your wallet data, feathercoins and Omni Layer tokens may be lost, deleted, or corrupted, with or without warning due to bugs or glitches. Please take caution.

This software is provided open-source at no cost. You are responsible for knowing the law in your country and determining if your use of this software contravenes any local laws.

PLEASE DO NOT use wallet(s) with significant amounts of feathercoins or Omni Layer tokens while testing!
