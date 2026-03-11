#!/usr/bin/env python3
"""
SubGather - Elite Subdomain Discovery Suite
Bug Bounty Recon Script by JAhid
"""
import subprocess
import sys
import os
import re
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

# ============================================================
#  API KEYS
# ============================================================
VT_API_KEY    = "***VT_KEY_REMOVED***"
GITHUB_TOKEN  = "***GH_TOKEN_REMOVED***"
# ============================================================

LOGO = r"""
                _                    _   _
 ___ _   _  | |__    __ _   __ _| |_| |__   ___  _ __
/ __| | | | | '_ \  / _` | / _` | __| '_ \ / _ \| '__|
\__ \ |_| | | |_) || (_| || (_| | |_| | | |  __/| |
|___/\__,_| |_.__/  \__, | \__,_|\__|_| |_|\___||_|
                     |___/
"""

def print_banner():
    print(LOGO)
    print(f"                    SubGather v2.2 by JAhid")
    print(f"              Target : {target_domain}")
    print(f"              Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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

# FIX 5 — pad overwrite line to 60 chars to fully clear "Running <label>..." leftover chars
def run_command(cmd, shell=True, output_file=None, label=None, silent=False):
    display = label if label else (
        cmd.split()[0].split('/')[-1] if '/' in cmd.split()[0] else cmd.split()[0]
    )
    if not silent:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Running {display}...", end="", flush=True)
    try:
        result = subprocess.run(
            cmd, shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            if not silent:
                line = f"\r[{datetime.now().strftime('%H:%M:%S')}] {display} — failed"
                print(f"{line:<60}")
            return result.stdout, result.stderr, result.returncode
        else:
            if not silent:
                if output_file and os.path.exists(output_file):
                    count = count_lines_in_file(output_file)
                    line = f"\r[{datetime.now().strftime('%H:%M:%S')}] {display} — {format_count(count)} subdomains"
                    print(f"{line:<60}")
                else:
                    # FIX 5 — "merge done" padded to clear "Running merge..." leftover
                    line = f"\r[{datetime.now().strftime('%H:%M:%S')}] {display} — done"
                    print(f"{line:<60}")
            return result.stdout, result.stderr, result.returncode
    except Exception as e:
        if not silent:
            line = f"\r[{datetime.now().strftime('%H:%M:%S')}] {display} — error: {str(e)}"
            print(f"{line:<60}")
        return "", str(e), 1

def main():
    global target_domain

    if len(sys.argv) != 2:
        print(f"Usage: python3 subdomain_gather.py <target_domain>")
        sys.exit(1)

    target_domain = sys.argv[1]
    output_filename = f"{target_domain.replace('.', '_')}-subgather.txt"
    legacy_output_filename = f"{target_domain}.txt"

    print_banner()
    print(f"[>] Target : {target_domain}")
    print(f"[>] Output : {output_filename}")
    print()

    temp_files = [
        "subfinder.txt",
        "assetfinder.txt",
        "findomain.txt",
        "crtsh.txt",
        "wayback.txt",
        "virustotal.txt",
        "git.txt",
        "subs_clean.txt",
        "certspotter.txt",
        "final.txt"
    ]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    # -------------------------------------------------------
    # Step 1: Subfinder
    # -------------------------------------------------------
    print(f"[*] Step 1/8 — Subfinder")
    run_command(
        f"subfinder -d {target_domain} -all -recursive -o subfinder.txt",
        output_file="subfinder.txt", label="subfinder"
    )
    print()  # FIX 3 — spacing between steps

    # -------------------------------------------------------
    # Step 2: Assetfinder
    # -------------------------------------------------------
    print(f"[*] Step 2/8 — Assetfinder")
    run_command(
        f"assetfinder --subs-only {target_domain} > assetfinder.txt",
        output_file="assetfinder.txt", label="assetfinder"
    )
    print()  # FIX 3

    # -------------------------------------------------------
    # Step 3: Findomain
    # -------------------------------------------------------
    print(f"[*] Step 3/8 — Findomain")
    run_command(
        f"findomain -t {target_domain} | tee findomain.txt",
        output_file="findomain.txt", label="findomain"
    )
    print()  # FIX 3

    # -------------------------------------------------------
    # Step 4: CRT.SH
    # FIX 1 — use single-quoted jq filter via bash -c to avoid shell interpretation issues,
    #          and drop broken select() in favour of plain .[].name_value
    # -------------------------------------------------------
    print(f"[*] Step 4/8 — CRT.SH")
    cmd_crtsh = (
        f"bash -c 'curl -s \"https://crt.sh/?q={target_domain}&output=json\""
        f" | jq -r \".[].name_value\""
        f" | sed \"s/^\\*\\.//g\""
        f" | sort -u > crtsh.txt'"
    )
    run_command(cmd_crtsh, output_file="crtsh.txt", label="crt.sh")
    print()  # FIX 3

    # -------------------------------------------------------
    # Step 5: Wayback Machine
    # FIX 2 — rewrite sed chain using double-quoted expressions to eliminate
    #          the broken adjacent-single-quote bug that left the pipe unexecuted
    # -------------------------------------------------------
    print(f"[*] Step 5/8 — Wayback Machine")
    cmd_wayback = (
        f'curl -s "http://web.archive.org/cdx/search/cdx?url=*.{target_domain}/*'
        f'&output=text&fl=original&collapse=urlkey"'
        f' | sort'
        f' | sed -e "s_https*://__" -e "s/\\/.*$//" -e "s/:.*$//" -e "s/^www\\.//"'
        f' | sort -u > wayback.txt'
    )
    run_command(cmd_wayback, output_file="wayback.txt", label="wayback")
    print()  # FIX 3

    # -------------------------------------------------------
    # Step 6: VirusTotal
    # -------------------------------------------------------
    print(f"[*] Step 6/8 — VirusTotal")
    if VT_API_KEY == "YOUR_VT_API_KEY_HERE":
        print(f"[!] SKIPPED VirusTotal — API key not set")
    else:
        vt_query_domain = f"www.{target_domain}"
        cmd_vt = (
            f'curl -s "https://www.virustotal.com/vtapi/v2/domain/report'
            f'?apikey={VT_API_KEY}&domain={vt_query_domain}"'
            f" | jq -r '.domain_siblings[]?' > virustotal.txt"
        )
        run_command(cmd_vt, output_file="virustotal.txt", label="virustotal")
    print()  # FIX 3

    # -------------------------------------------------------
    # Step 7: GitHub Subdomains
    # FIX 4 — run silently, filter silently, then print ONE line with final count
    # -------------------------------------------------------
    print(f"[*] Step 7/8 — GitHub")
    if GITHUB_TOKEN == "YOUR_GITHUB_TOKEN_HERE":
        print(f"[!] SKIPPED GitHub — token not set")
    else:
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] github-subdomains — running...", end="", flush=True)
        try:
            result = subprocess.run(
                f"github-subdomains -d {target_domain} -t {GITHUB_TOKEN}",
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if result.returncode == 0:
                with open('git.txt', 'w') as f:
                    f.write(result.stdout)
                subprocess.run(
                    f"grep -oE '[a-zA-Z0-9._-]+\\.{re.escape(target_domain)}'"
                    f" git.txt | sort -u > subs_clean.txt",
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                count = count_lines_in_file('subs_clean.txt')
                line = f"\r[{datetime.now().strftime('%H:%M:%S')}] github-subdomains — {format_count(count)} subdomains"
                print(f"{line:<60}")
            else:
                line = f"\r[{datetime.now().strftime('%H:%M:%S')}] github-subdomains — failed"
                print(f"{line:<60}")
        except Exception as e:
            line = f"\r[{datetime.now().strftime('%H:%M:%S')}] github-subdomains — error: {str(e)}"
            print(f"{line:<60}")
    print()  # FIX 3

    # -------------------------------------------------------
    # Step 8: CertSpotter
    # -------------------------------------------------------
    print(f"[*] Step 8/8 — CertSpotter")
    cmd_certspotter = (
        f'curl -s "https://api.certspotter.com/v1/issuances'
        f'?domain={target_domain}&include_subdomains=true&expand=dns_names"'
        f" | jq -r '.[].dns_names[]'"
        f" | grep -E '\\.{re.escape(target_domain)}$'"
        f" | sed 's/^\\*\\.//g' | sort -u > certspotter.txt"
    )
    run_command(cmd_certspotter, output_file="certspotter.txt", label="certspotter")
    print()  # FIX 3

    # -------------------------------------------------------
    # Combine + Filter
    # -------------------------------------------------------
    print(f"[*] Aggregating results...")
    run_command("cat *.txt 2>/dev/null | sort -u > final.txt", label="merge")
    run_command(
        f"grep -E '(^|\\.){re.escape(target_domain)}$'"
        f" final.txt | sort -u | uniq > {output_filename}",
        output_file=output_filename, label="filter"
    )

    total_discovered = count_lines_in_file(output_filename)

    # Cleanup temp files
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    if os.path.exists(legacy_output_filename):
        os.remove(legacy_output_filename)

    # Summary
    print()
    print("─" * 50)
    print(f"  Target  : {target_domain}")
    print(f"  Found   : {format_count(total_discovered)} unique subdomains")
    print(f"  Output  : {output_filename}")
    print(f"  Done at : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("─" * 50)
    print()
    print(f"[>] Next step:")
    print(f"    python3 deep_gather.py {target_domain} {output_filename}")

if __name__ == "__main__":
    try:
        from colorama import Fore, Style
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "colorama"], check=True)
        from colorama import Fore, Style
    main()