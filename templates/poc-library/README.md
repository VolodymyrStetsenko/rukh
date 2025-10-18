# RUKH PoC Library

**Author:** Volodymyr Stetsenko (Zero2Auditor)

## Overview

This library contains production-ready Proof of Concept (PoC) templates for common smart contract vulnerabilities. Each template is designed to be adapted for specific CTF challenges, Code4rena audits, and bug bounty programs.

## Vulnerability Categories

### 1. Reentrancy Attacks
- **Location:** `reentrancy/ReentrancyPoC.sol`
- **Patterns:**
  - Single-function reentrancy
  - Cross-function reentrancy
  - Cross-contract reentrancy
  - Read-only reentrancy
- **Use Cases:** Classic reentrancy exploits, ERC777 hooks, callback vulnerabilities

### 2. Flash Loan Attacks
- **Location:** `flash-loan/FlashLoanPoC.sol`
- **Attack Vectors:**
  - Price manipulation
  - Governance attacks
  - Liquidation manipulation
  - Arbitrage exploitation
- **Use Cases:** DeFi protocol exploits, oracle manipulation, governance takeover

### 3. Access Control Vulnerabilities
- **Location:** `access-control/AccessControlPoC.sol`
- **Patterns:**
  - Missing access control
  - Broken access control
  - Privilege escalation
  - tx.origin authentication
- **Use Cases:** Unauthorized function calls, privilege bypass

### 4. Arithmetic Vulnerabilities
- **Location:** `arithmetic/ArithmeticPoC.sol`
- **Patterns:**
  - Integer overflow/underflow
  - Precision loss
  - Rounding errors
- **Use Cases:** Token manipulation, reward calculation exploits

### 5. Price Manipulation
- **Location:** `price-manipulation/PriceManipulationPoC.sol`
- **Attack Vectors:**
  - Oracle manipulation
  - AMM price manipulation
  - Sandwich attacks
  - Front-running
- **Use Cases:** DeFi exploits, MEV attacks

### 6. Delegatecall Vulnerabilities
- **Location:** `delegatecall/DelegatecallPoC.sol`
- **Patterns:**
  - Storage collision
  - Selfdestruct via delegatecall
  - Unprotected delegatecall
- **Use Cases:** Proxy exploits, storage manipulation

## Usage

### Quick Start

1. **Identify Vulnerability Type**
   ```bash
   # Run Slither to identify vulnerabilities
   slither target_contract.sol
   ```

2. **Select Appropriate Template**
   ```bash
   cp templates/poc-library/reentrancy/ReentrancyPoC.sol test/
   ```

3. **Adapt Template**
   - Replace interface with target contract
   - Implement attack logic
   - Add specific exploit steps

4. **Test Exploit**
   ```bash
   forge test --match-contract ReentrancyPoC -vvvv
   ```

### CTF Workflow

```bash
# 1. Analyze contract
rukh analyze challenge.sol

# 2. Generate initial tests
python integrations/foundry/test_generator.py Challenge challenge.sol vulnerabilities.json

# 3. Adapt PoC template
cp templates/poc-library/reentrancy/ReentrancyPoC.sol test/ChallengeExploit.t.sol

# 4. Run exploit
forge test --match-contract ChallengeExploit -vvvv
```

### Code4rena Workflow

```bash
# 1. Clone audit repository
git clone https://github.com/code-423n4/audit-repo

# 2. Run comprehensive analysis
rukh analyze src/

# 3. Generate PoC for each vulnerability
for vuln in vulnerabilities/*.json; do
    python integrations/foundry/test_generator.py Contract src/Contract.sol $vuln
done

# 4. Submit findings with PoC
```

## Template Structure

Each PoC template follows this structure:

```solidity
// 1. Interfaces
interface IVulnerableContract { ... }

// 2. Attacker Contract
contract Attacker {
    // Attack logic
    function attack() external { ... }
}

// 3. Test Suite
contract PoCTest is Test {
    // Setup
    function setUp() public { ... }
    
    // Exploit test
    function test_exploit() public { ... }
}

// 4. Advanced Patterns
contract AdvancedAttacker {
    // Complex attack scenarios
}
```

## Customization Guide

### Step 1: Update Interfaces
```solidity
// Replace with actual target contract interface
interface IVulnerableContract {
    function vulnerableFunction() external;
}
```

### Step 2: Implement Attack Logic
```solidity
function attack() external payable {
    // 1. Setup attack conditions
    // 2. Trigger vulnerability
    // 3. Extract profits
}
```

### Step 3: Add Assertions
```solidity
function test_exploit() public {
    // Execute attack
    attacker.attack();
    
    // Verify success
    assertGt(profit, 0, "Attack failed");
}
```

## Best Practices

1. **Always Test Locally First**
   - Use Foundry's forking feature
   - Test against mainnet forks
   - Verify exploit works before submission

2. **Document Your Findings**
   - Add comments explaining attack steps
   - Include severity assessment
   - Provide remediation recommendations

3. **Responsible Disclosure**
   - Report vulnerabilities to project teams
   - Follow responsible disclosure timelines
   - Never exploit on mainnet without permission

4. **Continuous Learning**
   - Study past exploits
   - Analyze Code4rena reports
   - Stay updated on new attack vectors

## Advanced Techniques

### Combining Multiple Vulnerabilities
```solidity
// Example: Reentrancy + Flash Loan
function complexAttack() external {
    // 1. Take flash loan
    // 2. Use funds for reentrancy attack
    // 3. Repay flash loan with profits
}
```

### Multi-Step Exploits
```solidity
// Example: Setup -> Exploit -> Cleanup
function multiStepAttack() external {
    step1_setup();
    step2_exploit();
    step3_cleanup();
}
```

## Resources

- **Foundry Book:** https://book.getfoundry.sh/
- **Slither Documentation:** https://github.com/crytic/slither
- **SWC Registry:** https://swcregistry.io/
- **Code4rena:** https://code4rena.com/
- **Immunefi:** https://immunefi.com/

## Contributing

To add new PoC templates:

1. Create new directory under `poc-library/`
2. Add template contract with comprehensive comments
3. Include test suite
4. Update this README

## License

MIT License - See LICENSE file for details

---

**Disclaimer:** These templates are for educational and authorized security testing only. Never use these techniques on contracts without explicit permission.

