# SubGather & DeepGather — Subdomain Recon Suite

A two-stage subdomain discovery toolkit built for bug bounty hunters.  
**SubGather** handles fast passive recon. **DeepGather** handles active bruteforce and mutation.

---

## How It Works

```
Stage 1 — subdomain_gather.py   (passive, fast)
          Queries 8 sources simultaneously
                    ↓
          <target_domain>-subgather.txt

Stage 2 — deep_gather.py        (active, slow)
          Bruteforces + mutates using Stage 1 output
                    ↓
          <target_domain>-deepgather.txt
          <target_domain>-FINAL.txt  ← merged output of both stages
```

---

## Prerequisites

### Tools Required

Install all tools before running the scripts.

```bash
# Go-based tools
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/tomnomnom/assetfinder@latest
go install github.com/d3mondev/puredns/v2@latest
go install github.com/projectdiscovery/alterx/cmd/alterx@latest
go install github.com/gwen001/github-subdomains@latest

# Findomain
wget https://github.com/Findomain/Findomain/releases/latest/download/findomain-linux-i386.zip
unzip findomain-linux-i386.zip
chmod +x findomain
sudo mv findomain /usr/local/bin/

# System tools
sudo apt install curl jq -y
```

### Optional

Configure subfinder sources API keys for maximum coverage.
Path:
```bash
~/.config/subfinder/provider-config.yaml
```

### Python Dependencies

```bash
pip install colorama
```

### Wordlists (for DeepGather)

```bash
# Install SecLists
sudo apt install seclists -y

# Or clone manually
git clone https://github.com/danielmiessler/SecLists.git /usr/share/seclists
```

Wordlist used by default:
```
/usr/share/seclists/Discovery/DNS/FUZZSUBS_CYFARE_1.txt
```

Resolvers file used by default:
```
/usr/share/seclists/Miscellaneous/dns-resolvers.txt
```

### API Keys Required

Open `subdomain_gather.py` and fill in your keys at the top of the file:

| Key | Where to get |
|-----|-------------|
| `VT_API_KEY` | [virustotal.com](https://www.virustotal.com) → Profile → API Key |
| `GITHUB_TOKEN` | [github.com](https://github.com/settings/tokens) → Settings → Developer Settings → Personal Access Tokens |

---

## Stage 1 — SubGather (Passive)

Queries 8 passive sources and combines results into a single deduplicated file.

### Sources

| # | Source | Method |
|---|--------|--------|
| 1 | Subfinder | 40+ passive APIs |
| 2 | Assetfinder | Certificate + DNS sources |
| 3 | Findomain | Certificate transparency |
| 4 | CRT.SH | Certificate transparency logs |
| 5 | Wayback Machine | Historical URL archive |
| 6 | VirusTotal | Domain intelligence (API key needed) |
| 7 | GitHub | Source code repository leaks (token needed) |
| 8 | CertSpotter | SSL certificate database |

### Usage

```bash
python3 subdomain_gather.py <target_domain>
```

### Example

```bash
python3 subdomain_gather.py <target_domain>
```

### Output

```
<target_domain>-subgather.txt
```

---

## Stage 2 — DeepGather (Active)

Bruteforces DNS with a wordlist, then generates smart mutations from all found subdomains and resolves them.

### Steps

```
Step 1 — puredns bruteforce
         Tries every word in the wordlist as a subdomain
         Wildcard detection built-in to prevent false positives

Step 2 — alterx mutations
         Takes all known subdomains (subgather + puredns)
         Generates smart variations: api → api-v2, dev-api, api-internal etc.
         puredns resolves the mutations

Step 3 — Merge
         Combines deepgather results with subgather output
         Outputs single FINAL file
```

### Usage

```bash
# Recommended — feed subgather output for richer mutations
python3 deep_gather.py <target_domain> <subgather_output.txt>

# Without seed file — bruteforce only, no enriched mutations
python3 deep_gather.py <target_domain>
```

### Example

```bash
python3 deep_gather.py <target_domain> <target_domain>-subgather.txt
```

### Output Files

| File | Contents |
|------|----------|
| `<target_domain>-subgather.txt` | Stage 1 passive results (kept untouched) |
| `<target_domain>-deepgather.txt` | Stage 2 active results only |
| `<target_domain>-FINAL.txt` | Merged output of both stages |

> Both `-subgather.txt` and `-deepgather.txt` are kept after the run.  
> Delete them manually once you've verified the FINAL file looks correct.

---

## Full Workflow

```bash
# Stage 1 — passive recon (fast)
python3 subdomain_gather.py {domain_name}

# Stage 2 — active bruteforce + mutations (slow)
python3 deep_gather.py {domain_name} t_mobile_com-subgather.txt

# Optional — probe live hosts from FINAL output (separate tool)
cat {domain_name}-FINAL.txt | httpx -ports 80,443,8080 -sc --title -threads 200
```

---

## Notes

- **DeepGather can take a long time** depending on wordlist size. puredns prints a live progress bar so you can track ETA.
- **Run SubGather first** — DeepGather uses its output to generate better mutations.
- **amass** is intentionally excluded — run it separately as it can take hours.
- **httpx** live host probing is intentionally excluded — run it separately on the FINAL output.

---

Built for elite recon. Happy hunting.
