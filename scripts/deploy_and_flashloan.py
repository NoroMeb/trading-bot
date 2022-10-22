from brownie import Arbitrage, accounts, interface


WETH_TOKEN = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
WETH_HOLDER = "0x56178a0d5F301bAf6CF3e1Cd53d9863437345Bf9"
MY_ACCOUNT = "0x108A176896bAD4E05b5C4BE738839fDC4238c526"


def main():
    deploy()
    flash_loan()


def deploy():
    # Deploy the Arbitrage contract
    account = accounts[0]
    arbitrage = Arbitrage.deploy(
        {"from": account},
    )

    return arbitrage


def flash_loan():
    arbitrage = Arbitrage[-1]
    erc20 = interface.IERC20(WETH_TOKEN)
    # approve token transfer to the smart contract .
    tx1 = erc20.approve(arbitrage.address, 10, {"from": WETH_HOLDER})
    tx1.wait(1)
    # transfer the funds so the contract can flashloan and pay the fees .
    tx2 = erc20.transfer(arbitrage.address, 10, {"from": WETH_HOLDER})

    # Execute the flashloan
    tx = arbitrage.executeTrade(
        WETH_TOKEN,
        1,
        MY_ACCOUNT,
        {"from": arbitrage.address},
    )
    tx.wait(1)
