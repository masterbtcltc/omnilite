#include <omnicore/omnicore.h>
#include <omnicore/rules.h>

#include <chainparams.h>
#include <test/test_bitcoin.h>

#include <boost/test/unit_test.hpp>

#include <stdint.h>
#include <string>

using namespace mastercore;

BOOST_FIXTURE_TEST_SUITE(omnicore_params_tests, BasicTestingSetup)

BOOST_AUTO_TEST_CASE(get_params)
{
    const CConsensusParams& params = ConsensusParams();
    BOOST_CHECK_EQUAL(params.MIN_ACTIVATION_BLOCKS, 2048);
}

BOOST_AUTO_TEST_CASE(network_restrictions_main)
{
    const CConsensusParams& params = ConsensusParams("main");
    BOOST_CHECK_EQUAL(params.MSC_STO_BLOCK, 0);
}

BOOST_AUTO_TEST_CASE(network_restrictions_test)
{
    const CConsensusParams& params = ConsensusParams("test");
    BOOST_CHECK_EQUAL(params.MSC_STO_BLOCK, 0);
}

BOOST_AUTO_TEST_CASE(ecosystem_restrictions_main)
{
    // Unit tests and mainnet use the same params
    BOOST_CHECK(!IsTransactionTypeAllowed(0, OMNI_PROPERTY_MSC, MSC_TYPE_OFFER_ACCEPT_A_BET, MP_TX_PKT_V0));
    BOOST_CHECK(IsTransactionTypeAllowed(0, OMNI_PROPERTY_TMSC, MSC_TYPE_OFFER_ACCEPT_A_BET, MP_TX_PKT_V0));
}

BOOST_AUTO_TEST_CASE(ecosystem_restrictions_test)
{
    SelectParams(CBaseChainParams::TESTNET);
    BOOST_CHECK(!IsTransactionTypeAllowed(0, OMNI_PROPERTY_MSC, MSC_TYPE_OFFER_ACCEPT_A_BET, MP_TX_PKT_V0));
    BOOST_CHECK(IsTransactionTypeAllowed(0, OMNI_PROPERTY_TMSC, MSC_TYPE_OFFER_ACCEPT_A_BET, MP_TX_PKT_V0));
    // Restore original
    SelectParams(CBaseChainParams::MAIN);
}

BOOST_AUTO_TEST_SUITE_END()
