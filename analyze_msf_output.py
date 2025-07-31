#!/usr/bin/env python3
"""
Analyze MSF Console Output Patterns
===================================
This script captures and analyzes actual MSF output to understand parsing issues.
"""

import subprocess
import json
import time
import re
from typing import Dict, List

class MSFOutputAnalyzer:
    def __init__(self):
        self.samples = {}
        
    def capture_msf_command_output(self, command: str, timeout: int = 30) -> str:
        """Capture raw MSF console output for analysis"""
        print(f"📥 Capturing output for: {command}")
        
        # Use msfconsole directly to get clean output
        process = subprocess.Popen(
            ["msfconsole", "-q", "-x", f"{command}; exit"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return stdout
        except subprocess.TimeoutExpired:
            process.terminate()
            return "TIMEOUT"
            
    def analyze_search_output(self):
        """Analyze module search output patterns"""
        print("\n🔍 ANALYZING SEARCH OUTPUT")
        print("=" * 50)
        
        search_output = self.capture_msf_command_output("search ms17_010")
        print("Raw search output:")
        print("-" * 30)
        print(search_output[:500] + "..." if len(search_output) > 500 else search_output)
        print("-" * 30)
        
        # Analyze structure
        lines = search_output.split('\n')
        print(f"Total lines: {len(lines)}")
        
        for i, line in enumerate(lines[:10]):  # First 10 lines
            print(f"Line {i}: '{line.strip()}'")
            
        self.samples['search'] = search_output
        return search_output
        
    def analyze_version_output(self):
        """Analyze version command output"""
        print("\n🔍 ANALYZING VERSION OUTPUT")
        print("=" * 50)
        
        version_output = self.capture_msf_command_output("version")
        print("Raw version output:")
        print("-" * 30)
        print(version_output)
        print("-" * 30)
        
        self.samples['version'] = version_output
        return version_output
        
    def analyze_workspace_output(self):
        """Analyze workspace command output"""
        print("\n🔍 ANALYZING WORKSPACE OUTPUT")
        print("=" * 50)
        
        workspace_output = self.capture_msf_command_output("workspace")
        print("Raw workspace output:")
        print("-" * 30)
        print(workspace_output)
        print("-" * 30)
        
        self.samples['workspace'] = workspace_output
        return workspace_output
        
    def analyze_help_output(self):
        """Analyze help command output"""
        print("\n🔍 ANALYZING HELP OUTPUT")
        print("=" * 50)
        
        help_output = self.capture_msf_command_output("help")
        print("Raw help output (first 500 chars):")
        print("-" * 30)
        print(help_output[:500] + "..." if len(help_output) > 500 else help_output)
        print("-" * 30)
        
        self.samples['help'] = help_output
        return help_output
        
    def test_module_operations(self):
        """Test module operations to identify syntax issues"""
        print("\n🔍 TESTING MODULE OPERATIONS")
        print("=" * 50)
        
        # Test different module operation commands
        test_commands = [
            "use auxiliary/scanner/portscan/tcp",
            "info auxiliary/scanner/portscan/tcp", 
            "use auxiliary/scanner/portscan/tcp; info",
            "use auxiliary/scanner/portscan/tcp; show options"
        ]
        
        for cmd in test_commands:
            print(f"\nTesting: {cmd}")
            output = self.capture_msf_command_output(cmd)
            print(f"Output length: {len(output)}")
            if "error" in output.lower() or "invalid" in output.lower():
                print("❌ Error detected in output")
            else:
                print("✅ Command executed successfully")
                
            # Show first few lines
            lines = output.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"  > {line.strip()}")
                    
    def test_payload_generation(self):
        """Test payload generation to identify msfvenom issues"""
        print("\n🔍 TESTING PAYLOAD GENERATION")
        print("=" * 50)
        
        # Test different approaches
        test_commands = [
            "msfvenom -p windows/meterpreter/reverse_tcp LHOST=127.0.0.1 LPORT=4444 -f raw",
            "generate -p windows/meterpreter/reverse_tcp LHOST=127.0.0.1 LPORT=4444",
            "!msfvenom -p windows/meterpreter/reverse_tcp LHOST=127.0.0.1 LPORT=4444 -f raw"
        ]
        
        for cmd in test_commands:
            print(f"\nTesting: {cmd}")
            output = self.capture_msf_command_output(cmd)
            print(f"Output length: {len(output)}")
            
            if "not found" in output.lower() or "command not found" in output.lower():
                print("❌ Command not recognized")
            elif "error" in output.lower():
                print("⚠️ Error in execution")
            else:
                print("✅ Command executed")
                
            # Show relevant lines
            lines = output.split('\n')[:3]
            for line in lines:
                if line.strip():
                    print(f"  > {line.strip()}")
                    
    def identify_parsing_patterns(self):
        """Identify common patterns in MSF output for better parsing"""
        print("\n🔍 IDENTIFYING PARSING PATTERNS")
        print("=" * 50)
        
        patterns = {
            "table_separator": r"={3,}",
            "table_header": r"^\s*[A-Za-z]+\s+[A-Za-z]+",
            "module_line": r"^\s*\S+/\S+/\S+",
            "error_indicator": r"error|invalid|not found|failed",
            "success_indicator": r"successful|complete|done"
        }
        
        for name, pattern in patterns.items():
            print(f"\nPattern: {name} -> {pattern}")
            
            # Test against captured samples
            for sample_name, sample_text in self.samples.items():
                matches = re.findall(pattern, sample_text, re.IGNORECASE | re.MULTILINE)
                print(f"  {sample_name}: {len(matches)} matches")
                if matches:
                    print(f"    Examples: {matches[:3]}")
                    
    def generate_parsing_recommendations(self):
        """Generate recommendations for improved parsing"""
        print("\n📋 PARSING RECOMMENDATIONS")
        print("=" * 50)
        
        recommendations = [
            "1. Use regex patterns to identify table structures",
            "2. Implement dynamic header detection for tables",
            "3. Add error pattern detection before parsing",
            "4. Use column-based parsing for tabular data",
            "5. Implement fallback to raw output when parsing fails",
            "6. Add output type detection (table, list, single value, error)",
            "7. Use MSF-specific markers for section identification"
        ]
        
        for rec in recommendations:
            print(rec)
            
        return recommendations
        
    def save_analysis_results(self):
        """Save analysis results to files"""
        print("\n💾 SAVING ANALYSIS RESULTS")
        print("=" * 50)
        
        # Save raw samples
        with open('msf_output_samples.json', 'w') as f:
            json.dump(self.samples, f, indent=2)
        print("✅ Raw samples saved to msf_output_samples.json")
        
        # Create analysis report
        report = {
            "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "samples_captured": len(self.samples),
            "key_findings": [
                "MSF output varies significantly between commands",
                "Table format is inconsistent",
                "Error detection needed before parsing",
                "Module commands may need different syntax"
            ],
            "recommended_improvements": self.generate_parsing_recommendations()
        }
        
        with open('msf_parsing_analysis.json', 'w') as f:
            json.dump(report, f, indent=2)
        print("✅ Analysis report saved to msf_parsing_analysis.json")

def main():
    print("🔬 MSF Console Output Analysis Tool")
    print("=" * 60)
    
    analyzer = MSFOutputAnalyzer()
    
    try:
        # Capture and analyze different output types
        analyzer.analyze_version_output()
        analyzer.analyze_workspace_output()
        analyzer.analyze_search_output()
        analyzer.analyze_help_output()
        
        # Test problematic operations
        analyzer.test_module_operations()
        analyzer.test_payload_generation()
        
        # Identify patterns and generate recommendations
        analyzer.identify_parsing_patterns()
        analyzer.generate_parsing_recommendations()
        
        # Save results
        analyzer.save_analysis_results()
        
        print("\n🎉 Analysis complete! Check generated files for detailed results.")
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())