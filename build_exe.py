#!/usr/bin/env python3
"""
Build script to create Windows .exe from Falcon BMS Performance Monitor
This script will create a standalone executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed, install if not"""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("📦 PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            return False

def install_dependencies():
    """Install all required dependencies"""
    dependencies = [
        "psutil",
        "nvidia-ml-py3", 
        "GPUtil",
        "pyinstaller"
    ]
    
    print("📦 Installing dependencies...")
    for dep in dependencies:
        try:
            # Use older subprocess syntax for compatibility
            with open(os.devnull, 'w') as devnull:
                result = subprocess.call([sys.executable, "-m", "pip", "install", dep], 
                                       stdout=devnull, stderr=devnull)
            if result == 0:
                print(f"✅ {dep} installed")
            else:
                print(f"⚠️  Warning: Could not install {dep}")
                if dep in ["nvidia-ml-py3", "GPUtil"]:
                    print(f"   {dep} is optional for GPU monitoring")
                else:
                    print(f"   {dep} is required - build may fail")
        except Exception as e:
            print(f"⚠️  Warning: Could not install {dep} - {e}")
            if dep in ["nvidia-ml-py3", "GPUtil"]:
                print(f"   {dep} is optional for GPU monitoring")
            else:
                print(f"   {dep} is required - build may fail")

def create_spec_file():
    """Create a custom PyInstaller spec file for better control"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['falcon_bms_monitor.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'nvidia_ml_py3',
        'nvidia_ml_py3.py_nvml',
        'pynvml',
        'GPUtil',
        'psutil',
        'threading',
        'collections',
        'collections.deque',
        'collections.defaultdict',
        'dataclasses',
        'datetime',
        'json',
        'time',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Force include nvidia libraries if available
try:
    import nvidia_ml_py3
    print("Found nvidia_ml_py3 - including in build")
except ImportError:
    print("nvidia_ml_py3 not found")

try:
    import GPUtil
    print("Found GPUtil - including in build")
except ImportError:
    print("GPUtil not found")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FalconBMS_PerformanceMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    with open('falcon_bms_monitor.spec', 'w') as f:
        f.write(spec_content)
    print("✅ Created custom PyInstaller spec file")

def build_executable():
    """Build the executable using PyInstaller"""
    print("\n🔨 Building Windows executable...")
    print("This may take a few minutes...")
    
    # Build command options with comprehensive hidden imports
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Single executable file
        "--console",                    # Keep console window
        "--name", "FalconBMS_PerformanceMonitor",
        "--distpath", "dist",
        "--workpath", "build", 
        "--specpath", ".",
        # Comprehensive hidden imports for GPU libraries
        "--hidden-import", "nvidia_ml_py3",
        "--hidden-import", "nvidia_ml_py3.py_nvml",
        "--hidden-import", "pynvml",  # Alternative name
        "--hidden-import", "GPUtil", 
        "--hidden-import", "psutil",
        "--hidden-import", "threading",
        "--hidden-import", "collections",
        "--hidden-import", "dataclasses",
        "--hidden-import", "datetime",
        "--hidden-import", "json",
        "--hidden-import", "time",
        "--hidden-import", "os",
        "--hidden-import", "sys",
        # Force collect all submodules
        "--collect-all", "nvidia_ml_py3",
        "--collect-all", "GPUtil",
        # Exclude unnecessary modules to reduce size
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy", 
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "tkinter",
        "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6",
        # Optimize
        "--optimize", "2",
        "falcon_bms_monitor.py"
    ]
    
    try:
        # Run PyInstaller - compatible with older Python versions
        print("Running PyInstaller command...")
        result = subprocess.call(build_cmd)
        
        if result == 0:
            print("✅ Executable built successfully!")
            
            # Check if file exists
            exe_path = Path("dist/FalconBMS_PerformanceMonitor.exe")
            if exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
                print(f"📁 Executable location: {exe_path.absolute()}")
                print(f"📏 File size: {file_size:.1f} MB")
                return True
            else:
                print("❌ Executable file not found after build")
                return False
        else:
            print("❌ Build failed!")
            print("Check the output above for error details")
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def cleanup_build_files():
    """Clean up temporary build files"""
    print("\n🧹 Cleaning up build files...")
    
    # Remove build directory
    if os.path.exists("build"):
        shutil.rmtree("build")
        print("✅ Removed build directory")
    
    # Remove spec file
    if os.path.exists("falcon_bms_monitor.spec"):
        os.remove("falcon_bms_monitor.spec")
        print("✅ Removed spec file")
    
    # Remove __pycache__
    if os.path.exists("__pycache__"):
        shutil.rmtree("__pycache__")
        print("✅ Removed __pycache__")

def create_readme():
    """Create a README file for the executable"""
    readme_content = """# Falcon BMS Performance Monitor

## What is this?
This executable monitors your system performance while running Falcon BMS and identifies bottlenecks in real-time.

## How to use:
1. Start Falcon BMS (the tool will detect it automatically)
2. Double-click "FalconBMS_PerformanceMonitor.exe"
3. Watch the real-time performance analysis
4. Follow the recommendations to optimize performance

## What it monitors:
- CPU usage (overall and per-core)
- Memory (RAM) usage
- GPU utilization and VRAM
- GPU temperature
- Falcon BMS process metrics

## Bottleneck detection:
- CPU: High processor usage limiting performance
- Memory: RAM shortage causing slowdowns  
- GPU: Graphics card utilization maxed out
- GPU Memory: VRAM shortage affecting textures/graphics

## Requirements:
- Windows 10/11
- NVIDIA or AMD graphics card (for GPU monitoring)
- No additional software installation required

## Troubleshooting:
- If GPU monitoring doesn't work, the tool will still monitor CPU and RAM
- The tool looks for common Falcon BMS process names
- Run as Administrator if you encounter permission issues

## Controls:
- Press Ctrl+C to stop monitoring
- The display updates every 2 seconds

Built with Python and love for the Falcon BMS community!
"""
    
    with open("dist/README.txt", "w") as f:
        f.write(readme_content)
    print("✅ Created README.txt in dist folder")

def main():
    """Main build process"""
    print("🚀 Falcon BMS Performance Monitor - EXE Builder")
    print("=" * 60)
    
    # Check if source file exists
    if not os.path.exists("falcon_bms_monitor.py"):
        print("❌ Error: falcon_bms_monitor.py not found in current directory")
        print("   Make sure you saved the Python script as 'falcon_bms_monitor.py'")
        return False
    
    # Step 1: Install dependencies
    install_dependencies()
    
    # Step 2: Check PyInstaller
    if not check_pyinstaller():
        return False
    
    # Step 3: Create output directory
    os.makedirs("dist", exist_ok=True)
    
    # Step 4: Build executable
    success = build_executable()
    
    if success:
        # Step 5: Create documentation
        create_readme()
        
        # Step 6: Clean up
        cleanup_build_files()
        
        print("\n🎉 SUCCESS!")
        print("=" * 60)
        print("Your executable is ready:")
        print(f"📁 Location: {os.path.abspath('dist/FalconBMS_PerformanceMonitor.exe')}")
        print("\n📋 Next steps:")
        print("1. Navigate to the 'dist' folder")
        print("2. Copy 'FalconBMS_PerformanceMonitor.exe' wherever you want")
        print("3. Run it while Falcon BMS is running")
        print("4. Read 'README.txt' for detailed instructions")
        
        return True
    else:
        print("\n❌ Build failed. Check the error messages above.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        input(f"\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        input("Press Enter to exit...")