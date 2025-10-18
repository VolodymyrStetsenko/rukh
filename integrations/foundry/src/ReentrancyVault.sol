// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ReentrancyVault
 * @notice Demo vulnerable contract for RUKH testing
 * @dev Contains intentional reentrancy vulnerability for educational purposes
 * @author Volodymyr Stetsenko (Zero2Auditor)
 */
contract ReentrancyVault {
    mapping(address => uint256) public balances;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    
    /**
     * @notice Deposit ETH into the vault
     */
    function deposit() external payable {
        require(msg.value > 0, "Must deposit non-zero amount");
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }
    
    /**
     * @notice Withdraw ETH from the vault
     * @dev VULNERABLE: External call before state update allows reentrancy
     * @param amount Amount to withdraw
     */
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // VULNERABILITY: External call before state update
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        // State update happens AFTER external call
        balances[msg.sender] -= amount;
        emit Withdrawal(msg.sender, amount);
    }
    
    /**
     * @notice Get contract balance
     */
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
    
    /**
     * @notice Get user balance
     */
    function getUserBalance(address user) external view returns (uint256) {
        return balances[user];
    }
}

