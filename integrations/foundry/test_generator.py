"""
RUKH Foundry Test Generator
Automatically generates Foundry tests from vulnerabilities
Author: Volodymyr Stetsenko (Zero2Auditor)
"""

import os
import json
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class TestTemplate:
    """Test template data"""
    name: str
    vulnerability_type: str
    test_code: str


class FoundryTestGenerator:
    """Generates Foundry test suites"""
    
    def __init__(self, contract_name: str, contract_path: str):
        self.contract_name = contract_name
        self.contract_path = contract_path
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load test templates for common vulnerabilities"""
        return {
            'reentrancy': self._reentrancy_template(),
            'access-control': self._access_control_template(),
            'arithmetic': self._arithmetic_template(),
            'unchecked-call': self._unchecked_call_template(),
            'delegatecall': self._delegatecall_template(),
            'timestamp-dependence': self._timestamp_template(),
            'tx-origin': self._tx_origin_template(),
        }
    
    def generate_test_suite(self, vulnerabilities: List[Dict], output_dir: str):
        """Generate complete test suite"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate main test file
        test_content = self._generate_main_test(vulnerabilities)
        test_path = os.path.join(output_dir, f"{self.contract_name}.t.sol")
        
        with open(test_path, 'w') as f:
            f.write(test_content)
        
        print(f"[+] Generated test file: {test_path}")
        
        # Generate exploit contracts
        for vuln in vulnerabilities:
            if vuln.get('check') in ['reentrancy', 'delegatecall']:
                exploit_content = self._generate_exploit_contract(vuln)
                exploit_path = os.path.join(output_dir, f"Exploit_{vuln['check']}.sol")
                with open(exploit_path, 'w') as f:
                    f.write(exploit_content)
                print(f"[+] Generated exploit: {exploit_path}")
    
    def _generate_main_test(self, vulnerabilities: List[Dict]) -> str:
        """Generate main test contract"""
        test_code = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {{Test}} from "forge-std/Test.sol";
import {{console}} from "forge-std/console.sol";
import {{{self.contract_name}}} from "{self.contract_path}";

/**
 * @title {self.contract_name} Security Test Suite
 * @notice Comprehensive security tests for {self.contract_name}
 * @author Volodymyr Stetsenko (Zero2Auditor)
 */
contract {self.contract_name}Test is Test {{
    {self.contract_name} public targetContract;
    
    address public attacker = address(0x1337);
    address public victim = address(0x1234);
    address public owner = address(this);
    
    function setUp() public {{
        // Deploy target contract
        targetContract = new {self.contract_name}();
        
        // Fund accounts
        vm.deal(attacker, 100 ether);
        vm.deal(victim, 100 ether);
        vm.deal(address(targetContract), 10 ether);
    }}
    
"""
        
        # Add tests for each vulnerability
        for i, vuln in enumerate(vulnerabilities, 1):
            vuln_type = vuln.get('check', 'unknown')
            template = self.templates.get(vuln_type)
            
            if template:
                test_code += f"    // Test {i}: {vuln_type}\n"
                test_code += template
                test_code += "\n\n"
        
        # Add fuzzing tests
        test_code += self._generate_fuzz_tests()
        
        # Add invariant tests
        test_code += self._generate_invariant_tests()
        
        test_code += "}\n"
        
        return test_code
    
    def _reentrancy_template(self) -> str:
        return """    function test_reentrancy_attack() public {
        // Setup: Attacker deposits funds
        vm.startPrank(attacker);
        uint256 attackerBalanceBefore = attacker.balance;
        
        // Execute reentrancy attack
        // TODO: Implement specific attack logic
        
        vm.stopPrank();
        
        // Verify: Attacker drained funds
        uint256 attackerBalanceAfter = attacker.balance;
        assertGt(attackerBalanceAfter, attackerBalanceBefore, "Reentrancy attack failed");
    }"""
    
    def _access_control_template(self) -> str:
        return """    function test_access_control_bypass() public {
        // Attempt to call privileged function as non-owner
        vm.startPrank(attacker);
        
        // TODO: Call privileged function
        // vm.expectRevert("Unauthorized");
        // targetContract.privilegedFunction();
        
        vm.stopPrank();
    }"""
    
    def _arithmetic_template(self) -> str:
        return """    function test_arithmetic_overflow() public {
        // Test integer overflow/underflow
        uint256 maxValue = type(uint256).max;
        
        // TODO: Trigger overflow condition
        // vm.expectRevert();
        // targetContract.vulnerableFunction(maxValue);
    }"""
    
    def _unchecked_call_template(self) -> str:
        return """    function test_unchecked_external_call() public {
        // Test unchecked low-level call
        vm.startPrank(attacker);
        
        // TODO: Call function with unchecked external call
        // bool success = targetContract.vulnerableCall();
        // assertFalse(success, "Call should fail");
        
        vm.stopPrank();
    }"""
    
    def _delegatecall_template(self) -> str:
        return """    function test_delegatecall_injection() public {
        // Test delegatecall to malicious contract
        vm.startPrank(attacker);
        
        // TODO: Deploy malicious contract and exploit delegatecall
        
        vm.stopPrank();
    }"""
    
    def _timestamp_template(self) -> str:
        return """    function test_timestamp_manipulation() public {
        // Test timestamp dependence
        uint256 currentTime = block.timestamp;
        
        // Warp time forward
        vm.warp(currentTime + 1 days);
        
        // TODO: Test time-dependent logic
    }"""
    
    def _tx_origin_template(self) -> str:
        return """    function test_tx_origin_vulnerability() public {
        // Test tx.origin authentication bypass
        vm.startPrank(attacker);
        
        // TODO: Exploit tx.origin check
        
        vm.stopPrank();
    }"""
    
    def _generate_fuzz_tests(self) -> str:
        return """    // Fuzz Tests
    function testFuzz_input_validation(uint256 amount) public {
        vm.assume(amount > 0 && amount < 1000 ether);
        
        // TODO: Fuzz test input validation
    }
    
    function testFuzz_state_transitions(uint8 action) public {
        vm.assume(action < 10);
        
        // TODO: Fuzz test state transitions
    }
"""
    
    def _generate_invariant_tests(self) -> str:
        return """    // Invariant Tests
    function invariant_balance_conservation() public {
        // Total balance should be conserved
        // TODO: Implement invariant check
    }
    
    function invariant_access_control() public {
        // Only authorized addresses should have privileges
        // TODO: Implement invariant check
    }
"""
    
    def _generate_exploit_contract(self, vuln: Dict) -> str:
        """Generate exploit contract for PoC"""
        vuln_type = vuln.get('check', 'unknown')
        
        if vuln_type == 'reentrancy':
            return f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {{{self.contract_name}}} from "{self.contract_path}";

/**
 * @title Reentrancy Exploit
 * @notice PoC exploit for reentrancy vulnerability
 * @author Volodymyr Stetsenko (Zero2Auditor)
 */
contract ReentrancyExploit {{
    {self.contract_name} public target;
    uint256 public attackCount;
    
    constructor({self.contract_name} _target) {{
        target = _target;
    }}
    
    receive() external payable {{
        // Reenter if target still has balance
        if (address(target).balance >= 1 ether && attackCount < 3) {{
            attackCount++;
            // target.withdraw(1 ether);  // TODO: Call vulnerable function
        }}
    }}
    
    function attack() external payable {{
        require(msg.value >= 1 ether, "Need at least 1 ETH");
        attackCount = 0;
        
        // TODO: Implement attack logic
        // target.deposit{{value: msg.value}}();
        // target.withdraw(msg.value);
        
        // Transfer stolen funds to attacker
        payable(msg.sender).transfer(address(this).balance);
    }}
}}
"""
        
        return ""


def main():
    """CLI entry point"""
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python test_generator.py <contract_name> <contract_path> <vulnerabilities_json> [output_dir]")
        sys.exit(1)
    
    contract_name = sys.argv[1]
    contract_path = sys.argv[2]
    vuln_json_path = sys.argv[3]
    output_dir = sys.argv[4] if len(sys.argv) > 4 else './test'
    
    # Load vulnerabilities
    with open(vuln_json_path, 'r') as f:
        vulnerabilities = json.load(f)
    
    # Generate tests
    generator = FoundryTestGenerator(contract_name, contract_path)
    generator.generate_test_suite(vulnerabilities, output_dir)
    
    print(f"[+] Test suite generated in {output_dir}")


if __name__ == "__main__":
    main()

