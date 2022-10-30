import decimal

import pytest
from brownie import accounts, config, network, Arbitrage
import asyncio
import web3

FEE = 0.02

from scripts.help_scripts import (
    get_erc20_contract,
    get_factory,
    get_pair_address,
    get_pair_contract,
    calculate_price,
    determine_direction,
    get_router_contract,
    get_reserves,
    getEstimatedReturn,
    fund_the_contract,
)

WETH_TOKEN = config["networks"][network.show_active()]["weth_token"]
USDC_TOKEN = config["networks"][network.show_active()]["usdc_token"]
DAI_TOKEN = config["networks"][network.show_active()]["dai_token"]
WETH_HOLDER = config["networks"][network.show_active()]["weth_holder"]
USDC_HOLDER = config["networks"][network.show_active()]["usdc_holder"]
DAI_HOLDER = config["networks"][network.show_active()]["dai_holder"]
MY_ACCOUNT = config["networks"][network.show_active()]["my_account"]


UNISWAP_FACTORY_ADDRESS = config["networks"][network.show_active()]["uniswap"][
    "factory_address"
]
SUSHISWAP_FACTORY_ADDRESS = config["networks"][network.show_active()]["sushiswap"][
    "factory_address"
]

UNISWAP_ROUTER_ADDRESS = config["networks"][network.show_active()]["uniswap"][
    "router_address"
]
SUSHISWAP_ROUTER_ADDRESS = config["networks"][network.show_active()]["sushiswap"][
    "router_address"
]


acct = accounts.load("MyAccount")
uniswap_factory = get_factory(UNISWAP_FACTORY_ADDRESS)
sushiswap_factory = get_factory(SUSHISWAP_FACTORY_ADDRESS)
uniswap_pair_address = get_pair_address(uniswap_factory, WETH_TOKEN, USDC_TOKEN, acct)
sushiswap_pair_address = get_pair_address(
    sushiswap_factory, WETH_TOKEN, USDC_TOKEN, acct
)
uniswap_pair = get_pair_contract(uniswap_pair_address)
sushiswap_pair = get_pair_contract(sushiswap_pair_address)


def main():

    arbitrage = deploy()

    fund_the_contract(arbitrage)

    # take the events swaps
    event_filter = []
    event_filter.append(uniswap_pair.events.Swap.createFilter(fromBlock="latest"))
    event_filter.append(sushiswap_pair.events.Swap.createFilter(fromBlock="latest"))

    loop = asyncio.get_event_loop()
    try:
        print("waiting for a swap ...")

        loop.run_until_complete(asyncio.gather(log_loop(event_filter, 2)))

    finally:
        loop.close()


"""
when an event (swap in this case) we execute the following function
"""


def handle_event(event):

    print(web3.Web3.toJSON(event))

    uniswap_price = calculate_price(uniswap_pair)
    sushiswap_price = calculate_price(sushiswap_pair)

    print(f"\nUniswap price : {uniswap_price} WETH | USDC")
    print(f"Sushiswap price : {sushiswap_price} WETH | USDC \n")

    router_path = determine_direction(uniswap_price, sushiswap_price)

    profitable, flash_amount = determine_profitability(
        router_path, WETH_TOKEN, USDC_TOKEN
    )

    if profitable == True:
        execute_trade(router_path, WETH_TOKEN, USDC_TOKEN, flash_amount)
    elif profitable == False:
        print("NOT PROFITABLE !!!")

    print("waiting for a swap ...")


# waiting for swaps
async def log_loop(event_filter, poll_interval):
    while True:
        for events in event_filter:
            for event in events.get_new_entries():
                handle_event(event)
            await asyncio.sleep(poll_interval)


def execute_trade(router_path, token0, token1, flash_amount):

    if router_path[0] == UNISWAP_ROUTER_ADDRESS:
        start_on_uniswap = True
    elif router_path[0] == SUSHISWAP_ROUTER_ADDRESS:
        start_on_uniswap == False

    arbitrage = Arbitrage[-1]

    # Execute the Trade
    tx = arbitrage.executeTrade(
        start_on_uniswap, token0, token1, flash_amount, {"from": arbitrage.address}
    )

    if tx:
        print("Trade executed succefully")
    else:
        print("Failed :(")


def deploy():
    # Deploy the Arbitrage contract
    account = accounts[0]
    arbitrage = Arbitrage.deploy(
        SUSHISWAP_ROUTER_ADDRESS,
        UNISWAP_ROUTER_ADDRESS,
        {"from": account},
    )

    return arbitrage


def determine_profitability(router_path, token0, token1):

    router = get_router_contract(router_path[0])

    """
    amount_out : amount we get when we swap amount_in
    amount_in : amount w put to get amount_out
    """
    amount_out = web3.Web3.toWei(5000, "mwei")
    amount_in, amount_out = router.getAmountsIn(
        amount_out, [token0, token1], {"from": accounts[0]}
    )

    flash_amount = amount_in
    flash_amount = flash_amount * 10**18

    amountIn, amountOut = getEstimatedReturn(flash_amount, router_path, token0, token1)

    if amountIn > (amountOut + (decimal.Decimal(flash_amount * FEE / 100))):
        return True, flash_amount
    else:
        return False, flash_amount
