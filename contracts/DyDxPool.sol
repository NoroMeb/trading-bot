// SPDX-License-Identifier: MIT

pragma solidity <=0.8.10;
pragma experimental ABIEncoderV2;

import "./../interfaces/Structs.sol";

abstract contract DyDxPool is Structs {
    function operate(Info[] memory, ActionArgs[] memory) public virtual;
}
