// SPDX-License-Identifier: MIT

pragma solidity <=0.8.10;
pragma experimental ABIEncoderV2;

import "./../interfaces/Structs.sol";
import "./DyDxPool.sol";
import "./DyDxFlashLoan.sol";

contract Arbitrage is DyDxFlashLoan {
    address public owner;

    constructor() public {
        owner = msg.sender;
    }

    function executeTrade(
        address _token0,
        uint256 _flashAmount,
        address profitReciever
    ) external {
        uint256 balanceBefore = IERC20(_token0).balanceOf(address(this));

        bytes memory data = abi.encode(
            _token0,
            _flashAmount,
            balanceBefore,
            profitReciever
        );

        flashloan(_token0, _flashAmount, data); // execution goes to `callFunction`
    }

    function callFunction(
        address, /* sender */
        Info calldata, /* accountInfo */
        bytes calldata data
    ) external OnlyPool {
        (
            address token0,
            uint256 flashAmount,
            uint256 balanceBefore,
            address profitReciever
        ) = abi.decode(data, (address, uint256, uint256, address));

        uint256 balanceAfter = IERC20(token0).balanceOf(address(this));

        require(
            balanceAfter - balanceBefore == flashAmount,
            "contract did not get the loan"
        );

        IERC20(token0).transfer(
            profitReciever,
            IERC20(token0).balanceOf(address(this)) - (flashAmount + 1)
        );
    }


}
