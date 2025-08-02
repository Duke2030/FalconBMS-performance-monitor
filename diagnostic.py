#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot Falcon BMS Monitor issues
Run this to check what processes are running and what GPU libraries are available
"""

import psutil
import sys
import os

def check_gpu_libraries():
    """Check which GPU libraries are available"""
    print("🔍 GPU Library Check:")
    print("-" * 40)
    
    # Check nvidia-ml-py3
    try:
        import nvidia_ml_py3 as nvml
        nvml.nvmlInit()
        device_count = nvml.nvmlDeviceGetCount()
        print(f"✅ nvidia-ml-py3: Available ({device_count} GPU(s) detected)")
        
        # Get GPU info
        if device_count > 0:
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
            print(f"   GPU 0: {name}")
    except ImportError:
        print("❌ nvidia-ml-py3: Not available (ImportError)")
    except Exception as e:
        print(f"❌ nvidia-ml-py3: Error - {e}")
    
    # Check GPUtil
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        print(f"✅ GPUtil: Available ({len(gpus)} GPU(s) detected)")
        for i, gpu in enumerate(gpus):
            print(f"   GPU {i}: {gpu.name}")
    except ImportError:
        print("❌ GPUtil: Not available (ImportError)")
    except Exception as e:
        print(f"❌ GPUtil: Error - {e}")

def find_running_processes():
    """Find all running processes that might be Falcon BMS"""
    print("\n🔍 Process Detection:")
    print("-" * 40)
    
    # Common Falcon BMS process names
    falcon_names = [
        'Falcon BMS.exe', 'falcon bms.exe', 'FALCON BMS.exe',
        'bms.exe', 'BMS.exe',
        'falcon4.exe', 'Falcon4.exe', 'FALCON4.exe',
        'FalconBMS.exe', 'falconbms.exe', 'FALCONBMS.exe',
        'Falcon.exe', 'falcon.exe', 'FALCON.exe'
    ]
    
    print("Looking for Falcon BMS processes...")
    found_processes = []
    
    # Get all running processes
    all_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
        try:
            all_processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'] or 'Unknown',
                'exe': proc.info['exe'] or 'Unknown',
                'cmdline': ' '.join(proc.info['cmdline'] or [])
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Check for exact matches
    for proc in all_processes:
        for falcon_name in falcon_names:
            if falcon_name.lower() == proc['name'].lower():
                found_processes.append(proc)
                print(f"✅ Found exact match: {proc['name']} (PID: {proc['pid']})")
    
    # Check for partial matches
    print("\nChecking for partial matches (any process containing 'falcon' or 'bms'):")
    partial_matches = []
    for proc in all_processes:
        name_lower = proc['name'].lower()
        if ('falcon' in name_lower or 'bms' in name_lower) and proc not in found_processes:
            partial_matches.append(proc)
            print(f"🔍 Partial match: {proc['name']} (PID: {proc['pid']})")
    
    if not found_processes and not partial_matches:
        print("❌ No Falcon BMS processes detected")
        print("\nAll running processes containing 'game', 'sim', or '.exe':")
        game_processes = []
        for proc in all_processes:
            name_lower = proc['name'].lower()
            if ('game' in name_lower or 'sim' in name_lower or '.exe' in name_lower):
                if len(game_processes) < 20:  # Limit output
                    game_processes.append(proc)
        
        for proc in sorted(game_processes, key=lambda x: x['name'].lower())[:20]:
            print(f"   {proc['name']} (PID: {proc['pid']})")
    
    return found_processes + partial_matches

def check_system_info():
    """Check basic system information"""
    print("\n🔍 System Information:")
    print("-" * 40)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Architecture: {os.name}")
    
    # Check if running from exe
    if getattr(sys, 'frozen', False):
        print("✅ Running from compiled executable")
        print(f"Executable path: {sys.executable}")
    else:
        print("✅ Running from Python script")

def main():
    """Run all diagnostic checks"""
    print("🔧 Falcon BMS Monitor Diagnostic Tool")
    print("=" * 50)
    
    check_system_info()
    check_gpu_libraries()
    processes = find_running_processes()
    
    print(f"\n📋 Summary:")
    print("-" * 40)
    print(f"Falcon processes found: {len(processes)}")
    
    if processes:
        print("✅ Process detection should work")
        print("Recommended process names to add to the monitor:")
        for proc in processes:
            print(f"   '{proc['name']}'")
    else:
        print("❌ No Falcon processes detected")
        print("Make sure Falcon BMS is running, then run this diagnostic again")
    
    print(f"\n💡 Next steps:")
    if not processes:
        print("1. Start Falcon BMS")
        print("2. Run this diagnostic again to see the process name")
        print("3. We'll update the monitor with the correct process name")
    else:
        print("1. We'll update the monitor with the detected process names")
        print("2. For GPU issues, we'll create a version without nvidia-ml-py3 dependency")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")