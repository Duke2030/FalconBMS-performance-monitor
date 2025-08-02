#!/usr/bin/env python3
"""
CPU Measurement Diagnostic Tool
Tests different CPU measurement methods to find the most accurate one
"""

import psutil
import time
import threading
from collections import deque

def test_cpu_measurement_methods():
    """Test different CPU measurement approaches"""
    print("🔍 Testing CPU Measurement Methods")
    print("=" * 50)
    print("Please keep your flight simulator running in VR...")
    print("Taking measurements over 10 seconds...\n")
    
    # Method 1: psutil with no interval (cached)
    cpu1 = psutil.cpu_percent(interval=None)
    print(f"Method 1 - psutil(interval=None):     {cpu1:6.1f}%")
    
    # Method 2: psutil with 1 second interval
    cpu2 = psutil.cpu_percent(interval=1.0)
    print(f"Method 2 - psutil(interval=1.0):      {cpu2:6.1f}%")
    
    # Method 3: psutil with blocking measurement
    cpu3 = psutil.cpu_percent(interval=2.0)
    print(f"Method 3 - psutil(interval=2.0):      {cpu3:6.1f}%")
    
    # Method 4: Average over multiple samples
    print("Method 4 - Multiple samples (5 seconds)...")
    samples = []
    for i in range(5):
        sample = psutil.cpu_percent(interval=1.0)
        samples.append(sample)
        print(f"  Sample {i+1}: {sample:6.1f}%")
    cpu4 = sum(samples) / len(samples)
    print(f"Method 4 - Average of 5 samples:      {cpu4:6.1f}%")
    
    # Method 5: Per-core analysis
    per_core = psutil.cpu_percent(interval=1.0, percpu=True)
    max_core = max(per_core)
    avg_core = sum(per_core) / len(per_core)
    print(f"Method 5 - Per-core average:          {avg_core:6.1f}%")
    print(f"Method 5 - Highest core:              {max_core:6.1f}%")
    
    print(f"\nCore utilization breakdown:")
    for i, core_usage in enumerate(per_core):
        bar = "█" * int(core_usage / 5)  # Scale for display
        print(f"  Core {i:2d}: {core_usage:6.1f}% {bar}")

def find_intensive_processes():
    """Find processes using the most CPU"""
    print(f"\n🔍 Top CPU-consuming processes:")
    print("=" * 50)
    
    # Get all processes with CPU usage
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            proc_info = proc.info
            # Get CPU usage over 1 second
            cpu_usage = proc.cpu_percent(interval=1.0)
            if cpu_usage > 0.1:  # Only show processes using some CPU
                processes.append({
                    'name': proc_info['name'],
                    'pid': proc_info['pid'],
                    'cpu': cpu_usage
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Sort by CPU usage
    processes.sort(key=lambda x: x['cpu'], reverse=True)
    
    print("Top 15 CPU users:")
    for i, proc in enumerate(processes[:15]):
        print(f"  {i+1:2d}. {proc['name']:<25} {proc['cpu']:6.1f}% (PID: {proc['pid']})")
    
    # Look for VR and flight sim related processes
    vr_keywords = ['vr', 'steam', 'oculus', 'meta', 'falcon', 'bms', 'simulator', 'runtime']
    vr_processes = []
    for proc in processes:
        if any(keyword in proc['name'].lower() for keyword in vr_keywords):
            vr_processes.append(proc)
    
    if vr_processes:
        print(f"\nVR/Flight Sim related processes:")
        for proc in vr_processes:
            print(f"  • {proc['name']:<25} {proc['cpu']:6.1f}% (PID: {proc['pid']})")

def continuous_monitoring():
    """Monitor CPU continuously for patterns"""
    print(f"\n🔍 Continuous CPU Monitoring (30 seconds)")
    print("=" * 50)
    print("Time     Overall  Max Core  Top Process")
    print("-" * 50)
    
    start_time = time.time()
    while time.time() - start_time < 30:
        # Overall CPU
        overall_cpu = psutil.cpu_percent(interval=None)
        
        # Per-core CPU
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        max_core = max(per_core) if per_core else 0
        
        # Find top process
        top_process = "Unknown"
        top_cpu = 0
        for proc in psutil.process_iter(['name', 'cpu_percent']):
            try:
                cpu = proc.cpu_percent()
                if cpu > top_cpu:
                    top_cpu = cpu
                    top_process = proc.info['name'][:15]
            except:
                continue
        
        timestamp = time.strftime("%H:%M:%S")
        print(f"{timestamp}  {overall_cpu:6.1f}%  {max_core:6.1f}%   {top_process} ({top_cpu:.1f}%)")
        
        time.sleep(2)

def system_info():
    """Display system information"""
    print("🔍 System Information")
    print("=" * 50)
    
    # CPU info
    cpu_count = psutil.cpu_count()
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    
    print(f"Physical CPU cores: {cpu_count}")
    print(f"Logical CPU cores:  {cpu_count_logical}")
    if cpu_freq:
        print(f"CPU frequency:      {cpu_freq.current:.0f} MHz (Max: {cpu_freq.max:.0f} MHz)")
    
    # Memory info
    memory = psutil.virtual_memory()
    print(f"Total memory:       {memory.total / (1024**3):.1f} GB")
    print(f"Available memory:   {memory.available / (1024**3):.1f} GB")
    print(f"Memory usage:       {memory.percent:.1f}%")

def main():
    """Run all diagnostics"""
    print("🔧 Falcon BMS CPU Measurement Diagnostic")
    print("=" * 60)
    print("This tool will help identify why CPU measurements seem low")
    print("Make sure Falcon BMS is running in VR before proceeding!\n")
    
    input("Press Enter when ready to start diagnostics...")
    
    system_info()
    print()
    test_cpu_measurement_methods()
    print()
    find_intensive_processes()
    print()
    continuous_monitoring()
    
    print(f"\n💡 Analysis complete!")
    print("=" * 50)
    print("Based on the results above:")
    print("1. Which measurement method showed the highest CPU usage?")
    print("2. Are VR-related processes consuming significant CPU?")
    print("3. Does the continuous monitoring show realistic values?")
    print("\nThis will help us fix the CPU measurement in your monitor!")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")