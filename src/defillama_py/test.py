from client import Llama

# create a DefiLlama instance
obj = Llama()

# get historical DeFi TVL on all chains
# print(obj.get_all_protocols_current_tvl())

# df = obj.get_protocol_current_tvl('velodrome')
# df = obj.get_all_protocols_current_tvl()
# df = obj.get_protocol_historical_tvl('velodrome')
# df = obj.get_chain_historical_tvl('arbitrum')
# df = obj.get_all_chains_current_tvl()
# df = obj.get_all_chains_historical_tvl()



print(df)
# df.to_csv('test.csv')
