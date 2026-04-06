#!/usr/bin/env python3
"""
NEXUS SHADOW SIGHT  Ultimate OSINT Engine
Dynamically loads and coordinates all specialized OSINT modules.
"""

import os
import sys
import json
import importlib
import importlib.util
from pathlib import Path
from datetime import datetime

class ShadowSightCLI:
    def __init__(self):
        self.src_dir = Path(__file__).parent
        self.modules = {}
        if str(self.src_dir) not in sys.path:
            sys.path.insert(0, str(self.src_dir))
        self._load_modules()

    def _load_modules(self):
        for py_file in self.src_dir.glob("*.py"):
            if py_file.name == "shadow_cli.py" or py_file.name == "__init__.py":
                continue
            
            mod_name = py_file.stem
            try:
                spec = importlib.util.spec_from_file_location(mod_name, py_file)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                if hasattr(mod, "run"):
                    doc = mod.__doc__ or "No description provided."
                    # Get the first meaningful line of the docstring
                    doc_lines = [line.strip() for line in doc.split("\n") if line.strip()]
                    title = doc_lines[0] if doc_lines else mod_name.replace("_", " ").title()
                    
                    self.modules[mod_name] = {
                        "module": mod,
                        "title": title
                    }
            except Exception as e:
                print(f"  [!] Failed to load plugin '{mod_name}': {e}")

    def banner(self):
        print("\n" + "=" * 60)
        print("  SHADOW SIGHT OSINT ENGINE V5.0 (Golden Edition)")
        print(f"  Active Intelligence Plugins: {len(self.modules)}")
        print("=" * 60 + "\n")

    def list_modules(self):
        print("[*] Loaded Modules:")
        for name, info in self.modules.items():
            print(f"  --> {info['title']} [{name}.py]")
        print()

    def execute_all(self, target: str):
        print(f"[*] Initiating Full-Spectrum Recon on: {target}")
        results = {}
        
        for name, info in self.modules.items():
            print(f"\n[>] Running: {info['title']} ...")
            try:
                mod_run = getattr(info['module'], "run")
                res = mod_run(target)
                results[name] = res
                print(f"    [+] Successfully gathered intel.")
            except Exception as e:
                print(f"    [!] Error during execution: {e}")
                results[name] = {"error": str(e)}
                
        try:
            logs_dir = self.src_dir.parent / "logs"
            logs_dir.mkdir(exist_ok=True, parents=True)
            report_path = logs_dir / f"report_{target.replace('.', '_')}_{int(datetime.now().timestamp())}.json"
            report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            
            print("\n" + "=" * 60)
            print(f"[*] RECON COMPLETE. Full report saved to: {report_path.name}")
            print("=" * 60 + "\n")
        except Exception as e:
            print("\n" + "=" * 60)
            print(f"[!] RECON COMPLETE, but failed to save report: {e}")
            print("=" * 60 + "\n")

if __name__ == "__main__":
    cli = ShadowSightCLI()
    cli.banner()
    
    if len(sys.argv) < 2:
        print("Usage: python shadow_cli.py <target_domain_or_ip_or_email>")
        print("Example: python shadow_cli.py example.com")
        sys.exit(1)
        
    cli.list_modules()
    target = sys.argv[1]
    cli.execute_all(target)
