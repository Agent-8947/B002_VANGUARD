#!/usr/bin/env python3
"""
NEXUS VANGUARD  Mission-Critical OSINT Engine
Orchestrates parallel execution of intelligence modules with safety guardrails.
"""

import os, sys, json, importlib.util, argparse, time, socket
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

DISCLAIMER = """[!] ETHICAL USE WARNING: This software is for authorized security research and 
    professional intelligence gathering only. Unauthorized usage may be illegal."""

class ShadowSightCLI:
    def __init__(self):
        self.src_dir = Path(__file__).parent
        self.root_dir = self.src_dir.parent
        self.modules = {}
        if str(self.src_dir) not in sys.path:
            sys.path.insert(0, str(self.src_dir))
        self._load_modules()

    def _load_modules(self):
        for py_file in self.src_dir.glob("*.py"):
            if py_file.name in ["shadow_cli.py", "__init__.py"]: continue
            mod_name = py_file.stem
            try:
                spec = importlib.util.spec_from_file_location(mod_name, py_file)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "run"):
                    doc = mod.__doc__ or mod_name.replace("_", " ").title()
                    title = doc.split("\n")[0].strip()
                    self.modules[mod_name] = {"module": mod, "title": title}
            except Exception as e:
                print(f"  [!] Failed to load plugin '{mod_name}': {e}")

    def banner(self):
        print("\n" + "█" * 65)
        print("  NEXUS VANGUARD OSINT ORCHESTRATOR V5.0 (Golden Edition)")
        print(f"  Active Plugins: {len(self.modules)} | Mode: Production / Parallel ")
        print("█" * 65)
        print(DISCLAIMER)
        print("█" * 65 + "\n")

    def _validate_target(self, target: str):
        if not target or len(target) < 3: return False
        # Block private IP ranges (basic safety)
        private_patterns = ["127.0.0.1", "192.168.", "10.0.", "172.16."]
        if any(p in target for p in private_patterns):
            print(f"  [!] REJECTED: Target '{target}' is in a private network range.")
            return False
        return True

    def execute(self, target: str, specific_mod=None, output_format="text"):
        if not self._validate_target(target): return
        
        target_mods = {specific_mod: self.modules[specific_mod]} if specific_mod else self.modules
        print(f"[*] Starting Intelligence Extraction on: {target}")
        print(f"[*] Task Queue: {len(target_mods)} modules.")
        
        results = {}
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=min(len(target_mods), 10)) as executor:
            future_to_mod = {executor.submit(info['module'].run, target): name 
                             for name, info in target_mods.items()}
            
            completed = 0
            # Wait with global 60s timeout
            done, not_done = wait(future_to_mod.keys(), timeout=65, return_when=ALL_COMPLETED)
            
            for future in done:
                mod_name = future_to_mod[future]
                completed += 1
                print(f"  [{completed}/{len(target_mods)}] {self.modules[mod_name]['title']} -> DONE")
                try: results[mod_name] = future.result()
                except Exception as e: results[mod_name] = {"error": str(e)}
            
            for future in not_done:
                print(f"  [!] TIMEOUT: {future_to_mod[future]} failed to finish in time.")
                results[future_to_mod[future]] = {"error": "Module execution timeout (65s)"}

        duration = round(time.time() - start_time, 2)
        
        # Save Report
        try:
            logs_dir = self.root_dir / "logs"
            logs_dir.mkdir(exist_ok=True, parents=True)
            report_path = logs_dir / f"recon_{target.replace('.', '_')}_{int(time.time())}.json"
            report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"\n[+] Processing Finished in {duration}s.")
            print(f"[+] Full JSON Report: {report_path}")
        except Exception as e:
            print(f"\n[!] Storage Error: {e}")

        if output_format == "json":
            print("\n" + json.dumps(results, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="NEXUS VANGUARD - Ultimate OSINT CLI")
    parser.add_argument("target", nargs="?", help="Target domain, IP, or email")
    parser.add_argument("--module", help="Run only one specific module (e.g. domain_intel)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--list", action="store_true", help="List all available modules")
    args = parser.parse_args()

    cli = ShadowSightCLI()
    cli.banner()

    if args.list:
        print("[*] Available Intelligence Modules:")
        for name, info in cli.modules.items():
            print(f"  - {name:20} | {info['title']}")
        sys.exit(0)

    if not args.target:
        parser.print_help()
        sys.exit(1)

    if args.module and args.module not in cli.modules:
        print(f"[!] Error: Module '{args.module}' not found.")
        sys.exit(1)

    cli.execute(args.target, args.module, args.format)

if __name__ == "__main__":
    main()
