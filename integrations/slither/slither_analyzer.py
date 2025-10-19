"""
RUKH Slither Integration
Wrapper for Slither static analysis tool
Author: Volodymyr Stetsenko (Zero2Auditor)
"""

import json
import os
import subprocess
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Vulnerability:
    """Vulnerability data structure"""
    check: str
    impact: str
    confidence: str
    description: str
    elements: List[Dict]
    markdown: str
    first_markdown_element: str
    id: str


class SlitherAnalyzer:
    """Slither static analysis wrapper"""
    
    def __init__(self, contract_path: str):
        self.contract_path = contract_path
        self.results: List[Vulnerability] = []
    
    def analyze(self) -> List[Vulnerability]:
        """Run Slither analysis"""
        print(f"[*] Running Slither on {self.contract_path}...")
        
        try:
            # Run Slither with JSON output
            result = subprocess.run(
                ['slither', self.contract_path, '--json', '-'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse JSON output
            if result.stdout:
                data = json.loads(result.stdout)
                self.results = self._parse_results(data)
            
            print(f"[+] Found {len(self.results)} issues")
            return self.results
            
        except subprocess.TimeoutExpired:
            print("[!] Slither analysis timed out")
            return []
        except json.JSONDecodeError as e:
            print(f"[!] Failed to parse Slither output: {e}")
            return []
        except Exception as e:
            print(f"[!] Error running Slither: {e}")
            return []
    
    def _parse_results(self, data: Dict) -> List[Vulnerability]:
        """Parse Slither JSON output"""
        vulnerabilities = []
        
        if 'results' in data and 'detectors' in data['results']:
            for detector in data['results']['detectors']:
                vuln = Vulnerability(
                    check=detector.get('check', 'unknown'),
                    impact=detector.get('impact', 'unknown'),
                    confidence=detector.get('confidence', 'unknown'),
                    description=detector.get('description', ''),
                    elements=detector.get('elements', []),
                    markdown=detector.get('markdown', ''),
                    first_markdown_element=detector.get('first_markdown_element', ''),
                    id=detector.get('id', '')
                )
                vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def get_high_severity(self) -> List[Vulnerability]:
        """Get high and critical severity issues"""
        return [v for v in self.results if v.impact in ['High', 'Critical']]
    
    def get_by_check(self, check_name: str) -> List[Vulnerability]:
        """Get vulnerabilities by check name"""
        return [v for v in self.results if v.check == check_name]
    
    def export_json(self, output_path: str):
        """Export results to JSON"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump([asdict(v) for v in self.results], f, indent=2)
        print(f"[+] Results exported to {output_path}")
    
    def export_markdown(self, output_path: str):
        """Export results to Markdown"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("# Slither Analysis Report\n\n")
            f.write(f"**Contract:** {self.contract_path}\n\n")
            f.write(f"**Total Issues:** {len(self.results)}\n\n")
            
            # Group by severity
            critical = [v for v in self.results if v.impact == 'Critical']
            high = [v for v in self.results if v.impact == 'High']
            medium = [v for v in self.results if v.impact == 'Medium']
            low = [v for v in self.results if v.impact == 'Low']
            
            f.write("## Summary\n\n")
            f.write(f"- Critical: {len(critical)}\n")
            f.write(f"- High: {len(high)}\n")
            f.write(f"- Medium: {len(medium)}\n")
            f.write(f"- Low: {len(low)}\n\n")
            
            # Write details
            for severity, issues in [('Critical', critical), ('High', high), 
                                     ('Medium', medium), ('Low', low)]:
                if issues:
                    f.write(f"## {severity} Severity Issues\n\n")
                    for i, vuln in enumerate(issues, 1):
                        f.write(f"### {i}. {vuln.check}\n\n")
                        f.write(f"**Confidence:** {vuln.confidence}\n\n")
                        f.write(f"**Description:**\n{vuln.description}\n\n")
                        if vuln.markdown:
                            f.write(f"**Details:**\n{vuln.markdown}\n\n")
                        f.write("---\n\n")
        
        print(f"[+] Markdown report exported to {output_path}")


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python slither_analyzer.py <contract_path> [output_dir]")
        sys.exit(1)
    
    contract_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    analyzer = SlitherAnalyzer(contract_path)
    vulnerabilities = analyzer.analyze()
    
    if vulnerabilities:
        # Export results
        analyzer.export_json(f"{output_dir}/slither-results.json")
        analyzer.export_markdown(f"{output_dir}/slither-report.md")
        
        # Print summary
        print("\n[*] High/Critical Issues:")
        for vuln in analyzer.get_high_severity():
            print(f"  - [{vuln.impact}] {vuln.check}: {vuln.description[:80]}...")
    else:
        print("[+] No vulnerabilities found!")


if __name__ == "__main__":
    main()

