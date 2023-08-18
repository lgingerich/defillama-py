import requests
import polars as pl

# TO DO:

# add better method to get chain, protocol, and token slugs
# add functionality for large scale data extraction (i.e. get historical tvl of all dapps across all chains)


# general ordering of methods per category:
# ------ small to big ------
# 1. all xyz current
# 2. specific xyz historical



TVL_URL = VOLUMES_URL = FEES_URL = 'https://api.llama.fi/'
COINS_URL = 'https://coins.llama.fi/'
STABLECOINS_URL = 'https://stablecoins.llama.fi/'
YIELDS_URL='https://yields.llama.fi/'
ABI_URL='https://abi-decoder.llama.fi/'
BRIDGES_URL='https://bridges.llama.fi/'


class Llama:

    # --- Helpers --- #

    def __init__(self):
        """
        Initialize the object
        """
        self.session = requests.Session()


    def _get(self, api_tag, endpoint, params=None):
        if api_tag == 'TVL':
            url = TVL_URL + endpoint
        elif api_tag == 'COINS':
            url = COINS_URL + endpoint  
        elif api_tag == 'STABLECOINS':    
            url = STABLECOINS_URL + endpoint
        elif api_tag == 'YIELDS':
            url = YIELDS_URL + endpoint 
        elif api_tag == 'ABI':
            url = ABI_URL + endpoint
        elif api_tag == 'BRIDGES':
            url = BRIDGES_URL + endpoint
        elif api_tag == 'VOLUMES':
            url = VOLUMES_URL + endpoint
        elif api_tag == 'FEES':
            url = FEES_URL + endpoint
        else:
            raise ValueError(f"'{api_tag}' is not a valid API tag.")
        
        try:
            response = self.session.request('GET', url, timeout=30)
            response.raise_for_status()
        except requests.Timeout:
            raise TimeoutError(f"Request to '{url}' timed out.")
        except requests.RequestException as e:
            raise ConnectionError(f"An error occurred while trying to connect to '{url}'. {str(e)}")
        
        try:
            return response.json()
        except ValueError:
            raise ValueError(f"Invalid JSON response received from '{url}'.")


    def _tstamp_to_dtime(self, df):
        
        df['date'].cast(pl.Datetime).dt.with_time_unit('s')
        return df
    

    # --- TVL --- #

    def get_protocol_current_tvl():
        # /tvl/{protocol}
        # Simplified endpoint to get current TVL of a protocol
        # 'https://api.llama.fi/tvl/{protocol}'


    def get_all_protocols_current_tvl():
        # /protocols
        # List all protocols on defillama along with their tvl
        # 'https://api.llama.fi/protocols'
        # endpoint = f"{TVL_URL}/protocols"


    def get_protocol_historical_tvl():
        # /protocol/{protocol}
        # Get historical TVL of a protocol and breakdowns by token and chain
        # 'https://api.llama.fi/protocol/{protocol}'
        # endpoint = f"{TVL_URL}/protocol/{protocol}"


    def get_chain_historical_tvl():
        # /v2/historicalChainTvl/{chain}
        # Get historical TVL (excludes liquid staking and double counted tvl) of a chain
        # 'https://api.llama.fi/v2/historicalChainTvl/{chain}'


    def get_all_chains_current_tvl():
        # /v2/chains
        # 'https://api.llama.fi/v2/chains'
        # Get current TVL of all chains


    def get_all_chains_historical_tvl():
        # /v2/historicalChainTvl
        # Get historical TVL (excludes liquid staking and double counted tvl) of DeFi on all chains
        # 'https://api.llama.fi/v2/historicalChainTvl'


    # --- Coins --- #


    # --- Stablecoins --- #


    # --- Yields --- #


    # --- ABI Decoder --- #


    # --- Bridges --- #


    # --- Volumes --- #


    # --- Fees --- #





# # Coins
# ## General blockchain data used by defillama and open-sourced

# /prices/current/{coins}
# 'https://coins.llama.fi/prices/current/{coins}'
# Get current prices of tokens by contract address
    
# Tokens are queried using {chain}:{address}, where chain is an identifier such as ethereum, bsc, polygon, avax... You can also get tokens by coingecko id by setting `coingecko` as the chain, eg: coingecko:ethereum, coingecko:bitcoin. Examples:
#     - ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1
#     - bsc:0x762539b45a1dcce3d36d080f74d1aed37844b878
#     - coingecko:ethereum
#     - arbitrum:0x4277f8f2c384827b5273592ff7cebd9f2c1ac258

# - url: https://coins.llama.fi
#       parameters:
#         - name: coins
#           in: path
#           required: true
#           description: set of comma-separated tokens defined as {chain}:{address}
#           schema:
#             type: string
#             example: ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1,coingecko:ethereum,bsc:0x762539b45a1dcce3d36d080f74d1aed37844b878,ethereum:0xdB25f211AB05b1c97D595516F45794528a807ad8
#         - name: searchWidth
#           in: query
#           required: false
#           description: time range on either side to find price data, defaults to 6 hours
#           schema:
#             type: string
#             example: 4h
#       responses:
#         '200':
#           description: successful operation
#           content:
#             'application/json':
#               schema:
#                 type: object
#                 properties:
#                   coins:
#                     type: object
#                     properties:
#                       'ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1':
#                         type: object
#                         properties:
#                           decimals:
#                             type: number
#                             example: 8
#                           price:
#                             type: number
#                             example: 0.022053735051098835
#                           'symbol':
#                             type: string
#                             example: 'cDAI'
#                           'timestamp':
#                             type: number
#                             example: 0.99
#         '502':
#           description: Internal error
#   /prices/historical/{timestamp}/{coins}:
#     get:
#       tags:
#         - coins
#       summary: Get historical prices of tokens by contract address
#       description: See /prices/current for explanation on how prices are sourced.
#       servers:
#         - url: https://coins.llama.fi
#       parameters:
#         - name: coins
#           in: path
#           required: true
#           description: set of comma-separated tokens defined as {chain}:{address}
#           schema:
#             type: string
#             example: ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1,coingecko:ethereum,bsc:0x762539b45a1dcce3d36d080f74d1aed37844b878,ethereum:0xdB25f211AB05b1c97D595516F45794528a807ad8
#         - name: timestamp
#           in: path
#           required: true
#           description: UNIX timestamp of time when you want historical prices
#           schema:
#             type: number
#             example: 1648680149
#         - name: searchWidth
#           in: query
#           required: false
#           description: time range on either side to find price data, defaults to 6 hours
#           schema:
#             type: string
#             example: 4h
#       responses:
#         '200':
#           description: successful operation
#           content:
#             'application/json':
#               schema:
#                 type: object
#                 properties:
#                   coins:
#                     type: object
#                     properties:
#                       'ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1':
#                         type: object
#                         properties:
#                           decimals:
#                             type: number
#                             example: 8
#                           price:
#                             type: number
#                             example: 0.022053735051098835
#                           'symbol':
#                             type: string
#                             example: 'cDAI'
#                           'timestamp':
#                             type: number
#                             example: 1648680149
#         '502':
#           description: Internal error
#   /batchHistorical:
#     get:
#       tags:
#         - coins
#       summary: Get historical prices for multiple tokens at multiple different timestamps
#       description: |
#         Strings accepted by period and searchWidth:
#         Can use regular chart candle notion like ‘4h’ etc where:
#         W = week, D = day, H = hour, M = minute (not case sensitive)
#       servers:
#         - url: https://coins.llama.fi
#       parameters:
#         - name: coins
#           in: query
#           required: true
#           description: object where keys are coins in the form {chain}:{address}, and values are arrays of requested timestamps
#           schema:
#             type: string
#             example: |
#               {"avax:0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e": [1666876743, 1666862343], "coingecko:ethereum": [1666869543, 1666862343]}
#         - name: searchWidth
#           in: query
#           required: false
#           description: time range on either side to find price data, defaults to 6 hours
#           schema:
#             type: string
#             example: 600
#       responses:
#         '200':
#           description: successful operation
#           content:
#             'application/json':
#               schema:
#                 type: object
#                 properties:
#                   coins:
#                     type: object
#                     properties:
#                       'avax:0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e':
#                         type: object
#                         properties:
#                           symbol:
#                             type: string
#                             example: 'USDC'
#                           prices:
#                             type: array
#                             items:
#                               type: object
#                               properties:
#                                 timestamp:
#                                   type: number
#                                   example: 1666876674
#                                 price:
#                                   type: number
#                                   example: 0.999436
#                                 confidence:
#                                   type: number
#                                   example: 0.99
#         '502':
#           description: Internal error
#   /chart/{coins}:
#     get:
#       tags:
#         - coins
#       summary: Get token prices at regular time intervals
#       description: |
#         Strings accepted by period and searchWidth:
#         Can use regular chart candle notion like ‘4h’ etc where:
#         W = week, D = day, H = hour, M = minute (not case sensitive)
#       servers:
#         - url: https://coins.llama.fi
#       parameters:
#         - name: coins
#           in: path
#           required: true
#           description: set of comma-separated tokens defined as {chain}:{address}
#           schema:
#             type: string
#             example: ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1,coingecko:ethereum,bsc:0x762539b45a1dcce3d36d080f74d1aed37844b878,ethereum:0xdB25f211AB05b1c97D595516F45794528a807ad8
#         - name: start
#           in: query
#           required: false
#           description: unix timestamp of earliest data point requested
#           schema:
#             type: number
#             example: 1664364537
#         - name: end
#           in: query
#           required: false
#           description: unix timestamp of latest data point requested
#           schema:
#             type: number
#             example:
#         - name: span
#           in: query
#           required: false
#           description: number of data points returned, defaults to 0
#           schema:
#             type: number
#             example: 10
#         - name: period
#           in: query
#           required: false
#           description: duration between data points, defaults to 24 hours
#           schema:
#             type: string
#             example: 2d
#         - name: searchWidth
#           in: query
#           required: false
#           description: time range on either side to find price data, defaults to 10% of period
#           schema:
#             type: string
#             example: 600
#       responses:
#         '200':
#           description: successful operation
#           content:
#             'application/json':
#               schema:
#                 type: object
#                 properties:
#                   coins:
#                     type: object
#                     properties:
#                       'ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1':
#                         type: object
#                         properties:
#                           decimals:
#                             type: number
#                             example: 8
#                           confidence:
#                             type: number
#                             example: 0.99
#                           prices:
#                             type: array
#                             items:
#                               type: object
#                               properties:
#                                 timestamp:
#                                   type: number
#                                   example: 1666790570
#                                 price:
#                                   type: number
#                                   example: 0.984519
#                           symbol:
#                             type: string
#                             example: 'HUSD'
#         '502':
#           description: Internal error
#   /percentage/{coins}:
#     get:
#       tags:
#         - coins
#       summary: Get percentage change in price over time
#       description: |
#         Strings accepted by period:
#         Can use regular chart candle notion like ‘4h’ etc where:
#         W = week, D = day, H = hour, M = minute (not case sensitive)
#       servers:
#         - url: https://coins.llama.fi
#       parameters:
#         - name: coins
#           in: path
#           required: true
#           description: set of comma-separated tokens defined as {chain}:{address}
#           schema:
#             type: string
#             example: ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1,coingecko:ethereum,bsc:0x762539b45a1dcce3d36d080f74d1aed37844b878,ethereum:0xdB25f211AB05b1c97D595516F45794528a807ad8
#         - name: timestamp
#           in: query
#           required: false
#           description: timestamp of data point requested, defaults to time now
#           schema:
#             type: number
#             example: 1664364537
#         - name: lookForward
#           in: query
#           required: false
#           description: whether you want the duration after your given timestamp or not, defaults to false (looking back)
#           schema:
#             type: boolean
#             example: false
#         - name: period
#           in: query
#           required: false
#           description: duration between data points, defaults to 24 hours
#           schema:
#             type: string
#             example: 3w
#       responses:
#         '200':
#           description: successful operation
#           content:
#             'application/json':
#               schema:
#                 type: object
#                 properties:
#                   coins:
#                     type: object
#                     properties:
#                       'ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1':
#                         type: number
#                         example: -2.3009954568977147
#         '502':
#           description: Internal error
#   /prices/first/{coins}:
#     get:
#       tags:
#         - coins
#       summary: Get earliest timestamp price record for coins
#       servers:
#         - url: https://coins.llama.fi
#       parameters:
#         - name: coins
#           in: path
#           required: true
#           description: set of comma-separated tokens defined as {chain}:{address}
#           schema:
#             type: string
#             example: ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1,coingecko:ethereum,bsc:0x762539b45a1dcce3d36d080f74d1aed37844b878,ethereum:0xdB25f211AB05b1c97D595516F45794528a807ad8
#       responses:
#         '200':
#           description: successful operation
#           content:
#             'application/json':
#               schema:
#                 type: object
#                 properties:
#                   coins:
#                     type: object
#                     properties:
#                       'ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1':
#                         type: object
#                         properties:
#                           price:
#                             type: number
#                             example: 0.9992047673109988
#                           symbol:
#                             type: string
#                             example: 'HUSD'
#                           'timestamp':
#                             type: number
#                             example: 1568883821
#         '502':
#           description: Internal error
#   /block/{chain}/{timestamp}:
#     get:
#       tags:
#         - coins
#       summary: Get the closest block to a timestamp
#       description: |
#         Runs binary search over a blockchain's blocks to get the closest one to a timestamp.
#         Every time this is run we add new data to our database, so each query permanently speeds up future queries.
#       servers:
#         - url: https://coins.llama.fi
#       parameters:
#         - name: chain
#           in: path
#           description: Chain which you want to get the block from
#           required: true
#           schema:
#             type: string
#         - name: timestamp
#           in: path
#           description: UNIX timestamp of the block you are searching for
#           required: true
#           schema:
#             type: integer
#       responses:
#         '200':
#           description: successful operation
#           content:
#             'application/json':
#               schema:
#                 type: object
#                 properties:
#                   height:
#                     type: integer
#                     format: uint
#                     example: 11150916
#                   timestamp:
#                     type: integer
#                     format: uint
#                     example: 1603964988
#         '400':
#           description: Invalid chain or timestamp provided
#   /stablecoins:
#     get:
#       tags:
#         - stablecoins
#       summary: List all stablecoins along with their circulating amounts
#       servers:
#         - url: https://stablecoins.llama.fi
#       parameters:
#         - name: includePrices
#           in: query
#           required: false
#           description: set whether to include current stablecoin prices
#           schema:
#             type: boolean
#             example: true
#       responses:
#         '200':
#           description: successful operation
#   /stablecoincharts/all:
#     get:
#       tags:
#         - stablecoins
#       summary: Get historical mcap sum of all stablecoins
#       servers:
#         - url: https://stablecoins.llama.fi
#       parameters:
#         - name: stablecoin
#           in: query
#           required: false
#           description: stablecoin ID, you can get these from /stablecoins
#           schema:
#             type: integer
#             example: 1
#       responses:
#         '200':
#           description: successful operation
#   /stablecoincharts/{chain}:
#     get:
#       tags:
#         - stablecoins
#       summary: Get historical mcap sum of all stablecoins in a chain
#       servers:
#         - url: https://stablecoins.llama.fi
#       parameters:
#         - name: chain
#           in: path
#           required: true
#           description: chain slug, you can get these from /chains or the chains property on /protocols
#           schema:
#             type: string
#             example: Ethereum
#         - name: stablecoin
#           in: query
#           required: false
#           description: stablecoin ID, you can get these from /stablecoins
#           schema:
#             type: integer
#             example: 1
#       responses:
#         '200':
#           description: successful operation
#   /stablecoin/{asset}:
#     get:
#       tags:
#         - stablecoins
#       summary: Get historical mcap and historical chain distribution of a stablecoin
#       servers:
#         - url: https://stablecoins.llama.fi
#       parameters:
#         - name: asset
#           in: path
#           required: true
#           description: stablecoin ID, you can get these from /stablecoins
#           schema:
#             type: integer
#             example: 1
#       responses:
#         '200':
#           description: successful operation
#   /stablecoinchains:
#     get:
#       tags:
#         - stablecoins
#       summary: Get current mcap sum of all stablecoins on each chain
#       servers:
#         - url: https://stablecoins.llama.fi
#       responses:
#         '200':
#           description: successful operation
#   /stablecoinprices:
#     get:
#       tags:
#         - stablecoins
#       summary: Get historical prices of all stablecoins
#       servers:
#         - url: https://stablecoins.llama.fi
#       responses:
#         '200':
#           description: successful operation
#   /pools:
#     get:
#       tags:
#         - yields
#       summary: Retrieve the latest data for all pools, including enriched information such as predictions
#       servers:
#         - url: https://yields.llama.fi
#       responses:
#         '200':
#           description: successful operation
#   /chart/{pool}:
#     get:
#       tags:
#         - yields
#       summary: Get historical APY and TVL of a pool
#       servers:
#         - url: https://yields.llama.fi
#       parameters:
#         - name: pool
#           in: path
#           required: true
#           description: pool id, can be retrieved from /pools (property is called pool)
#           schema:
#             type: string
#             example: '747c1d2a-c668-4682-b9f9-296708a3dd90'
#       responses:
#         '200':
#           description: successful operation
#   /fetch/signature:
#     get:
#       tags:
#         - abi-decoder
#       summary: Get the ABI for a function or event signature.
#       servers:
#         - url: https://abi-decoder.llama.fi
#       parameters:
#         - name: functions
#           in: query
#           required: false
#           description: function 4 byte signatures, you can add many signatures by joining them with ','
#           schema:
#             type: string
#             example: '0x23b872dd,0x18fccc76,0xb6b55f25,0xf5d07b60'
#         - name: events
#           in: query
#           required: false
#           description: event signatures, you can add many signatures by joining them with ','
#           schema:
#             type: string
#             example: '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef,0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67,0x4cc7e95e48af62690313a0733e93308ac9a73326bc3c29f1788b1191c376d5b6'
#       responses:
#         '200':
#           description: successful operation
#   /fetch/contract/{chain}/{address}:
#     get:
#       tags:
#         - abi-decoder
#       summary: Get the verbose ABI for a function or event signature for a particular contract
#       servers:
#         - url: https://abi-decoder.llama.fi
#       parameters:
#         - name: chain
#           in: path
#           required: true
#           description: Chain the smart contract is located in
#           schema:
#             type: string
#             enum:
#               - arbitrum
#               - avalanche
#               - bsc
#               - celo
#               - ethereum
#               - fantom
#               - optimism
#               - polygon
#               - tron
#             example: ethereum
#         - name: address
#           in: path
#           required: true
#           description: Address of the smart contract
#           schema:
#             type: string
#             example: '0x02f7bd798e765369a9d204e9095b2a526ef01667'
#         - name: functions
#           in: query
#           required: false
#           description: function 4 byte signatures, you can add many signatures by joining them with ','
#           schema:
#             type: string
#             example: '0xf43f523a,0x95d89b41,0x95d89b41,0x70a08231,0x70a08231'
#         - name: events
#           in: query
#           required: false
#           description: event signatures, you can add many signatures by joining them with ','
#           schema:
#             type: string
#             example: '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef,0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925'
#       responses:
#         '200':
#           description: successful operation
#   /bridges:
#     get:
#       tags:
#         - bridges
#       summary: List all bridges along with summaries of recent bridge volumes.
#       servers:
#         - url: https://bridges.llama.fi
#       parameters:
#         - name: includeChains
#           in: query
#           required: false
#           description: set whether to include current previous day volume breakdown by chain
#           schema:
#             type: boolean
#             example: true
#       responses:
#         '200':
#           description: successful operation
#   /bridge/{id}:
#     get:
#       tags:
#         - bridges
#       summary: Get summary of bridge volume and volume breakdown by chain
#       servers:
#         - url: https://bridges.llama.fi
#       parameters:
#         - name: id
#           in: path
#           required: true
#           description: bridge ID, you can get these from /bridges
#           schema:
#             type: integer
#             example: 1
#       responses:
#         '200':
#           description: successful operation
#   /bridgevolume/{chain}:
#     get:
#       tags:
#         - bridges
#       summary: Get historical volumes for a bridge, chain, or bridge on a particular chain
#       servers:
#         - url: https://bridges.llama.fi
#       parameters:
#         - name: chain
#           in: path
#           required: true
#           description: chain slug, you can get these from /chains. Call also use 'all' for volume on all chains.
#           schema:
#             type: string
#             example: Ethereum
#         - name: id
#           in: query
#           required: false
#           description: bridge ID, you can get these from /bridges
#           schema:
#             type: integer
#             example: 5
#       responses:
#         '200':
#           description: successful operation
#   /bridgedaystats/{timestamp}/{chain}:
#     get:
#       tags:
#         - bridges
#       summary: Get a 24hr token and address volume breakdown for a bridge
#       servers:
#         - url: https://bridges.llama.fi
#       parameters:
#         - name: timestamp
#           in: path
#           required: true
#           description: Unix timestamp. Data returned will be for the 24hr period starting at 00:00 UTC that the timestamp lands in.
#           schema:
#             type: integer
#             example: 1667304000
#         - name: chain
#           in: path
#           required: true
#           description: chain slug, you can get these from /chains.
#           schema:
#             type: string
#             example: Ethereum
#         - name: id
#           in: query
#           required: false
#           description: bridge ID, you can get these from /bridges
#           schema:
#             type: integer
#             example: 5
#       responses:
#         '200':
#           description: successful operation
#   /transactions/{id}:
#     get:
#       tags:
#         - bridges
#       summary: Get all transactions for a bridge within a date range
#       servers:
#         - url: https://bridges.llama.fi
#       parameters:
#         - name: id
#           in: path
#           required: true
#           description: bridge ID, you can get these from /bridges
#           schema:
#             type: integer
#             example: 1
#         - name: starttimestamp
#           in: query
#           required: false
#           description: start timestamp (Unix Timestamp) for date range
#           schema:
#             type: integer
#             example: 1667260800
#         - name: endtimestamp
#           in: query
#           required: false
#           description: end timestamp (Unix timestamp) for date range
#           schema:
#             type: integer
#             example: 1667347200
#         - name: sourcechain
#           in: query
#           required: false
#           description: Returns only transactions that are bridging from the specified source chain.
#           schema:
#             type: string
#             example: 'Polygon'
#         - name: address
#           in: query
#           required: false
#           description: Returns only transactions with specified address as "from" or "to". Addresses are quried in the form {chain}:{address}, where chain is an identifier such as ethereum, bsc, polygon, avax... .
#           schema:
#             type: string
#             example: 'ethereum:0x69b4B4390Bd1f0aE84E090Fe8af7AbAd2d95Cc8E'
#         - name: limit
#           in: query
#           required: false
#           description: limit to number of transactions returned, maximum is 6000
#           schema:
#             type: integer
#             example: 200
#       responses:
#         '200':
#           description: successful operation
#   /overview/dexs:
#     get:
#       tags:
#         - volumes
#       summary: List all dexs along with summaries of their volumes and dataType history data
#       servers:
#         - url: https://api.llama.fi
#       parameters:
#         - name: excludeTotalDataChart
#           in: query
#           required: false
#           description: true to exclude aggregated chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: excludeTotalDataChartBreakdown
#           in: query
#           required: false
#           description: true to exclude broken down chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: dataType
#           in: query
#           required: false
#           description: Desired data type, dailyVolume by default.
#           schema:
#             type: string
#             enum: [dailyVolume, totalVolume]
#             example: dailyVolume
#       responses:
#         '200':
#           description: successful operation
#   /overview/dexs/{chain}:
#     get:
#       tags:
#         - volumes
#       summary: List all dexs along with summaries of their volumes and dataType history data filtering by chain
#       servers:
#         - url: https://api.llama.fi
#       parameters:
#         - name: chain
#           in: path
#           required: true
#           description: chain name, list of all supported chains can be found under allChains attribute in /overview/dexs response
#           schema:
#             type: string
#             example: ethereum
#         - name: excludeTotalDataChart
#           in: query
#           required: false
#           description: true to exclude aggregated chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: excludeTotalDataChartBreakdown
#           in: query
#           required: false
#           description: true to exclude broken down chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: dataType
#           in: query
#           required: false
#           description: Desired data type, dailyVolume by default.
#           schema:
#             type: string
#             enum: [dailyVolume, totalVolume]
#             example: dailyVolume
#       responses:
#         '200':
#           description: successful operation
#   /summary/dexs/{protocol}:
#     get:
#       tags:
#         - volumes
#       summary: Get summary of dex volume with historical data
#       servers:
#         - url: https://api.llama.fi
#       parameters:
#         - name: protocol
#           in: path
#           required: true
#           description: protocol slug
#           schema:
#             type: string
#             example: aave
#         - name: excludeTotalDataChart
#           in: query
#           required: false
#           description: true to exclude aggregated chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: excludeTotalDataChartBreakdown
#           in: query
#           required: false
#           description: true to exclude broken down chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: dataType
#           in: query
#           required: false
#           description: Desired data type, dailyVolume by default.
#           schema:
#             type: string
#             enum: [dailyVolume, totalVolume]
#             example: dailyVolume
#       responses:
#         '200':
#           description: successful operation
#   /overview/options:
#     get:
#       tags:
#         - volumes
#       summary: List all options dexs along with summaries of their volumes and dataType history data
#       servers:
#         - url: https://api.llama.fi
#       parameters:
#         - name: excludeTotalDataChart
#           in: query
#           required: false
#           description: true to exclude aggregated chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: excludeTotalDataChartBreakdown
#           in: query
#           required: false
#           description: true to exclude broken down chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: dataType
#           in: query
#           required: false
#           description: Desired data type, dailyNotionalVolume by default.
#           schema:
#             type: string
#             enum: [dailyPremiumVolume, dailyNotionalVolume, totalPremiumVolume, totalNotionalVolume]
#             example: dailyPremiumVolume
#       responses:
#         '200':
#           description: successful operation
#   /overview/options/{chain}:
#     get:
#       tags:
#         - volumes
#       summary: List all options dexs along with summaries of their volumes and dataType history data filtering by chain
#       servers:
#         - url: https://api.llama.fi
#       parameters:
#         - name: chain
#           in: path
#           required: true
#           description: chain name, list of all supported chains can be found under allChains attribute in /overview/options response
#           schema:
#             type: string
#             example: ethereum
#         - name: excludeTotalDataChart
#           in: query
#           required: false
#           description: true to exclude aggregated chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: excludeTotalDataChartBreakdown
#           in: query
#           required: false
#           description: true to exclude broken down chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: dataType
#           in: query
#           required: false
#           description: Desired data type, dailyNotionalVolume by default.
#           schema:
#             type: string
#             enum: [dailyPremiumVolume, dailyNotionalVolume, totalPremiumVolume, totalNotionalVolume]
#             example: dailyPremiumVolume
#       responses:
#         '200':
#           description: successful operation
#   /summary/options/{protocol}:
#     get:
#       tags:
#         - volumes
#       summary: Get summary of options dex volume with historical data
#       servers:
#         - url: https://api.llama.fi
#       parameters:
#         - name: protocol
#           in: path
#           required: true
#           description: protocol slug
#           schema:
#             type: string
#             example: lyra
#         - name: dataType
#           in: query
#           required: false
#           description: Desired data type, dailyNotionalVolume by default.
#           schema:
#             type: string
#             enum: [dailyPremiumVolume, dailyNotionalVolume, totalPremiumVolume, totalNotionalVolume]
#             example: dailyPremiumVolume
#       responses:
#         '200':
#           description: successful operation
#   /overview/fees:
#     get:
#       tags:
#         - fees and revenue
#       summary: List all protocols along with summaries of their fees and revenue and dataType history data
#       servers:
#         - url: https://api.llama.fi
#       parameters:
#         - name: excludeTotalDataChart
#           in: query
#           required: false
#           description: true to exclude aggregated chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: excludeTotalDataChartBreakdown
#           in: query
#           required: false
#           description: true to exclude broken down chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: dataType
#           in: query
#           required: false
#           description: Desired data type, dailyFees by default.
#           schema:
#             type: string
#             enum: [totalFees, dailyFees, totalRevenue, dailyRevenue]
#             example: dailyFees
#       responses:
#         '200':
#           description: successful operation
#   /overview/fees/{chain}:
#     get:
#       tags:
#         - fees and revenue
#       summary: List all protocols along with summaries of their fees and revenue and dataType history data by chain
#       servers:
#         - url: https://api.llama.fi
#       parameters:
#         - name: chain
#           in: path
#           required: true
#           description: chain name, list of all supported chains can be found under allChains attribute in /overview/fees response
#           schema:
#             type: string
#             example: ethereum
#         - name: excludeTotalDataChart
#           in: query
#           required: false
#           description: true to exclude aggregated chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: excludeTotalDataChartBreakdown
#           in: query
#           required: false
#           description: true to exclude broken down chart from response
#           schema:
#             type: boolean
#             example: true
#         - name: dataType
#           in: query
#           required: false
#           description: Desired data type, dailyFees by default.
#           schema:
#             type: string
#             enum: [totalFees, dailyFees, totalRevenue, dailyRevenue]
#             example: dailyFees
#       responses:
#         '200':
#           description: successful operation
#   /summary/fees/{protocol}:
#     get:
#       tags:
#         - fees and revenue
#       summary: Get summary of protocol fees and revenue with historical data
#       servers:
#         - url: https://api.llama.fi
#       parameters:
#         - name: protocol
#           in: path
#           required: true
#           description: protocol slug
#           schema:
#             type: string
#             example: lyra
#         - name: dataType
#           in: query
#           required: false
#           description: Desired data type, dailyFees by default.
#           schema:
#             type: string
#             enum: [totalFees, dailyFees, totalRevenue, dailyRevenue]
#             example: dailyFees
#       responses:
#         '200':
#           description: successful operation
