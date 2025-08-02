# FalconBMS-performance-monitor
To determine what the bottlenecks are CPU,GPU,memory


# Falcon BMS Performance Monitor

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
