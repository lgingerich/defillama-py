# TO DO:

# packaged transformations should return only critical data (no metadata). for a tvl endpoint, only return tvl
# handle potential rate limiting: 500 requests / min
# check that function inputs (chains, protocols, coins, etc.) exist
# check is instance and type check matching
# lots of work to do on error handling, type checking, type enforcement, etc.
# make sure the test paths are accessed properly for when anyone new downloads and runs the code
# follow this logic for all functions: exclude_chart = params.get("excludeTotalDataChart", False)
# what happens if the first protocol/chain in my input list is shorter than the later options?
# maybe add dynamic column names. can reference get_protocol_fees_revenue() implentation

# technically returning a list of Dicts in many cases, may need to change "Returns" comment under each function
# `params` only ever contains optional parameters. required parameters are explicity called in the function definition.

import requests
import pandas as pd
from typing import Union, List, Dict
from urllib.parse import urlencode

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
        BASE_URLS = {
            'TVL': TVL_URL,
            'COINS': COINS_URL,
            'STABLECOINS': STABLECOINS_URL,
            'YIELDS': YIELDS_URL,
            'ABI': ABI_URL,
            'BRIDGES': BRIDGES_URL,
            'VOLUMES': VOLUMES_URL,
            'FEES': FEES_URL
        }

        base_url = BASE_URLS.get(api_tag)
        if not base_url:
            raise ValueError(f"'{api_tag}' is not a valid API tag.")
        
        url = base_url + endpoint

        try:
            response = self.session.request('GET', url, timeout=30, params=params)
            print(f"Calling API endpoint: {response.url}")
            response.raise_for_status()
        except requests.Timeout:
            raise TimeoutError(f"Request to '{response.url}' timed out.")
        except requests.RequestException as e:
            raise ConnectionError(f"An error occurred while trying to connect to '{response.url}'. {str(e)}")
        
        try:
            return response.json()
        except ValueError:
            raise ValueError(f"Invalid JSON response received from '{response.url}'.")

        
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

    # should these helper functions include all static info rather than only bare minimum?? 
    #   leaning towards yes.

    
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
    # all tvl endpoints manually checked. seem good, need to write tests still
    
    
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

        else:
            results = []

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

        else:
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

        else:
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
        # Convert chains to list if it's a string
        if isinstance(chains, str):
            chains = [chains]

        if raw:
            if len(chains) == 1:
                return self._get('TVL', endpoint=f'/v2/historicalChainTvl/{chains[0]}')
            
            results = {}
            for chain in chains:
                results[chain] = self._get('TVL', endpoint=f'/v2/historicalChainTvl/{chain}')
            return results

        else:
            results = []

            for chain in chains:
                chain_data = self._get('TVL', endpoint=f'/v2/historicalChainTvl/{chain}')
                for entry in chain_data:
                    entry['chain'] = chain
                    results.append(entry)

            df = pd.DataFrame(results)
            return self._clean_chain_name(df)


    def get_protocol_current_tvl(self, protocols: Union[str, List[str]], raw: bool = True) -> Union[float, Dict[str, float], pd.DataFrame]:
        """
        Get current Total Value Locked (TVL) for the specified protocols.

        Endpoint: /tvl/{protocol}

        Parameters:
        - protocols (str or List[str], required): A list containing names of the desired protocol(s).
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - float or Dict[str, float] or DataFrame: Raw data from the API or a transformed DataFrame.
            - If a single protocol is provided and raw=True, returns the TVL as a float.
            - If multiple protocols are provided and raw=True, returns a dictionary mapping each protocol name to its TVL.
            - If raw=False, returns a DataFrame.
        """
        # Convert protocols to list if it's a string
        if isinstance(protocols, str):
            protocols = [protocols]
        
        if raw:
            if len(protocols) == 1:
                return float(self._get('TVL', endpoint=f'/tvl/{protocols[0]}'))
            
            results = {}
            for protocol in protocols:
                data = self._get('TVL', endpoint=f'/tvl/{protocol}')
                results[protocol] = float(data)

            return results

        else:
            results = []
            for protocol in protocols:
                tvl = float(self._get('TVL', endpoint=f'/tvl/{protocol}'))
                results.append({
                    'protocol': protocol,
                    'tvl': tvl
                })

            df = pd.DataFrame(results)
            return self._clean_chain_name(df)


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

        else:
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
    
    def get_all_bridge_volume(self, params: Dict = None, raw: bool = True) -> Union[Dict, pd.DataFrame]:
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
        response = self._get('BRIDGES', '/bridges', params=params)

        if raw:
            return response
        else:
            return pd.DataFrame(response['bridges'])
    

    # still need to handle raw=False
    def get_bridge_volume(self, ids: List[str], raw: bool = True) -> Union[Dict, pd.DataFrame]:
        """
        Get summary of bridge volume and volume breakdown by chain.
        
        Endpoint: /bridges/{id}

        Parameters:
        - ids (str or List[str], required): A list containing id's of the desired bridge(s).
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. 
                                Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """
        if isinstance(ids, str):
            ids = [ids]
        
        if raw:
            if len(ids) == 1:
                return self._get('BRIDGES', endpoint=f'/bridges/{ids[0]}')
            
            results = {}
            for id in ids:
                results[id] = self._get('BRIDGES', endpoint=f'/bridges/{ids}')
            return results


    # still need to handle raw=False
    def get_chain_bridge_volume(self, chains: List[str], params: Dict = None, raw: bool = True) -> Union[Dict, pd.DataFrame]:
        """
        Get historical volumes for a bridge, chain, or bridge on a particular chain.
        
        Endpoint: /bridgevolume/{chain}

        Parameters:
        - chains (str or List[str], required): A list containing id's of the desired bridge(s).
        - params (Dict, optional): Dictionary containing optional API parameters.
            - id (int): Id's of the desired bridge(s).
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. 
                                Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """
        if isinstance(chains, str):
            chains = [chains]
        
        if raw:
            if len(chains) == 1:
                return self._get('BRIDGES', endpoint=f'/bridgevolume/{chains[0]}')
            
            results = {}
            for chain in chains:
                results[chain] = self._get('BRIDGES', endpoint=f'/bridgevolume/{chains}')
            return results
    
    
    # still need to handle raw=False
    def get_chain_bridge_day_volume(self, timestamp: int, chains: List[str], params: Dict = None, raw: bool = True) -> Union[Dict, pd.DataFrame]:
        """
        Get a 24hr token and address volume breakdown for a bridge.
        
        Endpoint: /bridgedaystats/{timestamp}/{chain}

        Parameters:
        - timestamp (int, required): Unix timestamp. Data returned will be for the 24hr period starting at 00:00 UTC that the timestamp lands in.
        - chains (str or List[str], required): chain slug(s) — you can get these from get_chains().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - id (int): Id's of the desired bridge(s).
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. 
                                Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """       
        
        if isinstance(chains, str):
            chains = [chains]
        
        if raw:
            if len(chains) == 1:
                return self._get('BRIDGES', endpoint=f'/bridgedaystats/{timestamp}/{chains[0]}')
            
            results = {}
            for chain in chains:
                results[chain] = self._get('BRIDGES', endpoint=f'/bridgedaystats/{timestamp}/{chains}')
            return results    
        # doesn't work for multiple chains
    
    
    
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



    # --- Volumes --- #
    
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
        response = self._get('VOLUMES', '/overview/dexs', params=params)

        if raw:
            return response
        else:
            exclude_chart = params.get('excludeTotalDataChart', False) if params else False
            exclude_chart_breakdown = params.get('excludeTotalDataChartBreakdown', False) if params else False

            if not exclude_chart and exclude_chart_breakdown:
                return pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])

            elif exclude_chart and not exclude_chart_breakdown:
                records = []
                for item in response['totalDataChartBreakdown']:
                    timestamp, protocols = item
                    for protocol, volume in protocols.items():
                        records.append({'date': timestamp, 'protocol': protocol, 'volume': volume})

                return pd.DataFrame(records)

            # Default return 'totalDataChart' if raw = False and params.excludeTotalDataChart = params.excludeTotalDataChartBreakdown
            else:
                return pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])


    def get_chain_dex_volume(self, chains: Union[str, List[str]], params: Dict = None, raw: bool = True):
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

        results = {}
        dfs = []
        
        for chain in chains:
            response = self._get('VOLUMES', f"/overview/dexs/{chain}", params=params)
            if response.get("totalDataChart") is None and response.get("totalDataChartBreakdown") is None:
                raise ValueError(f"No data available for hain: {chain} with dataType: {params.get('dataType', 'dailyVolume')}")

            if raw:
                results[chain] = response
            else:
                if not params or (not params.get('excludeTotalDataChart', False) and params.get('excludeTotalDataChartBreakdown', False)):
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    dfs.append(self._clean_chain_name(df))

                elif params.get('excludeTotalDataChart', False) and not params.get('excludeTotalDataChartBreakdown', False):
                    records = []
                    for item in response['totalDataChartBreakdown']:
                        timestamp, protocols = item
                        for protocol, volume in protocols.items():
                            records.append({'date': timestamp, 'chain': chain, 'protocol': protocol, 'volume': volume})
                    df = pd.DataFrame(records)
                    dfs.append(self._clean_chain_name(df))
                    
                else:
                    # Default return 'totalDataChart' if raw = False and params.excludeTotalDataChart = params.excludeTotalDataChartBreakdown
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    dfs.append(self._clean_chain_name(df))
        
        if raw:
            return results
        else:
            return pd.concat(dfs, ignore_index=True)

    
    def get_protocol_dex_volume(self, protocols: Union[str, List[str]], params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get summary of protocol dex volume with historical data.
        
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
        if isinstance(protocols, str):
            protocols = [protocols]

        results = {}

        for protocol in protocols:
            response = self._get('VOLUMES', f'/summary/dexs/{protocol}', params=params)
            if response.get("totalDataChart") is None and response.get("totalDataChartBreakdown") is None:
                raise ValueError(f"No data available for dex protocol: {protocol} with dataType: {params.get('dataType', 'dailyVolume')}")
            results[protocol] = response

        if raw:
            return results
        else:
            exclude_chart = params.get("excludeTotalDataChart", False)
            exclude_chart_breakdown = params.get("excludeTotalDataChartBreakdown", False)

            all_data = []
            
            for protocol, data in results.items():
                # Handle case for totalDataChart
                if not exclude_chart and exclude_chart_breakdown:
                    for timestamp, volume in data["totalDataChart"]:
                        all_data.append({
                            "timestamp": timestamp,
                            "protocol": protocol,
                            "volume": volume
                        })

                # Handle case for totalDataChartBreakdown
                elif not exclude_chart_breakdown and exclude_chart:
                        for timestamp, chains in data["totalDataChartBreakdown"]:
                            for chain, protocols_data in chains.items():
                                for protocol_version, volume in protocols_data.items():
                                    all_data.append({
                                        "timestamp": timestamp,
                                        "chain": chain,
                                        "protocol": protocol,
                                        "protocol_version": protocol_version,
                                        "volume": volume
                                    })
                else:
                    for timestamp, volume in data["totalDataChart"]:
                        all_data.append({
                            "timestamp": timestamp,
                            "protocol": protocol,
                            "volume": volume
                        })

            return pd.DataFrame(all_data)


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
        response = self._get('VOLUMES', '/overview/derivatives', params=params)

        if raw:
            return response
        else:
            exclude_chart = params.get('excludeTotalDataChart', False) if params else False
            exclude_chart_breakdown = params.get('excludeTotalDataChartBreakdown', False) if params else False

            if not exclude_chart and exclude_chart_breakdown:
                return pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])

            elif exclude_chart and not exclude_chart_breakdown:
                records = []
                for item in response['totalDataChartBreakdown']:
                    timestamp, protocols = item
                    for protocol, volume in protocols.items():
                        records.append({'date': timestamp, 'protocol': protocol, 'volume': volume})

                return pd.DataFrame(records)

            # Default return 'totalDataChart' if raw = False and params.excludeTotalDataChart = params.excludeTotalDataChartBreakdown
            else:
                return pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
            

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

        results = {}
        dfs = []
        
        for chain in chains:
            response = self._get('VOLUMES', f"/overview/derivatives/{chain}", params=params)
            if response.get("totalDataChart") is None and response.get("totalDataChartBreakdown") is None:
                raise ValueError(f"No data available for chain: {chain} with dataType: {params.get('dataType', 'dailyVolume')}")

            if raw:
                results[chain] = response
            else:
                if not params or (not params.get('excludeTotalDataChart', False) and params.get('excludeTotalDataChartBreakdown', False)):
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    dfs.append(self._clean_chain_name(df))

                elif params.get('excludeTotalDataChart', False) and not params.get('excludeTotalDataChartBreakdown', False):
                    records = []
                    for item in response['totalDataChartBreakdown']:
                        timestamp, protocols = item
                        for protocol, volume in protocols.items():
                            records.append({'date': timestamp, 'chain': chain, 'protocol': protocol, 'volume': volume})
                    df = pd.DataFrame(records)
                    dfs.append(self._clean_chain_name(df))
                    
                else:
                    # Default return 'totalDataChart' if raw = False and params.excludeTotalDataChart = params.excludeTotalDataChartBreakdown
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    dfs.append(self._clean_chain_name(df))
        
        if raw:
            return results
        else:
            return pd.concat(dfs, ignore_index=True)

    
    def get_protocol_perps_volume(self, protocols: Union[str, List[str]], params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get summary of protocol perps dex volume with historical data.
        
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
        if isinstance(protocols, str):
            protocols = [protocols]

        results = {}

        for protocol in protocols:
            response = self._get('VOLUMES', f'/summary/derivatives/{protocol}', params=params)
            if response.get("totalDataChart") is None and response.get("totalDataChartBreakdown") is None:
                raise ValueError(f"No data available for perps protocol: {protocol} with dataType: {params.get('dataType', 'dailyVolume')}")
            results[protocol] = response

        if raw:
            return results
        else:
            exclude_chart = params.get("excludeTotalDataChart", False)
            exclude_chart_breakdown = params.get("excludeTotalDataChartBreakdown", False)

            all_data = []
            
            for protocol, data in results.items():
                # Handle case for totalDataChart
                if not exclude_chart and exclude_chart_breakdown:
                    for timestamp, volume in data["totalDataChart"]:
                        all_data.append({
                            "timestamp": timestamp,
                            "protocol": protocol,
                            "volume": volume
                        })

                # Handle case for totalDataChartBreakdown
                elif not exclude_chart_breakdown and exclude_chart:
                        for timestamp, chains in data["totalDataChartBreakdown"]:
                            for chain, protocols_data in chains.items():
                                for protocol_version, volume in protocols_data.items():
                                    all_data.append({
                                        "timestamp": timestamp,
                                        "chain": chain,
                                        "protocol": protocol,
                                        "protocol_version": protocol_version,
                                        "volume": volume
                                    })
                else:
                    for timestamp, volume in data["totalDataChart"]:
                        all_data.append({
                            "timestamp": timestamp,
                            "protocol": protocol,
                            "volume": volume
                        })

            return pd.DataFrame(all_data)


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
        response = self._get('VOLUMES', '/overview/options', params=params)

        if raw:
            return response
        else:
            exclude_chart = params.get('excludeTotalDataChart', False) if params else False
            exclude_chart_breakdown = params.get('excludeTotalDataChartBreakdown', False) if params else False

            if not exclude_chart and exclude_chart_breakdown:
                return pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])

            elif exclude_chart and not exclude_chart_breakdown:
                records = []
                for item in response['totalDataChartBreakdown']:
                    timestamp, protocols = item
                    for protocol, volume in protocols.items():
                        records.append({'date': timestamp, 'protocol': protocol, 'volume': volume})

                return pd.DataFrame(records)

            # Default return 'totalDataChart' if raw = False and params.excludeTotalDataChart = params.excludeTotalDataChartBreakdown
            else:
                return pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
        

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

        results = {}
        dfs = []
        
        for chain in chains:
            response = self._get('VOLUMES', f"/overview/options/{chain}", params=params)
            if response.get("totalDataChart") is None and response.get("totalDataChartBreakdown") is None:
                raise ValueError(f"No data available for chain: {chain} with dataType: {params.get('dataType', 'dailyNotionalVolume')}")

            if raw:
                results[chain] = response
            else:
                if not params or (not params.get('excludeTotalDataChart', False) and params.get('excludeTotalDataChartBreakdown', False)):
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    dfs.append(self._clean_chain_name(df))

                elif params.get('excludeTotalDataChart', False) and not params.get('excludeTotalDataChartBreakdown', False):
                    records = []
                    for item in response['totalDataChartBreakdown']:
                        timestamp, protocols = item
                        for protocol, volume in protocols.items():
                            records.append({'date': timestamp, 'chain': chain, 'protocol': protocol, 'volume': volume})
                    df = pd.DataFrame(records)
                    dfs.append(self._clean_chain_name(df))
                    
                else:
                    # Default return 'totalDataChart' if raw = False and params.excludeTotalDataChart = params.excludeTotalDataChartBreakdown
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', 'volume'])
                    df['chain'] = chain
                    dfs.append(self._clean_chain_name(df))
        
        if raw:
            return results
        else:
            return pd.concat(dfs, ignore_index=True)
    

    def get_protocol_options_volume(self, protocols: Union[str, List[str]], params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """
        Get summary of protocol options dex volume with historical data.
        
        Endpoint: /summary/options/{protocol}

        Parameters:
        - protocols (str or List[str], required): protocol slug(s) — you can get these from get_protocols().
        - params (Dict, optional): Dictionary containing optional API parameters.
            - dataType (string, optional): Desired data type. Available values are totalFees, dailyFees, totalRevenue, dailyRevenue. Defaults to dailyFees.
        - raw (bool, optional): If True, returns raw data. If False, returns a transformed DataFrame. Defaults to True.

        Returns:
        - Dict or DataFrame: Raw data from the API or a transformed DataFrame.
        """
        if isinstance(protocols, str):
            protocols = [protocols]

        results = {}

        for protocol in protocols:
            response = self._get('VOLUMES', f'/summary/options/{protocol}', params=params)
            if response.get("totalDataChart") is None and response.get("totalDataChartBreakdown") is None:
                raise ValueError(f"No data available for options protocol: {protocol} with dataType: {params.get('dataType', 'dailyFees')}")
            results[protocol] = response

        if raw:
            return results
        else:
            exclude_chart = params.get("excludeTotalDataChart", False)
            exclude_chart_breakdown = params.get("excludeTotalDataChartBreakdown", False)

            all_data = []
            
            for protocol, data in results.items():
                # Handle case for totalDataChart
                if not exclude_chart and exclude_chart_breakdown:
                    for timestamp, volume in data["totalDataChart"]:
                        all_data.append({
                            "timestamp": timestamp,
                            "protocol": protocol,
                            "volume": volume
                        })

                # Handle case for totalDataChartBreakdown
                elif not exclude_chart_breakdown and exclude_chart:
                        for timestamp, chains in data["totalDataChartBreakdown"]:
                            for chain, protocols_data in chains.items():
                                for protocol_version, volume in protocols_data.items():
                                    all_data.append({
                                        "timestamp": timestamp,
                                        "chain": chain,
                                        "protocol": protocol,
                                        "protocol_version": protocol_version,
                                        "volume": volume
                                    })
                else:
                    for timestamp, volume in data["totalDataChart"]:
                        all_data.append({
                            "timestamp": timestamp,
                            "protocol": protocol,
                            "volume": volume
                        })

            return pd.DataFrame(all_data)


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
        response = self._get('FEES', '/overview/fees', params=params)

        if raw:
            return response
        else:
            dataType = params.get("dataType", "dailyFees")
            fees_rev_col_name = dataType.replace("daily", "daily_").replace("total", "total_").lower()  # Transforming the dataType into a column name format

            exclude_chart = params.get('excludeTotalDataChart', False) if params else False
            exclude_chart_breakdown = params.get('excludeTotalDataChartBreakdown', False) if params else False

            if not exclude_chart and exclude_chart_breakdown:
                return pd.DataFrame(response['totalDataChart'], columns=['date', fees_rev_col_name])

            elif exclude_chart and not exclude_chart_breakdown:
                records = []
                for item in response['totalDataChartBreakdown']:
                    timestamp, protocols = item
                    for protocol, value in protocols.items():
                        records.append({
                            'date': timestamp, 
                            'protocol': protocol, 
                            fees_rev_col_name: value
                        })

                return pd.DataFrame(records)

            # Default return 'totalDataChart' if raw = False and params.excludeTotalDataChart = params.excludeTotalDataChartBreakdown
            else:
                return pd.DataFrame(response['totalDataChart'], columns=['date', fees_rev_col_name])


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
        if isinstance(chains, str):
            chains = [chains]

        results = {}
        dfs = []
        
        for chain in chains:
            response = self._get('FEES', f"/overview/fees/{chain}", params=params)
            if response.get("totalDataChart") is None and response.get("totalDataChartBreakdown") is None:
                raise ValueError(f"No data available for chain: {chain} with dataType: {params.get('dataType', 'dailyNotionalVolume')}")

            if raw:
                results[chain] = response
            else:
                dataType = params.get("dataType", "dailyFees")
                fees_rev_col_name = dataType.replace("daily", "daily_").replace("total", "total_").lower()  # Transforming the dataType into a column name format

                if not params or (not params.get('excludeTotalDataChart', False) and params.get('excludeTotalDataChartBreakdown', False)):
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', fees_rev_col_name])
                    df['chain'] = chain
                    dfs.append(self._clean_chain_name(df))

                elif params.get('excludeTotalDataChart', False) and not params.get('excludeTotalDataChartBreakdown', False):
                    records = []
                    for item in response['totalDataChartBreakdown']:
                        timestamp, protocols = item
                        for protocol, value in protocols.items():
                            records.append({
                                'date': timestamp, 
                                'chain': chain, 
                                'protocol': protocol, 
                                fees_rev_col_name: value
                            })
                    df = pd.DataFrame(records)
                    dfs.append(self._clean_chain_name(df))
                    
                else:
                    # Default return 'totalDataChart' if raw = False and params.excludeTotalDataChart = params.excludeTotalDataChartBreakdown
                    df = pd.DataFrame(response['totalDataChart'], columns=['date', fees_rev_col_name])
                    df['chain'] = chain
                    dfs.append(self._clean_chain_name(df))
        
        if raw:
            return results
        else:
            return pd.concat(dfs, ignore_index=True)
    
    
    def get_protocol_fees_revenue(self, protocols: Union[str, List[str]], params: Dict = None, raw: bool = True) -> Union[List[Dict], pd.DataFrame]:
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
        if isinstance(protocols, str):
            protocols = [protocols]

        results = {}

        for protocol in protocols:
            response = self._get('FEES', f'/summary/fees/{protocol}', params=params)
            if response.get("totalDataChart") is None and response.get("totalDataChartBreakdown") is None:
                raise ValueError(f"No data available for protocol: {protocol} with dataType: {params.get('dataType', 'dailyFees')}")
            results[protocol] = response

        if raw:
            return results
        else:
            # the /summary/fees/{protocol} endpoint doesn't actually have a flag for excludeTotalDataChart or 
            # excludeTotalDataChartBreakdown like the volume endpoints do, but the functionality works the same
            # here even without it.

            dataType = params.get("dataType", "dailyFees")
            fees_rev_col_name = dataType.replace("daily", "daily_").replace("total", "total_").lower()  # Transforming the dataType into a column name format

            exclude_chart = params.get("excludeTotalDataChart", False)
            exclude_chart_breakdown = params.get("excludeTotalDataChartBreakdown", False)

            all_data = []
            
            for protocol, data in results.items():
                # Handle case for totalDataChart
                if not exclude_chart and exclude_chart_breakdown:
                    for timestamp, value in data["totalDataChart"]:
                        all_data.append({
                            "timestamp": timestamp,
                            "protocol": protocol,
                            fees_rev_col_name: value
                        })

                # Handle case for totalDataChartBreakdown
                elif not exclude_chart_breakdown and exclude_chart:
                        for timestamp, chains in data["totalDataChartBreakdown"]:
                            for chain, protocols_data in chains.items():
                                for protocol_version, value in protocols_data.items():
                                    all_data.append({
                                        "timestamp": timestamp,
                                        "chain": chain,
                                        "protocol": protocol,
                                        "protocol_version": protocol_version,
                                        fees_rev_col_name: value 
                                    })
                else:
                    for timestamp, value in data["totalDataChart"]:
                        all_data.append({
                            "timestamp": timestamp,
                            "protocol": protocol,
                            fees_rev_col_name: value
                        })

            return pd.DataFrame(all_data)