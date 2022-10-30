from brownie import accounts, interface
from datetime import datetime
from web3 import Web3

"""
We execute a swap to test the bot.py functions ( determine_profitability, determine_direction, execute_trade)
"""

WETH_TOKEN = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC_TOKEN = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

WETH_HOLDER = "0x56178a0d5F301bAf6CF3e1Cd53d9863437345Bf9"

path = [WETH_TOKEN, USDC_TOKEN]


def main():
    manipulate()


def manipulate():
    account = WETH_HOLDER
    router = interface.IUniswapV2Router02("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")

    amount_in = int(Web3.toWei(100, "ether"))

    erc = interface.IERC20(WETH_TOKEN)
    erc.approve(router, amount_in, {"from": account})

    tx = router.swapExactTokensForTokens(
        amount_in,
        1,
        path,
        accounts[0],
        datetime.now().timestamp() + 250,
        {"from": account},
    )
