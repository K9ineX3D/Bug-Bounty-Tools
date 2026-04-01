#!/usr/bin/env python3
"""
DeepGather - Active DNS Bruteforce + Mutation Engine
Bug Bounty Recon Script by JAhid
Run AFTER subdomain_gather.py
"""
import subprocess
import sys
import os
import re
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

# ============================================================
WORDLIST  = "/usr/share/seclists/Discovery/DNS/FUZZSUBS_CYFARE_1.txt"
RESOLVERS = "/usr/share/seclists/Miscellaneous/dns-resolvers.txt"
# ============================================================

LOGO = r"""
     _
  __| |  ___   ___  _ __    __ _   __ _  _   _
 / _` | / _ \ / _ \| '_ \  / _` | / _` || | | |
| (_| ||  __/|  __/| |_) || (_| || (_| || |_| |
 \__,_| \___| \___|| .__/  \__, | \__,_| \__,_|
                    |_|     |___/
"""

def print_banner():
    print(LOGO)
    print(f"                  DeepGather v1.0 by JAhid")
    print(f"             Target : {target_domain}")
    print(f"             Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def count_lines_in_file(filename):
    try:
        with open(filename, 'r') as f:
            return sum(1 for line in f if line.strip())
    except FileNotFoundError:
        return 0

def format_count(count):
    if count > 0:
        return f"{Fore.GREEN}{count}{Style.RESET_ALL}"
    return f"{Fore.RED}{count}{Style.RESET_ALL}"

def run_command(cmd, label, output_file=None):
    """Standard silent command — captures output."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running {label}...", end="", flush=True)
    try:
        result = subprocess.run(
            cmd, shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if output_file and os.path.exists(output_file):
            count = count_lines_in_file(output_file)
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] {label} — {format_count(count)} subdomains")
        else:
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] {label} done")
        return result.stdout, result.returncode
    except Exception as e:
        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] {label} error: {e}")
        return "", 1

def run_live(cmd, label):
    """
    Live output command — lets tool print directly to terminal.
    Used for puredns so the progress bar is visible.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting {label} (live output below)")
    print("─" * 60)
    try:
        result = subprocess.run(cmd, shell=True)
        print("─" * 60)
        return result.returncode
    except Exception as e:
        print(f"Error: {e}")
        return 1

def main():
    global target_domain

    # -------------------------------------------------------
    # Argument handling
    # -------------------------------------------------------
    if len(sys.argv) < 2:
        print(f"Usage: python3 deep_gather.py <target_domain> [subgather_output.txt]")
        sys.exit(1)

    target_domain = sys.argv[1]
    seed_file = None

    if len(sys.argv) == 3:
        # File provided as argument
        seed_file = sys.argv[2]
        if not os.path.exists(seed_file):
            print(f"{Fore.RED}[!] File not found: {seed_file}{Style.RESET_ALL}")
            sys.exit(1)
    else:
        # No file provided — warn in red and ask
        print(f"{Fore.RED}[!] No subgather file provided.{Style.RESET_ALL}")
        print(f"{Fore.RED}[!] alterx mutations will only use puredns results (less effective).{Style.RESET_ALL}")
        print()
        print(f"    Options:")
        print(f"    [1] Press ENTER to proceed without seed file")
        print(f"    [2] Type the file path and press ENTER")
        print()
        user_input = input("    > ").strip()

        if user_input == "":
            print(f"[>] Proceeding without seed file...")
            seed_file = None
        else:
            if os.path.exists(user_input):
                seed_file = user_input
                print(f"[>] Using seed file: {seed_file}")
            else:
                print(f"{Fore.RED}[!] File not found: {user_input} — proceeding without seed file{Style.RESET_ALL}")
                seed_file = None

    # Output files — named with -deepgather and -subgather suffixes
    deep_output   = f"{target_domain.replace('.', '_')}-deepgather.txt"
    # subgather output file (for final merge)
    sub_output    = seed_file if seed_file else None
    final_output  = f"{target_domain.replace('.', '_')}-FINAL.txt"

    print_banner()
    print(f"[>] Wordlist  : {WORDLIST}")
    print(f"[>] Resolvers : {RESOLVERS}")
    print(f"[>] Seed file : {seed_file if seed_file else 'none'}")
    print(f"[>] Output    : {deep_output}")
    print()

    # Sanity checks
    if not os.path.exists(WORDLIST):
        print(f"{Fore.RED}[!] Wordlist not found: {WORDLIST}{Style.RESET_ALL}")
        sys.exit(1)

    resolvers_flag = f"--resolvers {RESOLVERS}" if os.path.exists(RESOLVERS) else ""
    if not resolvers_flag:
        print(f"[!] Resolvers file not found — using system DNS (may be slower)")

    temp_files = [
        "puredns_brute.txt",
        "alterx_mutations.txt",
        "alterx_resolved.txt",
        "_seed_combined.txt",
        "deep_final.txt"
    ]

    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)

    # -------------------------------------------------------
    # Step 1: puredns bruteforce — LIVE output with progress bar
    # -------------------------------------------------------
    print(f"[*] Step 1/3 — puredns bruteforce")
    wordlist_count = count_lines_in_file(WORDLIST)
    print(f"[>] Wordlist : {format_count(wordlist_count)} words")
    print(f"[!] This will take a while — watch the progress bar below")
    print()

    cmd_puredns = (
        f"puredns bruteforce {WORDLIST} {target_domain} "
        f"{resolvers_flag} "
        f"--wildcard-tests 5 "
        f"--wildcard-batch 1000000 "
        f"-w puredns_brute.txt"
    )

    # Run live so puredns progress bar prints to terminal
    ret = run_live(cmd_puredns, label="puredns bruteforce")

    puredns_count = count_lines_in_file("puredns_brute.txt")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] puredns done — {format_count(puredns_count)} subdomains found")
    print()

    # -------------------------------------------------------
    # Step 2: alterx mutations
    # -------------------------------------------------------
    print(f"[*] Step 2/3 — alterx mutations")

    # Build seed: combine puredns results + subgather file if available
    if seed_file and os.path.exists(seed_file):
        merge_cmd = f"cat {seed_file} puredns_brute.txt 2>/dev/null | sort -u > _seed_combined.txt"
        subprocess.run(merge_cmd, shell=True)
        actual_seed = "_seed_combined.txt"
        seed_count = count_lines_in_file(actual_seed)
        print(f"[>] Seed: subgather + puredns combined — {format_count(seed_count)} subdomains")
    else:
        actual_seed = "puredns_brute.txt"
        print(f"[>] Seed: puredns only — {format_count(puredns_count)} subdomains")

    if count_lines_in_file(actual_seed) == 0:
        print(f"[!] No subdomains to mutate — skipping alterx")
    else:
        # Generate mutations
        run_command(
            f"cat {actual_seed} | alterx -o alterx_mutations.txt",
            label="alterx generate",
            output_file="alterx_mutations.txt"
        )

        mutation_count = count_lines_in_file("alterx_mutations.txt")
        print(f"[>] {format_count(mutation_count)} mutations generated — resolving with puredns...")
        print()

        # Resolve mutations — LIVE output with progress bar
        cmd_resolve = (
            f"puredns resolve alterx_mutations.txt "
            f"{resolvers_flag} "
            f"--wildcard-tests 5 "
            f"-w alterx_resolved.txt"
        )
        run_live(cmd_resolve, label="puredns resolve mutations")

        alterx_count = count_lines_in_file("alterx_resolved.txt")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] alterx resolve done — {format_count(alterx_count)} new subdomains")
        print()

    # -------------------------------------------------------
    # Step 3: Combine deep results → deepgather output
    # -------------------------------------------------------
    print(f"[*] Step 3/3 — Combining results")

    run_command(
        "cat puredns_brute.txt alterx_resolved.txt 2>/dev/null | sort -u > deep_final.txt",
        label="merge deep results"
    )

    # Filter to target domain only → deepgather output
    run_command(
        f"grep -E '(^|\\.){re.escape(target_domain)}$' "
        f"deep_final.txt | sort -u > {deep_output}",
        label="filter deepgather",
        output_file=deep_output
    )

    deep_count = count_lines_in_file(deep_output)

    # -------------------------------------------------------
    # Merge subgather + deepgather → FINAL
    # -------------------------------------------------------
    if sub_output and os.path.exists(sub_output):
        merge_final_cmd = (
            f"cat {sub_output} {deep_output} | sort -u > {final_output}"
        )
        subprocess.run(merge_final_cmd, shell=True)
        final_count = count_lines_in_file(final_output)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] merged subgather + deepgather — {format_count(final_count)} total")
    else:
        # No subgather file — FINAL = deepgather only
        subprocess.run(f"cp {deep_output} {final_output}", shell=True)
        final_count = deep_count
        print(f"[{datetime.now().strftime('%H:%M:%S')}] no subgather file — FINAL = deepgather only")

    # Cleanup temp files
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)

    # -------------------------------------------------------
    # Summary
    # -------------------------------------------------------
    sub_count = count_lines_in_file(sub_output) if sub_output else 0

    print()
    print("─" * 55)
    print(f"  Target          : {target_domain}")
    print(f"  subgather subs  : {format_count(sub_count)}")
    print(f"  deepgather subs : {format_count(deep_count)}")
    print(f"  FINAL total     : {format_count(final_count)} unique subdomains")
    print(f"  Files kept:")
    if sub_output:
        print(f"    {sub_output}  ({format_count(sub_count)} subs)")
    print(f"    {deep_output}  ({format_count(deep_count)} subs)")
    print(f"    {final_output}  ({format_count(final_count)} subs)")
    print(f"  Done at         : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("─" * 55)
    print()
    print(f"[>] Happy hunting, JAhid!")

if __name__ == "__main__":
    try:
        from colorama import Fore, Style
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "colorama"], check=True)
        from colorama import Fore, Style
    main()
