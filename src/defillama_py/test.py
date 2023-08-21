from client import Llama

# create a DefiLlama instance
obj = Llama()

# df = obj.get_chains()
# df = obj.get_protocols()
# df = obj.get_stablecoins()
# df = obj.get_pools()

# df = obj.get_protocol_current_tvl(['velodrome'])
# df = obj.get_all_protocols_current_tvl(raw=False)

# df = obj.get_protocol_historical_tvl('satori-finance', raw=True)
# df = obj.get_protocol_historical_tvl(['satori-finance','velodrome'], raw=True)
# df = obj.get_protocol_historical_tvl(['satori-finance'], raw=False)
# df = obj.get_protocol_historical_tvl(['satori-finance','velodrome'], raw=False)

# df = obj.get_chain_historical_tvl('arbitrum', raw=True)
# df = obj.get_chain_historical_tvl(['arbitrum', 'zkSync Era'], raw=True)
# df = obj.get_chain_historical_tvl('arbitrum', raw=False)
# df = obj.get_chain_historical_tvl(['arbitrum', 'zkSync Era'], raw=False)

# df = obj.get_all_chains_current_tvl(raw=True)
# df = obj.get_all_chains_current_tvl(raw=False)

# df = obj.get_all_chains_historical_tvl()






print(df)
# df.to_csv('test.csv')
