from eth_utils import from_wei
from brownie import interface, config, network, accounts
import web3


WETH_HOLDER = config["networks"][network.show_active()]["weth_holder"]
WETH_TOKEN = config["networks"][network.show_active()]["weth_token"]


def calculate_price(pair_contract):
    """
    In a pair liquidity pool to calculate the estimated price of an asset we do
    reserve of the asset / reserve of the other asset
    """
    [reserve0, reserve1] = get_reserves(pair_contract)
    price = (reserve1 / (10**18)) / (reserve0 / (10**6))
    return price


def get_factory(factory_address):
    """
    to get the factory contract we need ABI and address
    the ABI is from the interface and the address we pass it as a parametre
    """
    factory = interface.IUniswapV2Factory(factory_address)
    return factory


def get_pair_address(factory, token0, token1, account):
    """
    we pass the tokens addresses to the factory contract to get the paire address
    """
    pair_address = factory.getPair(
        token0,
        token1,
        {"from": account},
    )
    return pair_address


def get_pair_contract(pair_address):
    """
    contract = ABI(interface) + pair address (parametre)
    """
    paire = interface.IUniswapV2Pair(pair_address)
    return paire


def get_reserves(pair_contract):
    """
    Call getReserves() of pair_contract to get the  reserves of the two tokens
    """
    [reserve0, reserve1, blockTimestampLast] = pair_contract.getReserves()
    return reserve0, reserve1


def determine_direction(uniswap_price, sushiswap_price):
    """
    If the uniswap price > sushiswap price we buy from uniswap and we sell in sushiswap and vice versa.
    and we return the path of the sell and buy actions
    """
    uniswap_router_contract = get_router_contract(
        config["networks"][network.show_active()]["uniswap"]["router_address"]
    )
    sushiswap_router_contract = get_router_contract(
        config["networks"][network.show_active()]["sushiswap"]["router_address"]
    )
    if uniswap_price < sushiswap_price:
        print("\nBuy on uniswap\n")
        print("Sell on sushiswap\n")
        return [uniswap_router_contract, sushiswap_router_contract]

    elif sushiswap_price < uniswap_price:
        print("\nBuy on sushiswap\n")
        print("Sell on Uniswap\n")
        return [sushiswap_router_contract, uniswap_router_contract]


def get_router_contract(router_address):
    """
    contract = ABI(interface) + router address (parametre)
    """
    router = interface.IUniswapV2Router02(router_address)
    return router


def get_erc20_contract(token):
    """
    contract = ABI(interface) + token address (parametre)
    """
    erc_20 = interface.IERC20(token)
    return erc_20


def get_balance(erc20_contract, account_address):
    """balance of an account"""
    balance = erc20_contract.balanceOf(account_address)
    return balance


def getEstimatedReturn(amount, _routerPath, _token0, _token1):
    """
    trade1 = [amount in, amount out]
    trade2 = [amount in, amount out]
    """
    trade1 = _routerPath[0].getAmountsOut(amount, [_token0, _token1])
    trade2 = _routerPath[1].getAmountsOut(trade1[1], [_token1, _token0])

    amountIn = from_wei(trade1[0], "ether")
    amountOut = from_wei(trade2[1], "ether")

    print(f"amountIN : {amountIn} \namountOUT : {amountOut}\n")

    return {amountIn, amountOut}


def fund_the_contract(contract):
    """
    Fund the contract(Arbitrage in this case) with WETH so it pays the flashloan fee
    """
    # approve token transfer to the smart contract .
    erc20_weth = get_erc20_contract(WETH_TOKEN)
    erc20_weth.approve(
        contract.address, int(web3.Web3.toWei(0.5, "ether")), {"from": WETH_HOLDER}
    )

    # transfer the funds so the contract can flashloan and pay the fees .
    erc20_weth.transfer(
        contract.address, int(web3.Web3.toWei(0.5, "ether")), {"from": WETH_HOLDER}
    )
