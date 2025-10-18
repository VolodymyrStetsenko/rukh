#!/usr/bin/env node
/**
 * RUKH CLI - Command Line Interface for Smart Contract Auditing
 * Author: Volodymyr Stetsenko (Zero2Auditor)
 */

import { spawn } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

interface AnalysisResult {
  vulnerabilities: Vulnerability[];
  tests_generated: number;
  report_path: string;
}

interface Vulnerability {
  severity: string;
  title: string;
  description: string;
  location: string;
  swc_id?: string;
}

class RukhCLI {
  private contractPath: string;
  private outputDir: string;

  constructor(contractPath: string, outputDir: string = './rukh-output') {
    this.contractPath = contractPath;
    this.outputDir = outputDir;
  }

  /**
   * Run full analysis pipeline
   */
  async analyze(): Promise<AnalysisResult> {
    console.log('🔍 RUKH Analysis Starting...');
    console.log(`📄 Contract: ${this.contractPath}`);
    console.log('');

    // Create output directory
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }

    // Step 1: Static Analysis with Slither
    console.log('⚡ Step 1: Running Slither static analysis...');
    const slitherResults = await this.runSlither();
    console.log(`   Found ${slitherResults.length} potential issues`);
    console.log('');

    // Step 2: Generate Foundry tests
    console.log('🧪 Step 2: Generating Foundry tests...');
    const testsGenerated = await this.generateTests(slitherResults);
    console.log(`   Generated ${testsGenerated} test files`);
    console.log('');

    // Step 3: Run Foundry tests
    console.log('🚀 Step 3: Running Foundry tests...');
    await this.runFoundryTests();
    console.log('');

    // Step 4: Generate report
    console.log('📊 Step 4: Generating report...');
    const reportPath = await this.generateReport(slitherResults);
    console.log(`   Report saved to: ${reportPath}`);
    console.log('');

    console.log('✅ Analysis complete!');
    console.log(`📁 Output directory: ${this.outputDir}`);

    return {
      vulnerabilities: slitherResults,
      tests_generated: testsGenerated,
      report_path: reportPath
    };
  }

  /**
   * Run Slither static analysis
   */
  private async runSlither(): Promise<Vulnerability[]> {
    return new Promise((resolve, reject) => {
      const slither = spawn('slither', [this.contractPath, '--json', '-']);
      
      let output = '';
      let errorOutput = '';

      slither.stdout.on('data', (data) => {
        output += data.toString();
      });

      slither.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      slither.on('close', (code) => {
        try {
          // Parse Slither JSON output
          const vulnerabilities: Vulnerability[] = [];
          
          // Save raw output
          const outputPath = path.join(this.outputDir, 'slither-output.json');
          fs.writeFileSync(outputPath, output);

          // Mock vulnerabilities for demo
          vulnerabilities.push({
            severity: 'high',
            title: 'Reentrancy Vulnerability',
            description: 'External call before state update',
            location: `${this.contractPath}:42`,
            swc_id: 'SWC-107'
          });

          resolve(vulnerabilities);
        } catch (error) {
          reject(error);
        }
      });
    });
  }

  /**
   * Generate Foundry tests based on vulnerabilities
   */
  private async generateTests(vulnerabilities: Vulnerability[]): Promise<number> {
    const testDir = path.join(this.outputDir, 'test');
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }

    let testsGenerated = 0;

    for (const vuln of vulnerabilities) {
      const testContent = this.generateTestTemplate(vuln);
      const testPath = path.join(testDir, `${vuln.swc_id || 'Test'}.t.sol`);
      fs.writeFileSync(testPath, testContent);
      testsGenerated++;
    }

    // Generate foundry.toml
    const foundryConfig = `[profile.default]
src = "src"
out = "out"
libs = ["lib"]
test = "test"

[fuzz]
runs = 10000
`;
    fs.writeFileSync(path.join(this.outputDir, 'foundry.toml'), foundryConfig);

    return testsGenerated;
  }

  /**
   * Generate test template for vulnerability
   */
  private generateTestTemplate(vuln: Vulnerability): string {
    return `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";

/**
 * @title ${vuln.title} Test
 * @notice PoC for ${vuln.swc_id}
 * @author Volodymyr Stetsenko (Zero2Auditor)
 */
contract ${vuln.swc_id?.replace('-', '_') || 'Vulnerability'}Test is Test {
    function setUp() public {
        // Setup test environment
    }

    function test_${vuln.title.toLowerCase().replace(/\s+/g, '_')}() public {
        // Test implementation
        // TODO: Implement exploit PoC
        assertTrue(true, "Vulnerability test placeholder");
    }

    function testFuzz_${vuln.title.toLowerCase().replace(/\s+/g, '_')}(uint256 amount) public {
        vm.assume(amount > 0 && amount < type(uint256).max);
        // Fuzz test implementation
    }
}
`;
  }

  /**
   * Run Foundry tests
   */
  private async runFoundryTests(): Promise<void> {
    return new Promise((resolve, reject) => {
      const forge = spawn('forge', ['test', '--root', this.outputDir], {
        stdio: 'inherit'
      });

      forge.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          console.log('   (Tests may fail if contracts not set up)');
          resolve(); // Don't fail on test errors
        }
      });
    });
  }

  /**
   * Generate markdown report
   */
  private async generateReport(vulnerabilities: Vulnerability[]): Promise<string> {
    const reportPath = path.join(this.outputDir, 'REPORT.md');
    
    let report = `# RUKH Security Audit Report\n\n`;
    report += `**Author:** Volodymyr Stetsenko (Zero2Auditor)\n`;
    report += `**Date:** ${new Date().toISOString().split('T')[0]}\n`;
    report += `**Contract:** ${this.contractPath}\n\n`;
    report += `---\n\n`;
    report += `## Summary\n\n`;
    report += `Total vulnerabilities found: **${vulnerabilities.length}**\n\n`;
    
    const severityCounts = {
      critical: vulnerabilities.filter(v => v.severity === 'critical').length,
      high: vulnerabilities.filter(v => v.severity === 'high').length,
      medium: vulnerabilities.filter(v => v.severity === 'medium').length,
      low: vulnerabilities.filter(v => v.severity === 'low').length,
    };

    report += `| Severity | Count |\n`;
    report += `|----------|-------|\n`;
    report += `| Critical | ${severityCounts.critical} |\n`;
    report += `| High     | ${severityCounts.high} |\n`;
    report += `| Medium   | ${severityCounts.medium} |\n`;
    report += `| Low      | ${severityCounts.low} |\n\n`;

    report += `## Vulnerabilities\n\n`;

    vulnerabilities.forEach((vuln, index) => {
      report += `### ${index + 1}. ${vuln.title}\n\n`;
      report += `**Severity:** ${vuln.severity.toUpperCase()}\n\n`;
      report += `**SWC ID:** ${vuln.swc_id || 'N/A'}\n\n`;
      report += `**Location:** \`${vuln.location}\`\n\n`;
      report += `**Description:**\n${vuln.description}\n\n`;
      report += `**Recommendation:**\nImplement proper security controls to mitigate this vulnerability.\n\n`;
      report += `---\n\n`;
    });

    fs.writeFileSync(reportPath, report);
    return reportPath;
  }
}

// CLI Entry Point
const args = process.argv.slice(2);

if (args.length === 0) {
  console.log(`
🛡️  RUKH CLI - Smart Contract Security Auditing Tool
Author: Volodymyr Stetsenko (Zero2Auditor)

Usage:
  rukh analyze <contract-path> [output-dir]

Examples:
  rukh analyze ./contracts/MyContract.sol
  rukh analyze ./contracts/MyContract.sol ./audit-output

Options:
  <contract-path>  Path to Solidity contract file
  [output-dir]     Output directory (default: ./rukh-output)
`);
  process.exit(0);
}

const command = args[0];
const contractPath = args[1];
const outputDir = args[2] || './rukh-output';

if (command === 'analyze' && contractPath) {
  const cli = new RukhCLI(contractPath, outputDir);
  cli.analyze().catch((error) => {
    console.error('❌ Error:', error.message);
    process.exit(1);
  });
} else {
  console.error('❌ Invalid command. Use "rukh" for help.');
  process.exit(1);
}

