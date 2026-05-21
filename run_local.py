import os
import re
import sys
import time
import subprocess
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.resolve()
ENV_PATH = ROOT_DIR / "config" / ".env"

def print_banner():
    print("=" * 60)
    print("   SpeakLearnPlay - Smart Launcher & Tunnel Auto-Updater   ")
    print("=" * 60)

def find_tunnel_url(proc):
    """Reads ssh output line by line and extracts the .lhr.life or .localhost.run URL."""
    print("[Launcher] Starting SSH Tunnel to port 5173...")
    url_pattern = re.compile(r"https://[a-zA-Z0-9.-]+\.(?:lhr\.life|localhost\.run)")
    
    # We will wait up to 15 seconds to find the URL
    start_time = time.time()
    while time.time() - start_time < 15:
        line = proc.stdout.readline()
        if not line:
            # Check if process died
            if proc.poll() is not None:
                print(f"[ERROR] SSH Tunnel process exited prematurely with code {proc.returncode}")
                return None
            time.sleep(0.1)
            continue
            
        line_str = line.strip()
        # Print output so user can see tunnel messages
        if line_str:
            print(f"  [Tunnel] {line_str}")
            
        # Only parse the line if it represents the active tunnel (avoiding banners with links)
        if "tunneled with tls termination" in line_str:
            match = url_pattern.search(line_str)
            if match:
                url = match.group(0)
                # Ensure it's not the admin UI page link
                if "admin.localhost.run" not in url:
                    return url
            
    print("[ERROR] Timeout waiting for SSH tunnel URL.")
    return None

def update_env_file(tunnel_url):
    """Automatically updates config/.env with the new tunnel URL."""
    if not ENV_PATH.exists():
        print(f"[WARNING] config/.env not found at {ENV_PATH}. Cannot auto-update.")
        return False
        
    content = ENV_PATH.read_text(encoding="utf-8")
    
    # We need to find WEBAPP_URL line
    lines = content.splitlines()
    updated = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith("WEBAPP_URL="):
            # Parse existing URL
            val = line.split("=", 1)[1].strip()
            
            # Case 1: Vercel style with query parameter ?api_url=
            if "?api_url=" in val:
                base, old_api = val.split("?api_url=", 1)
                new_line = f"WEBAPP_URL={base}?api_url={tunnel_url}"
                lines[i] = new_line
                updated = True
                print(f"[Launcher] Auto-updated Vercel WEBAPP_URL in config/.env:")
                print(f"  Old: {val}")
                print(f"  New: {base}?api_url={tunnel_url}")
            # Case 2: Direct tunnel style (e.g. https://xxxx.lhr.life/streak or without path)
            elif ".lhr.life" in val or ".localhost.run" in val:
                # Find path if any (e.g. /streak)
                path = ""
                # Simple extraction of path after host
                url_match = re.search(r"https?://[^/]+(/.*)?", val)
                if url_match and url_match.group(1):
                    path = url_match.group(1)
                new_line = f"WEBAPP_URL={tunnel_url}{path}"
                lines[i] = new_line
                updated = True
                print(f"[Launcher] Auto-updated Direct WEBAPP_URL in config/.env:")
                print(f"  Old: {val}")
                print(f"  New: {tunnel_url}{path}")
            else:
                # Default fallback: if it's localhost or anything else, let's append it
                # to make sure they get the dynamic API URL in local mode
                pass
                
    if updated:
        ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True
    else:
        print("[Launcher] WEBAPP_URL in config/.env is not using a dynamic tunnel or api_url param. Skipping auto-update.")
        print(f"[Launcher] Current WEBAPP_URL value: {content}")
        return False

def safe_terminate(proc, name="Process"):
    """Terminates a process and all its children to prevent orphaned processes on Windows."""
    if proc and proc.poll() is None:
        print(f"[Launcher] Terminating {name} (PID: {proc.pid})...")
        if os.name == 'nt':
            try:
                # taskkill /F /T /PID kills the process and all of its descendants
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                print(f"[Launcher] Warning: taskkill failed, falling back to standard termination: {e}")
                proc.terminate()
        else:
            proc.terminate()

def main():
    print_banner()
    
    # 1. Start SSH Tunnel
    tunnel_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=NUL", "-R", "80:localhost:5173", "nokey@localhost.run"]
    tunnel_proc = subprocess.Popen(
        tunnel_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    
    tunnel_url = find_tunnel_url(tunnel_proc)
    if not tunnel_url:
        print("[ERROR] Could not set up SSH tunnel. Aborting.")
        safe_terminate(tunnel_proc, "SSH Tunnel")
        sys.exit(1)
        
    print(f"\n[SUCCESS] Active Tunnel URL: {tunnel_url}\n")
    
    # 2. Update config/.env
    update_env_file(tunnel_url)
    
    # 3. Start Backend
    print("[Launcher] Starting FastAPI Backend on port 8001...")
    api_proc = subprocess.Popen(
        ["uv", "run", "python", "-m", "api.main"],
        cwd=ROOT_DIR,
    )
    
    # 4. Start Frontend Vite Dev Server
    print("[Launcher] Starting React/Vite Frontend on port 5173...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=ROOT_DIR / "frontend",
        shell=True, # Need shell=True for npm command on Windows
    )
    
    # 5. Start Bot in the foreground
    print("[Launcher] Starting Telegram Bot...")
    try:
        # We do NOT reload env manually into environment dictionary to avoid quoting bugs
        # like ADMIN_LIST='[]'. The standard python-dotenv inside common/config.py
        # will read the newly saved config/.env file dynamically from disk on startup.
        subprocess.run(["uv", "run", "main.py"], cwd=ROOT_DIR)
    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down processes...")
    finally:
        # Graceful cleanup of all processes and children
        safe_terminate(tunnel_proc, "SSH Tunnel")
        safe_terminate(api_proc, "Backend")
        safe_terminate(frontend_proc, "Frontend")
        
        # Wait a moment for processes to exit
        time.sleep(1)
        print("[Launcher] All processes stopped. Goodbye!")

if __name__ == "__main__":
    main()
