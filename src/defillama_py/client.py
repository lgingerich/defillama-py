import requests
import pandas as pd
from typing import Union, List, Dict
from urllib.parse import urlencode

# TO DO:

# add functionality for large scale data extraction (i.e. get historical tvl of all dapps across all chains)
# packaged transformations should return only critical data (no metadata). for a tvl endpoint, only return tvl
# handle potential rate limiting: 500 requests / min
# check that function inputs (chains, protocols, coins, etc.) exist
# check is instance and type check matching
# urllib for proper string encoding?

# general ordering of methods per category:
# ------ small to big ------
# 1. all xyz current
# 2. specific xyz historical



TVL_URL = VOLUMES_URL = FEES_URL = 'https://api.llama.fi'
COINS_URL = 'https://coins.llama.fi'
STABLECOINS_URL = 'https://stablecoins.llama.fi'
YIELDS_URL='https://yields.llama.fi'
ABI_URL='https://abi-decoder.llama.fi'
BRIDGES_URL='https://bridges.llama.fi'


class Llama:

    # --- Initialization and Helpers --- #

    def __init__(self):
        """
        Initialize the Llama object with a new session for making HTTP requests.
        """
        self.session = requests.Session()


    def _get(self, api_tag: str, endpoint: str, params: Dict = None):
        """
        Internal helper to make GET requests.
        """
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
            print(f"Calling API endpoint: {url}")
            response.raise_for_status()
        except requests.Timeout:
            raise TimeoutError(f"Request to '{url}' timed out.")
        except requests.RequestException as e:
            raise ConnectionError(f"An error occurred while trying to connect to '{url}'. {str(e)}")
        
        try:
            return response.json()
        except ValueError:
            raise ValueError(f"Invalid JSON response received from '{url}'.")

        
    def _clean_chain_name(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes a DataFrame, and for the "chain" column:
        - Converts the names to lowercase
        - Replaces spaces, hyphens, and dashes with underscores
        """
        if 'chain' in df.columns:
            df['chain'] = df['chain'].str.lower().str.replace('[-\s]', '_', regex=True)
        
        return df

    
    # --- Mappings --- #
    """
    Helper functions to get full lists of all chains, protocols, stablecoins, and pools tracked by DefiLlama.
    Used to map general names with unique identifiers such as chain IDs and protocol slugs.
    Returns minimum information necessary to uniquely identify objects.
    Bridges, DEXs, etc. can be fetched from the list of protocols, therefore, they do not have their own mapping function.
    """
    
    def get_chains(self):
        """
        Retrieve a list of all chains with their chain ID and name
        """
        results = []

        response = self._get('TVL', endpoint=f'/v2/chains')
        
        for asset in response:
            results.append({
                "chain_id": asset["chainId"],
                "name": asset["name"]
            })

        return results
        
    
    def get_protocols(self):
        """
        Retrieve a list of all protocols with their ID, name, and slug
        """
        results = []

        response = self._get('TVL', endpoint=f'/protocols')
        
        for asset in response:
            results.append({
                "id": asset["id"],
                "name": asset["name"],
                "slug": asset["slug"]
            })

        return results


    def get_stablecoins(self):
        """
        Retrieve a list of all stablecoins with their id, name, and symbol
        """
        results = []

        response = self._get('STABLECOINS', endpoint=f'/stablecoins')
        
        for asset in response['peggedAssets']:
            results.append({
                "id": asset["id"],
                "name": asset["name"],
                "symbol": asset["symbol"]
            })

        return results
   
   
    def get_pools(self):
        """
        Retrieve a list of all pools with their chain, project, symbol, and pool id
        """
        results = []

        response = self._get('YIELDS', endpoint=f'/pools')
        
        for asset in response['data']:
            results.append({
                "id": asset["pool"],
                "chain": asset["chain"],
                "project": asset["project"],
                "symbol": asset["symbol"]
            })

        return results   


    # --- TVL --- #

    def get_protocol_current_tvl(self, protocols: List[str]) -> Union[float, Dict[str, float]]:
        """
        Endpoint to get current TVL of one or multiple protocols.
        
        :param protocols: List of protocol names.
        :return: TVL value as float if a single protocol is provided; otherwise, a dictionary with protocol names as keys and their TVL as values.
        """
        if len(protocols) == 1:
            return self._get('TVL', endpoint=f'/tvl/{protocols[0]}')

        results = {}
        
        for protocol in protocols:
            data = self._get('TVL', endpoint=f'/tvl/{protocol}')
            results[protocol] = float(data)
            
        return results

    
    def get_all_protocols_current_tvl(self, raw: bool) -> Union[List[Dict], pd.DataFrame]:
        """
        Calls the API to get protocol data and either returns the raw data or a transformed DataFrame.
        
        :param raw: Whether to return the raw data or a transformed DataFrame.
        :return: Raw data or DataFrame.
        """
        if raw:
            return self._get('TVL', endpoint='/protocols')

        elif not raw:
            results = []

            # Iterate over each raw data entry
            for raw_data in self._get('TVL', endpoint='/protocols'):
                protocol = raw_data.get('slug')
                chain_tvls = raw_data.get('chainTvls', {})

                # Iterate over chainTvls to create denormalized rows
                for chain, tvl in chain_tvls.items():
                    results.append({
                        'chain': chain,
                        'protocol': protocol,
                        'tvl': tvl
                    })

            df = pd.DataFrame(results)
            return self._clean_chain_name(df)  
    
    
    def get_protocol_historical_tvl(self, protocols: List[str], raw: bool) -> Union[Dict[str, Dict], pd.DataFrame]:
        """
        Get historical TVL of a protocol and breakdowns by token and chain.

        :param protocols: List of protocol names.
        :param raw: Whether to return the raw data or a transformed DataFrame.
        :return: Raw data or DataFrame.
        """
        if isinstance(protocols, str):
            protocols = [protocols]
        
        if raw:
            if len(protocols) == 1:
                return self._get('TVL', endpoint=f'/protocol/{protocols[0]}')
            
            results = {}
            for protocol in protocols:
                results[protocol] = self._get('TVL', endpoint=f'/protocol/{protocol}')
            return results

        elif not raw:
            results = []

            for protocol in protocols:
                data = self._get('TVL', endpoint=f'/protocol/{protocol}')
                chain_tvls = data.get("chainTvls", {})
                
                for chain, chain_data in chain_tvls.items():
                    tvl_data = chain_data.get("tvl", [])
                    
                    for entry in tvl_data:
                        results.append({
                            'date': entry.get('date'),
                            'chain': chain,
                            'protocol': protocol,
                            'tvl': entry.get('totalLiquidityUSD')
                        })

            df = pd.DataFrame(results)
            return self._clean_chain_name(df)  
        

    def get_chain_historical_tvl(self, raw: bool, chains: Union[str, List[str]]) -> Union[Dict[str, List[Dict]], pd.DataFrame]:
        """
        Get historical TVL (excludes liquid staking and double counted tvl) of a chain or chains.
        
        :param chains: Chain or list of chains for which to retrieve historical TVL.
        :param raw: Whether to return the raw data or a transformed DataFrame.
        :return: Raw data or DataFrame.
        """
        if raw:
            if isinstance(chains, str):
                return self._get('TVL', endpoint=f'/v2/historicalChainTvl/{chains}')
            
            results = {}
            for chain in chains:
                results[chain] = self._get('TVL', endpoint=f'/v2/historicalChainTvl/{chain}')
            return results

        elif not raw:
            if isinstance(chains, str):
                chains = [chains]

            results = []

            for chain in chains:
                chain_data = self._get('TVL', endpoint=f'/v2/historicalChainTvl/{chain}')
                for entry in chain_data:
                    entry['chain'] = chain
                    results.append(entry)

            df = pd.DataFrame(results)
            return self._clean_chain_name(df)


    def get_all_chains_current_tvl(self, raw: bool) -> Union[List[Dict], pd.DataFrame]:
        """
        Get current TVL of all chains.

        :param raw: Whether to return the raw data or a transformed DataFrame.
        :return: Raw data or DataFrame.
        """
        if raw:
            return self._get('TVL', endpoint=f'/v2/chains')

        elif not raw:
            results = []

            for entry in self._get('TVL', endpoint=f'/v2/chains'):
                results.append({
                    'chain': entry.get('name'),
                    'tvl': entry.get('tvl')
                })

            df = pd.DataFrame(results)
            return self._clean_chain_name(df)


    def get_all_chains_historical_tvl(self, raw: bool) -> Union[List[Dict], pd.DataFrame]:
        """
        Get historical TVL (excludes liquid staking and double counted tvl) of DeFi on all chains.

        :param raw: Whether to return the raw data or a transformed DataFrame.
        :return: Raw data or DataFrame.
        """
        if raw:
            return self._get('TVL', endpoint=f'/v2/historicalChainTvl')

        elif not raw:
            return pd.DataFrame(self._get('TVL', endpoint=f'/v2/historicalChainTvl'))



    # --- Coins --- #
    
    # /prices/current/{coins}
    # /prices/historical/{timestamp}/{coins}
    # /batchHistorical
    # /chart/{coins}
    # /percentage/{coins}
    # /prices/first/{coins}
    # /block/{chain}/{timestamp}


    # --- Stablecoins --- #

    # /stablecoins                  
    # /stablecoincharts/all         def get_total_historical_stablecoin_mcap()
    # /stablecoincharts/{chain}     def get_chain_historical_stablecoin_mcap()
    # /stablecoin/{asset}           def get_historical_stablecoin_distribution()
    # /stablecoinchains             def get_all_chains_current_stablecoin_mcap()
    # /stablecoinprices             def get_historical_stablecoin_price()


    # --- Yields --- #

    # /pools
    # /chart/{pool}


    # --- ABI Decoder --- #
    
    # /fetch/signature
    # /fetch/contract/{chain}/{address}


    # --- Bridges --- #
    
    # /bridges
    # /bridges/{id}
    # /bridgevolume/{chain}
    # /bridgedaystats/{timestamp}/{chain}
    # /transactions/{id}


    # --- Volumes --- #
    
    def get_dex_volume(self, raw: bool, params):
        """
        
        excludeTotalDataChart - returns timestamp + volume for all chains and dex's
        excludeTotalDataChartBreakdown - returns timestamp + volume for all dapps and all chains (not broken down by chain)
        dataType - dailyVolume or totalVolume
        """
        
        if params:
            query_string = urlencode(params)
            endpoint = f"/overview/dexs?{query_string}"
            
        elif not params:
            raise ValueError("params dictionary is missing.")
        
        if raw:
            return self._get('VOLUMES', endpoint=endpoint, params=params)

        elif not raw:
            if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                response = self._get('VOLUMES', endpoint=endpoint, params=params)
                
                df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                return df
            
            elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                response = self._get('VOLUMES', endpoint=endpoint, params=params)
            
                records = []
                for item in response['totalDataChartBreakdown']:
                    timestamp, protocols = item
                    for protocol, volume in protocols.items():
                        records.append({'date': timestamp, 'protocol': protocol, 'volume': volume})

                df = pd.DataFrame(records)
                return df
            
            elif params['excludeTotalDataChart'] == params['excludeTotalDataChartBreakdown']:
                raise ValueError("Both excludeTotalDataChart and excludeTotalDataChartBreakdown cannot have the same value (either both True or both False) if raw = False.")



    def get_chain_dex_volume(self, raw: bool, chains: Union[str, List[str]], params):
        """
        /overview/dexs/{chain}
        

        excludeTotalDataChart - returns timestamp + volume for specified chain(s) and dex's
        excludeTotalDataChartBreakdown - returns timestamp + volume for all dapps and all chains (not broken down by chain)
        dataType - dailyVolume or totalVolume  
        """
            
        if isinstance(chains, str):
            chains = [chains]
        elif not isinstance(chains, list):
            raise ValueError("chains must be either a string or a list of strings.")
        
        if not params:
            raise ValueError("params dictionary is missing.")
        
        # Create the endpoint URL
        query_string = urlencode(params)

        results = []
        for chain in chains:
            endpoint = f"/overview/dexs/{chain}?{query_string}"

            if raw:
                results.append(self._get('VOLUMES', endpoint=endpoint, params=params))
            else:
                if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                    response = self._get('VOLUMES', endpoint=endpoint, params=params)
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    df = df[['date', 'chain', 'volume']]
                    df = self._clean_chain_name(df)
                    results.append(df)

                elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                    response = self._get('VOLUMES', endpoint=endpoint, params=params)

                    records = []
                    for item in response['totalDataChartBreakdown']:
                        timestamp, protocols = item
                        for protocol, volume in protocols.items():
                            records.append({'date': timestamp, 'chain': chain, 'protocol': protocol, 'volume': volume})

                    df = pd.DataFrame(records)
                    df = self._clean_chain_name(df)
                    results.append(df)
                    
                elif params['excludeTotalDataChart'] == params['excludeTotalDataChartBreakdown']:
                    raise ValueError("Both excludeTotalDataChart and excludeTotalDataChartBreakdown cannot have the same value (either both True or both False) if raw = False.")

        # Concatenate results
        if raw:
            return results
        else:
            return pd.concat(results, ignore_index=True)

    
    # def get_protocol_dex_volume(self, raw: bool, protocols: Union[str, List[str]], params):
    # """
    # /summary/dexs/{protocol}
    
    # dataType - dailyVolume or totalVolume  
    # """    
    

    def get_perps_volume(self, raw: bool, params):
        """
        
        excludeTotalDataChart - returns timestamp + volume for all chains and dex's
        excludeTotalDataChartBreakdown - returns timestamp + volume for all dapps and all chains (not broken down by chain)
        dataType - dailyVolume or totalVolume
        """
        
        if params:
            query_string = urlencode(params)
            endpoint = f"/overview/derivatives?{query_string}"
            
        elif not params:
            raise ValueError("params dictionary is missing.")
        
        if raw:
            return self._get('VOLUMES', endpoint=endpoint, params=params)

        elif not raw:
            if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                response = self._get('VOLUMES', endpoint=endpoint, params=params)
                
                df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                return df
            
            elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                response = self._get('VOLUMES', endpoint=endpoint, params=params)
            
                records = []
                for item in response['totalDataChartBreakdown']:
                    timestamp, protocols = item
                    for protocol, volume in protocols.items():
                        records.append({'date': timestamp, 'protocol': protocol, 'volume': volume})

                df = pd.DataFrame(records)
                return df
            
            elif params['excludeTotalDataChart'] == params['excludeTotalDataChartBreakdown']:
                raise ValueError("Both excludeTotalDataChart and excludeTotalDataChartBreakdown cannot have the same value (either both True or both False) if raw = False.")


    def get_chain_perps_volume(self, raw: bool, chains: Union[str, List[str]], params):
        """
        /overview/derivatives/{chain}
        

        excludeTotalDataChart - returns timestamp + volume for specified chain(s) and dex's
        excludeTotalDataChartBreakdown - returns timestamp + volume for all dapps and all chains (not broken down by chain)
        dataType - dailyVolume or totalVolume  
        """
            
        if isinstance(chains, str):
            chains = [chains]
        elif not isinstance(chains, list):
            raise ValueError("chains must be either a string or a list of strings.")
        
        if not params:
            raise ValueError("params dictionary is missing.")
        
        # Create the endpoint URL
        query_string = urlencode(params)

        results = []
        for chain in chains:
            endpoint = f"/overview/derivatives/{chain}?{query_string}"

            if raw:
                results.append(self._get('VOLUMES', endpoint=endpoint, params=params))
            else:
                if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                    response = self._get('VOLUMES', endpoint=endpoint, params=params)
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    df = df[['date', 'chain', 'volume']]
                    df = self._clean_chain_name(df)
                    results.append(df)

                elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                    response = self._get('VOLUMES', endpoint=endpoint, params=params)

                    records = []
                    for item in response['totalDataChartBreakdown']:
                        timestamp, protocols = item
                        for protocol, volume in protocols.items():
                            records.append({'date': timestamp, 'chain': chain, 'protocol': protocol, 'volume': volume})

                    df = pd.DataFrame(records)
                    df = self._clean_chain_name(df)
                    results.append(df)
                    
                elif params['excludeTotalDataChart'] == params['excludeTotalDataChartBreakdown']:
                    raise ValueError("Both excludeTotalDataChart and excludeTotalDataChartBreakdown cannot have the same value (either both True or both False) if raw = False.")

        # Concatenate results
        if raw:
            return results
        else:
            return pd.concat(results, ignore_index=True)

    
    # def get_protocol_perps_volume(self, raw: bool, protocols: Union[str, List[str]], params):
    # """
    # /summary/derivatives/{protocol}
    
    # dataType - dailyVolume or totalVolume  
    # """        
    

    def get_options_volume(self, raw: bool, params):
        """
        
        excludeTotalDataChart - returns timestamp + volume for all chains and dex's
        excludeTotalDataChartBreakdown - returns timestamp + volume for all dapps and all chains (not broken down by chain)
        dataType - dailyPremiumVolume, dailyNotionalVolume, totalPremiumVolume, or totalNotionalVolume
        """
        if params:
            query_string = urlencode(params)
            endpoint = f"/overview/options?{query_string}"
            
        elif not params:
            raise ValueError("params dictionary is missing.")
        
        if raw:
            return self._get('VOLUMES', endpoint=endpoint, params=params)

        elif not raw:
            if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                response = self._get('VOLUMES', endpoint=endpoint, params=params)
                
                df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                return df
            
            elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                response = self._get('VOLUMES', endpoint=endpoint, params=params)
            
                records = []
                for item in response['totalDataChartBreakdown']:
                    timestamp, protocols = item
                    for protocol, volume in protocols.items():
                        records.append({'date': timestamp, 'protocol': protocol, 'volume': volume})

                df = pd.DataFrame(records)
                return df
            
            elif params['excludeTotalDataChart'] == params['excludeTotalDataChartBreakdown']:
                raise ValueError("Both excludeTotalDataChart and excludeTotalDataChartBreakdown cannot have the same value (either both True or both False) if raw = False.")


    def get_chain_options_volume(self, raw: bool, params):
        """
        /overview/options/{chain}
        

        excludeTotalDataChart - returns timestamp + volume for specified chain(s) and dex's
        excludeTotalDataChartBreakdown - returns timestamp + volume for all dapps and all chains (not broken down by chain)
        dataType - dailyPremiumVolume, dailyNotionalVolume, totalPremiumVolume, or totalNotionalVolume
        """
        if isinstance(chains, str):
            chains = [chains]
        elif not isinstance(chains, list):
            raise ValueError("chains must be either a string or a list of strings.")
        
        if not params:
            raise ValueError("params dictionary is missing.")
        
        # Create the endpoint URL
        query_string = urlencode(params)

        results = []
        for chain in chains:
            endpoint = f"/overview/options/{chain}?{query_string}"

            if raw:
                results.append(self._get('VOLUMES', endpoint=endpoint, params=params))
            else:
                if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                    response = self._get('VOLUMES', endpoint=endpoint, params=params)
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    df = df[['date', 'chain', 'volume']]
                    df = self._clean_chain_name(df)
                    results.append(df)

                elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                    response = self._get('VOLUMES', endpoint=endpoint, params=params)

                    records = []
                    for item in response['totalDataChartBreakdown']:
                        timestamp, protocols = item
                        for protocol, volume in protocols.items():
                            records.append({'date': timestamp, 'chain': chain, 'protocol': protocol, 'volume': volume})

                    df = pd.DataFrame(records)
                    df = self._clean_chain_name(df)
                    results.append(df)
                    
                elif params['excludeTotalDataChart'] == params['excludeTotalDataChartBreakdown']:
                    raise ValueError("Both excludeTotalDataChart and excludeTotalDataChartBreakdown cannot have the same value (either both True or both False) if raw = False.")

        # Concatenate results
        if raw:
            return results
        else:
            return pd.concat(results, ignore_index=True)
    

    # def get_protocol_options_volume(self, raw: bool, protocols: Union[str, List[str]], params):
    # """
    # /summary/options/{protocol}
    

    # dataType - dailyPremiumVolume, dailyNotionalVolume, totalPremiumVolume, or totalNotionalVolume  
    # """     
    
    
    
    

    # --- Fees --- #

    # /overview/fees
    # /overview/fees/{chain}
    # /summary/fees/{protocol}



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



#   /prices/historical/{timestamp}/{coins}:
#       summary: Get historical prices of tokens by contract address
#       description: See /prices/current for explanation on how prices are sourced.
#       servers:
#         - url: https://coins.llama.fi
#       parameters:
#         - name: coins
#           description: set of comma-separated tokens defined as {chain}:{address}
#           schema:
#             type: string
#             example: ethereum:0xdF574c24545E5FfEcb9a659c229253D4111d87e1,coingecko:ethereum,bsc:0x762539b45a1dcce3d36d080f74d1aed37844b878,ethereum:0xdB25f211AB05b1c97D595516F45794528a807ad8
#         - name: timestamp
#           description: UNIX timestamp of time when you want historical prices
#           schema:
#             type: number
#             example: 1648680149
#         - name: searchWidth
#           description: time range on either side to find price data, defaults to 6 hours
#           schema:
#             type: string
#             example: 4h



#   /batchHistorical:
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
