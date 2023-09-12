from client import Llama

# create a DefiLlama instance
obj = Llama()

# df = obj.get_chains()
# df = obj.get_protocols()
# df = obj.get_stablecoins()
# df = obj.get_pools()

# df = obj.get_all_protocols_current_tvl(raw=False)
# df = obj.get_protocol_historical_tvl(protocols="velodrome", raw=False)
# df = obj.get_all_chains_historical_tvl(raw=False)
# df = obj.get_protocol_current_tvl(['velodrome'])

# df = obj.get_protocol_current_tvl(['velodrome', 'aave'], raw=False)
# df = obj.get_protocol_current_tvl(['velodrome', 'aave'])

# df = obj.get_chain_historical_tvl(['arbitrum', 'ethereum'], raw=False)

# get_protocol_current_tvl


# df = obj.get_dex_volume(raw=True, params = {
#     "excludeTotalDataChart": False,
#     "excludeTotalDataChartBreakdown": False,
#     "dataType": "dailyVolume"
# })

# df = obj.get_perps_volume(raw=False, params = {
#     "excludeTotalDataChart": True,
#     "excludeTotalDataChartBreakdown": False,
#     "dataType": "dailyVolume"
# })

# df = obj.get_options_volume(raw=False, params = {
#     "excludeTotalDataChart": True,
#     "excludeTotalDataChartBreakdown": False,
#     "dataType": "dailyNotionalVolume"
# })

# df = obj.get_chain_dex_volume(chains=['arbitrum', 'optimism'], raw=False, params = {
#     "excludeTotalDataChart": False,
#     "excludeTotalDataChartBreakdown": True,
#     "dataType": "dailyVolume"
# })

# df = obj.get_chain_dex_volume(chains=['arbitrum', 'optimism'], raw=False, params = {
#     "excludeTotalDataChart": True,
#     "excludeTotalDataChartBreakdown": False,
#     "dataType": "dailyVolume"
# })


# df = obj.get_protocol_options_volume('lyra', raw=False, params = {
#     "excludeTotalDataChart": False,
#     "excludeTotalDataChartBreakdown": True,
#     "dataType": "dailyVolume"
# })

# df = obj.get_protocol_fees_revenue('uniswap', raw=False, params = {
#     "excludeTotalDataChart": True,
#     "excludeTotalDataChartBreakdown": False,
#     "dataType": "dailyFees"
# })


# df = obj.get_chain_fees_revenue(
#     "ethereum",
#     raw=False,
#     params={
#         "excludeTotalDataChart": True,
#         "excludeTotalDataChartBreakdown": False,
#         "dataType": "totalFees",
#     },
# )


df = obj.get_abi(
    params={
        "functions": [
            "0xf43f523a",
            "0x95d89b41",
            "0x95d89b41",
            "0x70a08231",
            "0x70a08231",
        ]
    }
)
# df = obj.get_abi_by_contract('ethereum', '0x02f7bd798e765369a9d204e9095b2a526ef01667',
# params={"functions": ['0xf43f523a','0x95d89b41','0x95d89b41','0x70a08231',
# '0x70a08231']}, raw=True)

# df = obj.get_bridges(params={"includeChains": False}, raw=False)
# df = obj.get_chain_bridge_volume("Ethereum", raw=False)
# df = obj.get_bridge_day_stats(1694347200, ['ethereum'], raw=True)
# df = obj.get_bridge_transactions([1, 2], raw=False)

# df = obj.get_bridge_volume(["1", "2"], raw=True)
# df = obj.get_chain_bridge_volume(["ethereum", "arbitrum"], raw=False)
print(df)
# print(str(df)[:1000])
# df.to_csv('test.csv')
