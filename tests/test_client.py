import pytest
import pandas as pd
from defillama_py.client import Llama

# create a DefiLlama instance
obj = Llama()

# Global test parameters
RAW_VALUES = [True, False]
ADDRESSES = [
    "0x02f7bd798e765369a9d204e9095b2a526ef01667",
    "0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B",
]
BRIDGE_IDS = ["1", "2"]
CHAINS = ["arbitrum", "ethereum", "zksync era"]
COINS = [
    "ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1",
    "bsc:0x762539b45a1dcce3d36d080f74d1aed37844b878",
]
POOLS = ["2c5d3d72-10f5-48f3-be8c-f8f0fa07ba12", "747c1d2a-c668-4682-b9f9-296708a3dd90"]
PROTOCOLS = ["aave", "satori-finance"]
STABLECOINS = ["1", "2"]
TIMESTAMPS = ["1692056796", "1692385206"]

VOLUME_PARAMS = [
    {
        "excludeTotalDataChart": True,
        "excludeTotalDataChartBreakdown": True,
        "dataType": "dailyVolume",
    },
    {
        "excludeTotalDataChart": True,
        "excludeTotalDataChartBreakdown": False,
        "dataType": "dailyVolume",
    },
    {
        "excludeTotalDataChart": False,
        "excludeTotalDataChartBreakdown": False,
        "dataType": "dailyVolume",
    },
    {
        "excludeTotalDataChart": False,
        "excludeTotalDataChartBreakdown": True,
        "dataType": "dailyVolume",
    },
    {
        "excludeTotalDataChart": True,
        "excludeTotalDataChartBreakdown": True,
        "dataType": "totalVolume",
    },
    {
        "excludeTotalDataChart": True,
        "excludeTotalDataChartBreakdown": False,
        "dataType": "totalVolume",
    },
    {
        "excludeTotalDataChart": False,
        "excludeTotalDataChartBreakdown": False,
        "dataType": "totalVolume",
    },
    {
        "excludeTotalDataChart": False,
        "excludeTotalDataChartBreakdown": True,
        "dataType": "totalVolume",
    },
]


# @pytest.mark.parametrize("raw", RAW_VALUES)
# def test_get_all_protocols_current_tvl(raw):
#     response = obj.get_all_protocols_current_tvl(raw)

#     # If raw is True, the response should be a list of dictionaries
#     if raw:
#         assert isinstance(response, list)
#         if response:  # if the list is not empty
#             assert isinstance(response[0], dict)

#     # If raw is False, the response should be a DataFrame
#     else:
#         assert isinstance(response, pd.DataFrame)
#         # Checking for expected columns in the DataFrame
#         assert set(["chain", "protocol", "tvl"]).issubset(response.columns)

#         # Checking if the 'chain' column has been cleaned properly
#         assert all(response['chain'].str.contains(r'[-\s]') == False)


@pytest.mark.parametrize("chains", CHAINS)
@pytest.mark.parametrize("raw", RAW_VALUES)
@pytest.mark.parametrize("params", VOLUME_PARAMS)
def test_get_chain_perps_volume(chains, params, raw):
    # Create an instance of the class
    wrapper_instance = (
        Llama()
    )  # Adjust if you need specific arguments for initialization

    # Handle expected exceptions for invalid combinations
    if not params:
        with pytest.raises(ValueError, match="params dictionary is missing."):
            wrapper_instance.get_chain_perps_volume(chains, params, raw)
        return

    if (
        raw is False
        and params["excludeTotalDataChart"] == params["excludeTotalDataChartBreakdown"]
    ):
        with pytest.raises(
            ValueError,
            match=r"Both excludeTotalDataChart and excludeTotalDataChartBreakdown cannot have the same value \(either both True or both False\) if raw = False\.",
        ):
            wrapper_instance.get_chain_perps_volume(chains, params, raw)
        return

    # Actual testing
    result = wrapper_instance.get_chain_perps_volume(chains, params, raw)

    # Add further assertions to validate the returned result
    # For instance:
    if raw:
        assert isinstance(result, list)
    else:
        assert isinstance(result, pd.DataFrame)
