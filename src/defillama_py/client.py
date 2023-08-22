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
# lots of work to do on error handling, type checking, type enforcement, etc.
# urllib for proper string encoding?
# do i need get_bridges() or can I just use get_protocols()?
# handle required vs optional params
# volumes are wrong because I don't handle the case where optional params are omitted

# general ordering of methods per category:
# ------ small to big ------
# 1. all xyz current
# 2. specific xyz historical

# technically returning a list of Dicts in many cases, may need to change "Returns" comment under each function
# `params` only ever contains optional parameters. required parameters are explicity called in the function definition.


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
            df['chain'] = df['chain'].str.lower().str.replace(r'[-\s]', '_', regex=True)
        
        return df

    
    # --- Mappings --- #
    """
    Helper functions to get full lists of all chains, protocols, stablecoins, and pools tracked by DefiLlama.
    Used to map general names with unique identifiers such as chain IDs and protocol slugs.
    Returns minimum information necessary to uniquely identify objects.
    Bridges, DEXs, etc. can be fetched from the list of protocols, therefore, they do not have their own mapping function.
    """



    # should these helper functions include all static info rather than only bare minimum?? leaning towards yes.

    
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
    
    def get_all_protocols_current_tvl(self, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get all protocols on DefiLlama along with their TVL.

        Endpoint: /protocols

        Parameters:
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
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
    
    
    def get_protocol_historical_tvl(self, protocols: List[str], raw: bool = True) -> Union[Dict[str, Dict], pd.DataFrame]:
        """
        Get historical TVL of protocol(s) and breakdowns by token and chain.

        Endpoint: /protocol/{protocol}

        Parameters:
            - protocols (str or List[str], required): protocol slug(s) — you can get these from get_protocols().
            - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
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
        

    def get_all_chains_historical_tvl(self, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get historical TVL (excludes liquid staking and double counted tvl) of DeFi on all chains.

        Endpoint: /v2/historicalChainTvl

        Parameters:
            - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """
        if raw:
            return self._get('TVL', endpoint=f'/v2/historicalChainTvl')

        elif not raw:
            return pd.DataFrame(self._get('TVL', endpoint=f'/v2/historicalChainTvl'))
    

    def get_chain_historical_tvl(self, chains: Union[str, List[str]], raw: bool = True):
        """
        Get historical TVL (excludes liquid staking and double counted tvl) of a chain(s).

        Endpoint: /v2/historicalChainTvl/{chain}

        Parameters:
            - chains (str or List[str], required): chain slug(s) — you can get these from get_chains().
            - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
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


    # need to add raw param here
    def get_protocol_current_tvl(self, protocols: Union[str, List[str]]) -> Union[float, Dict[str, float]]:
        """
        Get current Total Value Locked (TVL) for the specified protocols.

        Endpoint: /tvl/{protocol}

        Parameters:
        - protocols (str or List[str], required): A list containing names of the desired protocol(s).

        Returns:
        - float or Dict[str, float]: 
            - If a single protocol is provided, returns the TVL as a float.
            - If multiple protocols are provided, returns a dictionary mapping each protocol name to its TVL.
        """
        if len(protocols) == 1:
            return self._get('TVL', endpoint=f'/tvl/{protocols[0]}')

        results = {}
        
        for protocol in protocols:
            data = self._get('TVL', endpoint=f'/tvl/{protocol}')
            results[protocol] = float(data)
            
        return results
    

    def get_all_chains_current_tvl(self, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get current TVL of all chains.

        Endpoint: /v2/chains

        Parameters:
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
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






    # --- Coins --- #
    
    # /prices/current/{coins}
    # /prices/historical/{timestamp}/{coins}
    # /batchHistorical
    # /chart/{coins}
    # /percentage/{coins}
    # /prices/first/{coins}
    # /block/{chain}/{timestamp}


    # --- Stablecoins --- #
    # (self, assets: Union[int, List[int]], params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:

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
    
    def get_bridge_volume(self, params: Dict = None, raw: bool = True) -> Union[Dict, pd.DataFrame]:
        """
        Get bridge data with summaries of recent bridge volumes.
        
        Endpoint: /bridges

        Parameters:
        - params (Dict, optional): Dictionary containing optional API parameters.
            - includeChains: Whether to include current previous day volume breakdown by chain. Defaults to False.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. 
                                Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """

        
        query_string = urlencode(params)
        endpoint = f"/bridges?{query_string}"
        response = self._get('BRIDGES', endpoint, params=params)

        if raw:
            return response
        
        elif not raw:
            if params.get('includeChains'):
                df = pd.DataFrame(response['chains'])
            else:
                df = pd.DataFrame(response['bridges'])

        return df

    


    # /bridges/{id}




    # /bridgevolume/{chain}
    # /bridgedaystats/{timestamp}/{chain}
    

    def get_bridge_day_stats(self, timestamp: int, chains: Union[str, List[str]], params: Dict = None, raw: bool = True):
        """
        Get a 24hr token and address volume breakdown for a bridge.
        
        Endpoint: /bridgedaystats/{timestamp}/{chain}

        Parameters:
        - timestamp (int, required): Unix timestamp. Data returned will be for the 24hr period starting at 00:00 UTC that the timestamp lands in.
        - chains (str, required): chain slug, you can get these from get_chains().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - id (int): bridge ID, you can get these from get_bridges().
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """


    def get_bridge_transactions(self, id: int, params: Dict = None, raw: bool = True):
        """
        Get all transactions for a bridge within a date range.
        
        Endpoint: /transactions/{id}

        Parameters:
        - id (int, required): bridge ID, you can get these from get_bridges().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - starttimestamp (int): start timestamp (Unix Timestamp) for date range
            - endtimestamp (int): end timestamp (Unix timestamp) for date range
            - sourcechain (str): returns only transactions that are bridging from the specified source chain
            - address (str): Returns only transactions with specified address as "from" or "to". Addresses are quried in the form {chain}:{address}, where chain is an identifier such as ethereum, bsc, polygon, avax... .
            - limit (int): limit to number of transactions returned, maximum is 6000
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. 
                                Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """

        if not params:
            params = {}

        query_string = urlencode(params)
        endpoint = f"/transactions/{id}?{query_string}"
        response = self._get(endpoint, params=params)

        if raw:
            return response
        else:
            df = pd.DataFrame(response)
            return df


    # --- Volumes --- #
    
    # this is likely broken based on changing function definition inputs
    def get_dex_volume(self, params: Dict = None, raw: bool = True):
        """
        Get all dexs along wtih summaries of their volumes and dataType history data.
        
        Endpoint: /overview/dexs
                
        Parameters:
        - params (Dict, optional): Dictionary containing optional API parameters.
            - excludeTotalDataChart (bool, optional): True to exclude aggregated chart from response. Defaults to False.
            - excludeTotalDataChartBreakdown (bool, optional): True to exclude broken down chart from response. Defaults to False.
            - dataType (string, optional): Desired data type. Available values are dailyVolume, totalVolume. Defaults to dailyVolume.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """
        
        if not params:
            raise ValueError("params dictionary is missing.")
        
        query_string = urlencode(params)
        endpoint = f"/overview/dexs?{query_string}"

        if raw:
            return self._get('VOLUMES', endpoint, params=params)

        elif not raw:
            if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                response = self._get('VOLUMES', endpoint, params=params)
                
                df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                return df
            
            elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                response = self._get('VOLUMES', endpoint, params=params)
            
                records = []
                for item in response['totalDataChartBreakdown']:
                    timestamp, protocols = item
                    for protocol, volume in protocols.items():
                        records.append({'date': timestamp, 'protocol': protocol, 'volume': volume})

                df = pd.DataFrame(records)
                return df
            
            elif params['excludeTotalDataChart'] == params['excludeTotalDataChartBreakdown']:
                raise ValueError("Both excludeTotalDataChart and excludeTotalDataChartBreakdown cannot have the same value (either both True or both False) if raw = False.")



    # is the response from allChains in /overview/chains the same as using get_chains()?
    def get_chain_perps_volume(self, chains: Union[str, List[str]], params: Dict = None, raw: bool = True):
        """
        Get all dexs along with summaries of their volumes and dataType history data filtering by chain.
        
        Endpoint: /overview/dexs/{chain}
                
        Parameters:
        - chains (str, required): chain slug, you can get these from get_chains().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - excludeTotalDataChart (bool, optional): True to exclude aggregated chart from response. Defaults to False.
            - excludeTotalDataChartBreakdown (bool, optional): True to exclude broken down chart from response. Defaults to False.
            - dataType (string, optional): Desired data type. Available values are dailyVolume, totalVolume. Defaults to dailyVolume.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """
            
        if isinstance(chains, str):
            chains = [chains]
        elif not isinstance(chains, list):
            raise ValueError("chains must be either a string or a list of strings.")
        
        if not params:
            raise ValueError("params dictionary is missing.")
        
        query_string = urlencode(params)

        results = []
        for chain in chains:
            endpoint = f"/overview/dexs/{chain}?{query_string}"

            if raw:
                results.append(self._get('VOLUMES', endpoint, params=params))
            else:
                if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                    response = self._get('VOLUMES', endpoint, params=params)
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    df = df[['date', 'chain', 'volume']]
                    df = self._clean_chain_name(df)
                    results.append(df)

                elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                    response = self._get('VOLUMES', endpoint, params=params)

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

    
    def get_summary_dex_volume(self, protocols: Union[str, List[str]], params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get summary of dex volume with historical data.
        
        Endpoint: /summary/dexs/{protocol}

        Parameters:
        - protocols (str or List[str], required): protocol slug(s) — you can get these from get_protocols().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - excludeTotalDataChart (bool, optional): True to exclude aggregated chart from response. Defaults to False.
            - excludeTotalDataChartBreakdown (bool, optional): True to exclude broken down chart from response. Defaults to False.
            - dataType (string, optional): Desired data type. Available values are dailyVolume, totalVolume. Defaults to dailyVolume.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """


    # this is likely broken based on changing function definition inputs
    def get_perps_volume(self, params: Dict = None, raw: bool = True):
        """
        Get all perps dexs along wtih summaries of their volumes and dataType history data.
        
        Endpoint: /overview/derivatives
                
        Parameters:
        - params (Dict, optional): Dictionary containing optional API parameters.
            - excludeTotalDataChart (bool, optional): True to exclude aggregated chart from response. Defaults to False.
            - excludeTotalDataChartBreakdown (bool, optional): True to exclude broken down chart from response. Defaults to False.
            - dataType (string, optional): Desired data type. Available values are dailyVolume, totalVolume. Defaults to dailyVolume.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """
        if params:
            query_string = urlencode(params)
            endpoint = f"/overview/derivatives?{query_string}"
            
        elif not params:
            raise ValueError("params dictionary is missing.")
        
        if raw:
            return self._get('VOLUMES', endpoint, params=params)

        elif not raw:
            if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                response = self._get('VOLUMES', endpoint, params=params)
                
                df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                return df
            
            elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                response = self._get('VOLUMES', endpoint, params=params)
            
                records = []
                for item in response['totalDataChartBreakdown']:
                    timestamp, protocols = item
                    for protocol, volume in protocols.items():
                        records.append({'date': timestamp, 'protocol': protocol, 'volume': volume})

                df = pd.DataFrame(records)
                return df
            
            elif params['excludeTotalDataChart'] == params['excludeTotalDataChartBreakdown']:
                raise ValueError("Both excludeTotalDataChart and excludeTotalDataChartBreakdown cannot have the same value (either both True or both False) if raw = False.")


    # is the response from allChains in /overview/derivatives the same as using get_chains()?
    def get_chain_perps_volume(self, chains: Union[str, List[str]], params: Dict = None, raw: bool = True):
        """
        Get all perps dexs along with summaries of their volumes and dataType history data filtering by chain.
        
        Endpoint: /overview/derivatives/{chain}
                
        Parameters:
        - chains (str, required): chain slug, you can get these from get_chains().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - excludeTotalDataChart (bool, optional): True to exclude aggregated chart from response. Defaults to False.
            - excludeTotalDataChartBreakdown (bool, optional): True to exclude broken down chart from response. Defaults to False.
            - dataType (string, optional): Desired data type. Available values are dailyVolume, totalVolume. Defaults to dailyVolume.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
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
                results.append(self._get('VOLUMES', endpoint, params=params))
            else:
                if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                    response = self._get('VOLUMES', endpoint, params=params)
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    df = df[['date', 'chain', 'volume']]
                    df = self._clean_chain_name(df)
                    results.append(df)

                elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                    response = self._get('VOLUMES', endpoint, params=params)

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

    
    def get_summary_perps_volume(self, protocols: Union[str, List[str]], params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get summary of perps dex volume with historical data.
        
        Endpoint: /summary/derivatives/{protocol}

        Parameters:
        - protocols (str or List[str], required): protocol slug(s) — you can get these from get_protocols().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - excludeTotalDataChart (bool, optional): True to exclude aggregated chart from response. Defaults to False.
            - excludeTotalDataChartBreakdown (bool, optional): True to exclude broken down chart from response. Defaults to False.
            - dataType (string, optional): Desired data type. Available values are dailyVolume, totalVolume. Defaults to dailyVolume.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """


    # this is likely broken based on changing function definition inputs
    def get_options_volume(self, params: Dict = None, raw: bool = True):
        """
        Get all options dexs along wtih summaries of their volumes and dataType history data.
        
        Endpoint: /overview/options
                
        Parameters:
        - params (Dict, optional): Dictionary containing optional API parameters.
            - excludeTotalDataChart (bool, optional): True to exclude aggregated chart from response. Defaults to False.
            - excludeTotalDataChartBreakdown (bool, optional): True to exclude broken down chart from response. Defaults to False.
            - dataType (string, optional): Desired data type. Available values are dailyPremiumVolume, dailyNotionalVolume, totalPremiumVolume, or totalNotionalVolume. Defaults to dailyNotionalVolume.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """
        if params:
            query_string = urlencode(params)
            endpoint = f"/overview/options?{query_string}"
            
        elif not params:
            raise ValueError("params dictionary is missing.")
        
        if raw:
            return self._get('VOLUMES', endpoint, params=params)

        elif not raw:
            if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                response = self._get('VOLUMES', endpoint, params=params)
                
                df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                return df
            
            elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                response = self._get('VOLUMES', endpoint, params=params)
            
                records = []
                for item in response['totalDataChartBreakdown']:
                    timestamp, protocols = item
                    for protocol, volume in protocols.items():
                        records.append({'date': timestamp, 'protocol': protocol, 'volume': volume})

                df = pd.DataFrame(records)
                return df
            
            elif params['excludeTotalDataChart'] == params['excludeTotalDataChartBreakdown']:
                raise ValueError("Both excludeTotalDataChart and excludeTotalDataChartBreakdown cannot have the same value (either both True or both False) if raw = False.")


    # is the response from allChains in /overview/options the same as using get_chains()?
    def get_chain_options_volume(self, chains: Union[str, List[str]], params: Dict = None, raw: bool = True):
        """
        Get all options dexs along with summaries of their volumes and dataType history data filtering by chain.
        
        Endpoint: /overview/options/{chain}
                
        Parameters:
        - chains (str, required): chain slug, you can get these from get_chains().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - excludeTotalDataChart (bool, optional): True to exclude aggregated chart from response. Defaults to False.
            - excludeTotalDataChartBreakdown (bool, optional): True to exclude broken down chart from response. Defaults to False.
            - dataType (string, optional): Desired data type. Available values are dailyPremiumVolume, dailyNotionalVolume, totalPremiumVolume, or totalNotionalVolume. Defaults to dailyNotionalVolume.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
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
                results.append(self._get('VOLUMES', endpoint, params=params))
            else:
                if params['excludeTotalDataChart'] == False and params['excludeTotalDataChartBreakdown'] == True:
                    response = self._get('VOLUMES', endpoint, params=params)
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    df = df[['date', 'chain', 'volume']]
                    df = self._clean_chain_name(df)
                    results.append(df)

                elif params['excludeTotalDataChart'] == True and params['excludeTotalDataChartBreakdown'] == False:
                    response = self._get('VOLUMES', endpoint, params=params)

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
    

    def get_summary_options_volume(self, protocols: Union[str, List[str]], params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get summary of options dex volume with historical data.
        
        Endpoint: /summary/options/{protocol}

        Parameters:
        - protocols (str or List[str], required): protocol slug(s) — you can get these from get_protocols().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - dataType (string, optional): Desired data type. Available values are totalFees, dailyFees, totalRevenue, dailyRevenue. Defaults to dailyFees.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """


    # --- Fees --- #

    def get_fees_revenue(self, params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get all protocols along with summaries of their fees and revenue and dataType history data.
        
        Endpoint: /overview/fees

        Parameters:
        - params (Dict, optional): Dictionary containing optional API parameters.
            - excludeTotalDataChart (bool, optional): True to exclude aggregated chart from response. Defaults to False.
            - excludeTotalDataChartBreakdown (bool, optional): True to exclude broken down chart from response. Defaults to False.
            - dataType (string, optional): Desired data type. Available values are totalFees, dailyFees, totalRevenue, dailyRevenue. Defaults to dailyFees.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """

    # is the response from allChains in /overview/fees the same as using get_chains()?
    def get_chain_fees_revenue(self, chains: Union[str, List[str]], params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get all protocols along with summaries of their fees and revenue and dataType history data by chain.
        
        Endpoint: /overview/fees/{chain}

        Parameters:
        - chains (str or List[str], required): chain slug(s) — you can get these from get_chains().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - excludeTotalDataChart (bool, optional): True to exclude aggregated chart from response. Defaults to False.
            - excludeTotalDataChartBreakdown (bool, optional): True to exclude broken down chart from response. Defaults to False.
            - dataType (string, optional): Desired data type. Available values are totalFees, dailyFees, totalRevenue, dailyRevenue. Defaults to dailyFees.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """
    
    
    def get_summary_protocol_fees_revenue(self, protocols: Union[str, List[str]], params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get summary of protocol fees and revenue with historical data.

        Endpoint: /summary/fees/{protocol}

        Parameters:
        - protocols (str or List[str], required): Protocol slug(s) — you can get these from get_protocols().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - dataType (string, optional): Desired data type. Available values are totalFees, dailyFees, totalRevenue, dailyRevenue. Defaults to dailyFees.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """
