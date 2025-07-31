#!/usr/bin/env python3
"""Test current parsing with simulated MSF output"""

import json
from typing import Dict, List

# Simulate actual MSF console output patterns
SAMPLE_OUTPUTS = {
    "search_ms17_010": """Matching Modules
================

   #  Name                                      Disclosure Date  Rank   Check  Description
   -  ----                                      ---------------  ----   -----  -----------
   0  auxiliary/admin/smb/ms17_010_command      2017-03-14       normal  No     MS17-010 EternalRomance/EternalSynergy/EternalChampion SMB Remote Windows Command Execution
   1  auxiliary/scanner/smb/smb_ms17_010        2017-03-14       normal  No     MS17-010 SMB RCE Detection
   2  exploit/windows/smb/ms17_010_eternalblue  2017-03-14       average  Yes    MS17-010 EternalBlue SMB Remote Windows Kernel Pool Corruption
   3  exploit/windows/smb/ms17_010_psexec       2017-03-14       normal  Yes    MS17-010 EternalRomance/EternalSynergy/EternalChampion SMB Remote Windows Code Execution

Interact with a module by name or index. For example info 3, use 3 or use exploit/windows/smb/ms17_010_psexec""",

    "workspace_list": """Workspaces
==========

* default
  test_workspace
  client_engagement""",

    "version_info": """Framework: 6.4.55-dev
Console  : 6.4.55-dev
Ruby     : ruby 3.0.4p208 (2022-04-12 revision 3fa771dded) [x86_64-linux-gnu]""",

    "hosts_empty": """hosts
=====

address  mac  name  os_name  os_flavor  os_sp  purpose  info  comments
-------  ---  ----  -------  ---------  -----  -------  ----  --------""",

    "module_info": """
       Name: TCP Port Scanner
     Module: auxiliary/scanner/portscan/tcp
    License: Metasploit Framework License (BSD)
       Rank: Normal
  Disclosed: 2003-10-06

Provided by:
  hdm <x@hdm.io>

Available targets:
  Id  Name
  --  ----
  0   Automatic

Check supported:
  No

Basic options:
  Name         Current Setting  Required  Description
  ----         ---------------  --------  -----------
  CONCURRENCY  10               yes       The number of concurrent ports to check per host
  DELAY        0                yes       The delay between connections, per thread, in milliseconds
  JITTER       0                yes       The delay jitter factor (maximum value by which to +/- DELAY)
  PORTS        1-10000          yes       Ports to scan (e.g. 22-25,80,110-900)
  RHOSTS                        yes       The target host(s), see https://docs.metasploit.com/docs/using-metasploit/basics/using-metasploit.html
  THREADS      1                yes       The number of concurrent threads (max one per host)
  TIMEOUT      1000             yes       Socket timeout for port checks

Description:
  Enumerate open TCP services by performing a full TCP connect on 
  each port. This does not need administrative privileges on the 
  source machine, which may be useful if pivoting.""",

    "error_output": """[-] Unknown command: invalid_command
[-] Use the 'help' command for more information""",

    "msfvenom_not_found": """[-] Unknown command: msfvenom
[-] Use the 'help' command for more information""",
}

# Current parsing functions from the MCP code
def _parse_search_results(output: str) -> List[Dict[str, str]]:
    """Parse module search results."""
    modules = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or '===' in line or 'Matching Modules' in line:
            continue
        
        # Skip header lines and separators
        if line.startswith('Name') or line.startswith('----') or line.startswith('='):
            continue
            
        # Try to parse module line - typical format:
        # module_name    disclosure_date    rank    description
        parts = line.split(None, 3)  # Split into max 4 parts
        if len(parts) >= 1:
            modules.append({
                "name": parts[0],
                "disclosure_date": parts[1] if len(parts) > 1 else "",
                "rank": parts[2] if len(parts) > 2 else "",
                "description": parts[3] if len(parts) > 3 else ""
            })
    
    return modules

def _parse_workspace_list(output: str) -> List[Dict[str, str]]:
    """Parse workspace list output."""
    workspaces = []
    lines = output.split('\n')
    
    for line in lines:
        line = line.strip()
        # Skip empty lines and headers
        if not line or line == 'Workspaces' or line.startswith('='):
            continue
            
        # Current workspace is marked with *
        current = line.startswith('*')
        name = line.lstrip('* ').strip()
        if name:
            workspaces.append({
                "name": name,
                "current": current
            })
    
    return workspaces

def test_current_parsing():
    """Test current parsing functions with real MSF output"""
    print("🧪 Testing Current Parsing Functions")
    print("=" * 50)
    
    # Test search parsing
    print("\n1. SEARCH RESULTS PARSING")
    print("-" * 30)
    search_results = _parse_search_results(SAMPLE_OUTPUTS["search_ms17_010"])
    print(f"Parsed {len(search_results)} modules:")
    for i, module in enumerate(search_results[:3]):  # Show first 3
        print(f"  {i+1}. {json.dumps(module, indent=4)}")
    
    print(f"\n❌ ISSUES IDENTIFIED:")
    print(f"  - Module format is actually: # name date rank check description")
    print(f"  - Current parsing misses the # and check columns")
    print(f"  - Description field is cut off")
    
    # Test workspace parsing  
    print("\n2. WORKSPACE LIST PARSING")
    print("-" * 30)
    workspace_results = _parse_workspace_list(SAMPLE_OUTPUTS["workspace_list"])
    print(f"Parsed {len(workspace_results)} workspaces:")
    for workspace in workspace_results:
        print(f"  - {json.dumps(workspace, indent=4)}")
    
    print(f"\n✅ Workspace parsing looks correct")
    
    # Analyze version output
    print("\n3. VERSION OUTPUT ANALYSIS")
    print("-" * 30)
    version_output = SAMPLE_OUTPUTS["version_info"]
    print("Raw version output:")
    print(version_output)
    print("\n❌ ISSUES:")
    print("  - No structured parsing for version info")
    print("  - Should extract framework, console, ruby versions separately")
    
    # Analyze module info
    print("\n4. MODULE INFO ANALYSIS")  
    print("-" * 30)
    module_info = SAMPLE_OUTPUTS["module_info"]
    print("Module info structure:")
    lines = module_info.split('\n')[:10]
    for line in lines:
        if line.strip():
            print(f"  '{line.strip()}'")
    
    print(f"\n❌ ISSUES:")
    print("  - Complex multi-section format")
    print("  - No parser for module info structure")
    print("  - Options table needs separate parsing")
    
    return {
        "search_results": search_results,
        "workspace_results": workspace_results,
        "analysis_complete": True
    }

def identify_root_causes():
    """Identify root causes of parsing issues"""
    print("\n🔍 ROOT CAUSE ANALYSIS")
    print("=" * 50)
    
    root_causes = {
        "1_incorrect_assumptions": [
            "Search results format assumed 4 columns, actually has 6",
            "Module info assumed simple structure, actually multi-section",
            "Command output assumed consistent, varies by command type"
        ],
        "2_missing_parsers": [
            "No parser for module info sections",
            "No parser for tabular options data", 
            "No parser for version information structure",
            "No error detection before parsing"
        ],
        "3_rigid_parsing": [
            "Fixed column assumptions break with varying data",
            "No fallback when parsing fails",
            "No output type detection (table vs list vs info)"
        ],
        "4_command_issues": [
            "Module operations using wrong syntax",
            "msfvenom not available in msfconsole context",
            "Commands need MSF-specific formatting"
        ]
    }
    
    for category, issues in root_causes.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        for issue in issues:
            print(f"  ❌ {issue}")
    
    return root_causes

def design_improved_parsing_system():
    """Design improved parsing system architecture"""
    print("\n🏗️ IMPROVED PARSING SYSTEM DESIGN")
    print("=" * 50)
    
    design = {
        "1_output_type_detection": {
            "description": "Detect output type before parsing",
            "types": ["table", "list", "info_block", "error", "raw"],
            "implementation": "Regex patterns + heuristics"
        },
        "2_flexible_table_parser": {
            "description": "Dynamic column detection and parsing",
            "features": ["Auto-detect headers", "Variable columns", "Handle separators"],
            "fallback": "Raw output if parsing fails"
        },
        "3_section_based_parser": {
            "description": "Parse multi-section outputs like module info",
            "sections": ["metadata", "options", "targets", "description"],
            "approach": "State machine or regex sections"
        },
        "4_error_handling": {
            "description": "Detect and handle errors gracefully",
            "patterns": ["[-] Unknown command", "error", "failed"],
            "response": "Return structured error info"
        }
    }
    
    for component, details in design.items():
        print(f"\n{component.replace('_', ' ').title()}:")
        print(f"  📝 {details['description']}")
        if 'features' in details:
            for feature in details['features']:
                print(f"    ✓ {feature}")
    
    return design

def main():
    print("🔬 MSF MCP Parsing Analysis")
    print("=" * 60)
    
    # Test current implementation
    results = test_current_parsing()
    
    # Identify problems
    root_causes = identify_root_causes()
    
    # Design solution
    design = design_improved_parsing_system()
    
    # Save analysis
    analysis_report = {
        "current_results": results,
        "root_causes": root_causes, 
        "improved_design": design,
        "next_steps": [
            "Implement output type detection",
            "Create flexible table parser",
            "Add section-based parsing for module info",
            "Fix module operations command syntax",
            "Replace msfvenom with MSF console equivalents"
        ]
    }
    
    with open('parsing_analysis_report.json', 'w') as f:
        json.dump(analysis_report, f, indent=2)
    
    print(f"\n📄 Analysis saved to parsing_analysis_report.json")
    print(f"🎯 Ready to implement improved parsing system!")

if __name__ == "__main__":
    main()