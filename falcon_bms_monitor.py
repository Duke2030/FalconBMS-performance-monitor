#!/usr/bin/env python3
"""
Falcon BMS Performance Monitor and Bottleneck Detector
Monitors CPU, GPU, and Memory usage to identify performance bottlenecks
"""

import psutil
import time
import threading
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import os
import sys

# Try to import GPU monitoring libraries
NVIDIA_AVAILABLE = False  # Disable nvidia-ml-py3 to avoid packaging issues

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
    print("✅ GPU monitoring enabled via GPUtil")
except ImportError:
    GPUTIL_AVAILABLE = False
    print("Warning: GPUtil not available. Install with: pip install GPUtil")


@dataclass
class SystemMetrics:
    """Data class to hold system performance metrics"""
    timestamp: datetime
    cpu_percent: float
    cpu_per_core: List[float]
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    gpu_utilization: float
    gpu_memory_percent: float
    gpu_memory_used_gb: float
    gpu_temperature: float
    falcon_bms_cpu: float
    falcon_bms_memory_mb: float
    bottleneck: str
    bottleneck_score: Dict[str, float]


class PerformanceMonitor:
    def __init__(self, sample_interval: float = 1.0, history_size: int = 300):
        """
        Initialize the performance monitor
        
        Args:
            sample_interval: Time between samples in seconds
            history_size: Number of samples to keep in history
        """
        self.sample_interval = sample_interval
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        self.running = False
        self.monitor_thread = None
        
        # Bottleneck thresholds
        self.thresholds = {
            'cpu_high': 85.0,
            'memory_high': 85.0,
            'gpu_high': 90.0,
            'gpu_memory_high': 85.0
        }
        
        # Initialize GPU monitoring
        self.gpu_available = self._init_gpu_monitoring()
        
    def _init_gpu_monitoring(self) -> bool:
        """Initialize GPU monitoring capabilities"""
        return GPUTIL_AVAILABLE  # Use GPUtil only for reliable .exe packaging

    def _get_gpu_metrics(self) -> Tuple[float, float, float, float]:
        """Get GPU metrics using GPUtil (more reliable for .exe packaging)"""
        if GPUTIL_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    return (
                        gpu.load * 100,           # GPU utilization %
                        gpu.memoryUtil * 100,     # GPU memory %
                        gpu.memoryUsed / 1024,    # GPU memory used in GB
                        gpu.temperature           # GPU temperature
                    )
            except Exception as e:
                print(f"GPU monitoring error: {e}")
        
        return 0.0, 0.0, 0.0, 0.0

    def _find_falcon_bms_process(self) -> Optional[psutil.Process]:
        """Find the Falcon BMS process"""
        falcon_names = ['Falcon BMS.exe', 'bms.exe', 'falcon4.exe', 'FalconBMS.exe']
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if any(name.lower() in proc.info['name'].lower() for name in falcon_names):
                    return psutil.Process(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def _analyze_bottleneck(self, metrics: SystemMetrics) -> Tuple[str, Dict[str, float]]:
        """
        Analyze current metrics to determine bottleneck
        Returns bottleneck type and confidence scores
        """
        scores = {
            'CPU': 0.0,
            'Memory': 0.0,
            'GPU': 0.0,
            'GPU_Memory': 0.0,
            'None': 0.0
        }
        
        # Enhanced CPU bottleneck analysis for multi-core systems
        max_core_usage = max(metrics.cpu_per_core) if metrics.cpu_per_core else 0
        
        # Single-core saturation is more important than overall CPU %
        if max_core_usage > 85.0:
            scores['CPU'] += 0.8  # High confidence for single-core bottleneck
        elif max_core_usage > 70.0:
            scores['CPU'] += 0.5  # Moderate confidence
        elif max_core_usage > 60.0:
            scores['CPU'] += 0.3  # Some CPU pressure
        
        # Overall CPU usage (less important for gaming)
        if metrics.cpu_percent > self.thresholds['cpu_high']:
            scores['CPU'] += (metrics.cpu_percent - self.thresholds['cpu_high']) / 30.0  # Reduced weight
        
        # Falcon BMS specific CPU analysis
        if metrics.falcon_bms_cpu > 150.0:  # More than 1.5 cores
            scores['CPU'] += 0.4
        elif metrics.falcon_bms_cpu > 100.0:  # More than 1 core
            scores['CPU'] += 0.2
        
        # Memory bottleneck analysis
        if metrics.memory_percent > self.thresholds['memory_high']:
            scores['Memory'] += (metrics.memory_percent - self.thresholds['memory_high']) / 15.0
        
        # GPU bottleneck analysis
        if self.gpu_available:
            if metrics.gpu_utilization > self.thresholds['gpu_high']:
                scores['GPU'] += (metrics.gpu_utilization - self.thresholds['gpu_high']) / 10.0
            
            if metrics.gpu_memory_percent > self.thresholds['gpu_memory_high']:
                scores['GPU_Memory'] += (metrics.gpu_memory_percent - self.thresholds['gpu_memory_high']) / 15.0
        
        # If no significant bottleneck detected
        max_score = max(scores.values())
        if max_score < 0.3:
            scores['None'] = 1.0
        
        # Normalize scores
        total_score = sum(scores.values())
        if total_score > 0:
            scores = {k: v / total_score for k, v in scores.items()}
        
        # Determine primary bottleneck
        bottleneck = max(scores.items(), key=lambda x: x[1])[0]
        
        return bottleneck, scores

    def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        timestamp = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        
        # GPU metrics
        gpu_util, gpu_mem_percent, gpu_mem_used_gb, gpu_temp = self._get_gpu_metrics()
        
        # Falcon BMS specific metrics
        falcon_process = self._find_falcon_bms_process()
        falcon_cpu = 0.0
        falcon_memory_mb = 0.0
        
        if falcon_process:
            try:
                falcon_cpu = falcon_process.cpu_percent()
                falcon_memory_mb = falcon_process.memory_info().rss / (1024**2)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Create metrics object
        metrics = SystemMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            cpu_per_core=cpu_per_core,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_available_gb=memory_available_gb,
            gpu_utilization=gpu_util,
            gpu_memory_percent=gpu_mem_percent,
            gpu_memory_used_gb=gpu_mem_used_gb,
            gpu_temperature=gpu_temp,
            falcon_bms_cpu=falcon_cpu,
            falcon_bms_memory_mb=falcon_memory_mb,
            bottleneck="",
            bottleneck_score={}
        )
        
        # Analyze bottleneck
        bottleneck, scores = self._analyze_bottleneck(metrics)
        metrics.bottleneck = bottleneck
        metrics.bottleneck_score = scores
        
        return metrics

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                time.sleep(self.sample_interval)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(self.sample_interval)

    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("Performance monitoring started...")

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("Performance monitoring stopped.")

    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_bottleneck_analysis(self, window_seconds: int = 30) -> Dict:
        """
        Get bottleneck analysis over a time window
        
        Args:
            window_seconds: Analysis window in seconds
        """
        if not self.metrics_history:
            return {"error": "No metrics data available"}
        
        # Get metrics within the time window
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            recent_metrics = [self.metrics_history[-1]]
        
        # Aggregate bottleneck scores
        bottleneck_counts = defaultdict(int)
        avg_scores = defaultdict(list)
        
        for metrics in recent_metrics:
            bottleneck_counts[metrics.bottleneck] += 1
            for component, score in metrics.bottleneck_score.items():
                avg_scores[component].append(score)
        
        # Calculate averages
        final_scores = {}
        for component, scores in avg_scores.items():
            final_scores[component] = sum(scores) / len(scores)
        
        # Get current metrics
        current = recent_metrics[-1]
        
        return {
            "current_bottleneck": current.bottleneck,
            "bottleneck_confidence": final_scores,
            "bottleneck_frequency": dict(bottleneck_counts),
            "current_metrics": {
                "cpu_percent": current.cpu_percent,
                "memory_percent": current.memory_percent,
                "gpu_utilization": current.gpu_utilization,
                "gpu_memory_percent": current.gpu_memory_percent,
                "falcon_bms_cpu": current.falcon_bms_cpu,
                "falcon_bms_memory_mb": current.falcon_bms_memory_mb
            },
            "recommendations": self._get_recommendations(current)
        }

    def _get_recommendations(self, metrics: SystemMetrics) -> List[str]:
        """Get performance recommendations based on current metrics"""
        recommendations = []
        
        max_core_usage = max(metrics.cpu_per_core) if metrics.cpu_per_core else 0
        
        if metrics.bottleneck == "CPU":
            if max_core_usage > 80:
                recommendations.extend([
                    f"Single-core bottleneck detected (Core at {max_core_usage:.0f}%)",
                    "Falcon BMS is limited by single-threaded performance",
                    "Consider overclocking your CPU for better single-core performance",
                    "Lower CPU-intensive settings: AI traffic, ground objects, weather complexity"
                ])
            else:
                recommendations.extend([
                    "CPU bottleneck detected - reduce CPU-intensive settings",
                    "Close unnecessary background applications",
                    "Lower AI traffic and ground object density",
                    "Consider upgrading to a faster CPU"
                ])
        elif metrics.bottleneck == "Memory":
            recommendations.extend([
                "Memory shortage detected - close unnecessary applications",
                "Consider adding more RAM to your system",
                "Lower texture quality in Falcon BMS settings",
                "Check for memory leaks in background processes"
            ])
        elif metrics.bottleneck == "GPU":
            recommendations.extend([
                "GPU bottleneck - lower graphics settings in Falcon BMS",
                "Reduce anti-aliasing and post-processing effects",
                "Lower VR resolution or use dynamic resolution scaling",
                "Check GPU temperatures and fan curves"
            ])
        elif metrics.bottleneck == "GPU_Memory":
            recommendations.extend([
                "GPU memory bottleneck - lower texture quality and resolution",
                "Reduce visual range and object density in VR",
                "Close other GPU-intensive applications",
                "Consider a GPU upgrade with more VRAM"
            ])
        else:
            recommendations.append("System performance appears balanced. No immediate bottlenecks detected.")
            if max_core_usage > 60:
                recommendations.append(f"Note: Highest core usage is {max_core_usage:.0f}% - monitor for single-core limits")
        
        return recommendations

    def print_real_time_status(self):
        """Print real-time status to console"""
        while self.running:
            try:
                os.system('cls' if os.name == 'nt' else 'clear')
                
                current = self.get_current_metrics()
                if not current:
                    print("Collecting initial data...")
                    time.sleep(1)
                    continue
                
                analysis = self.get_bottleneck_analysis(30)
                
                print("=" * 80)
                print(f"FALCON BMS PERFORMANCE MONITOR - {current.timestamp.strftime('%H:%M:%S')}")
                print("=" * 80)
                
                # System metrics
                print(f"\n📊 SYSTEM METRICS:")
                print(f"  CPU Usage:     {current.cpu_percent:6.1f}% overall (Max core: {max(current.cpu_per_core):6.1f}%)")
                print(f"  Memory Usage:  {current.memory_percent:6.1f}% ({current.memory_used_gb:.1f}GB used)")
                
                # Show top 4 most active CPU cores for better insight
                top_cores = sorted(enumerate(current.cpu_per_core), key=lambda x: x[1], reverse=True)[:4]
                core_info = ", ".join([f"C{core}:{usage:.0f}%" for core, usage in top_cores if usage > 5])
                if core_info:
                    print(f"  Active Cores:  {core_info}")
                
                if self.gpu_available:
                    print(f"  GPU Usage:     {current.gpu_utilization:6.1f}% (Temp: {current.gpu_temperature:.0f}°C)")
                    print(f"  GPU Memory:    {current.gpu_memory_percent:6.1f}% ({current.gpu_memory_used_gb:.1f}GB used)")
                else:
                    print(f"  GPU Usage:     Not available (install GPUtil for GPU monitoring)")
                
                # Falcon BMS specific
                print(f"\n🎮 FALCON BMS:")
                if current.falcon_bms_cpu > 0:
                    print(f"  Process CPU:   {current.falcon_bms_cpu:6.1f}%")
                    print(f"  Process RAM:   {current.falcon_bms_memory_mb:6.0f}MB")
                else:
                    print(f"  Status:        Not detected (not running or different process name)")
                
                # Bottleneck analysis
                print(f"\n🚨 BOTTLENECK ANALYSIS:")
                print(f"  Primary:       {analysis['current_bottleneck']}")
                
                print(f"  Confidence:")
                for component, confidence in sorted(analysis['bottleneck_confidence'].items(), 
                                                  key=lambda x: x[1], reverse=True):
                    if confidence > 0.1:
                        bar = "█" * int(confidence * 20)
                        print(f"    {component:12s} {confidence:5.1%} {bar}")
                
                # Recommendations
                print(f"\n💡 RECOMMENDATIONS:")
                for i, rec in enumerate(analysis['recommendations'][:3], 1):
                    print(f"  {i}. {rec}")
                
                print(f"\n⏱️  Monitoring for {len(self.metrics_history)} samples")
                print("   Press Ctrl+C to stop monitoring")
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Display error: {e}")
                time.sleep(1)


def main():
    """Main function to run the performance monitor"""
    print("Falcon BMS Performance Monitor")
    print("=" * 40)
    
    # Create monitor instance
    monitor = PerformanceMonitor(sample_interval=1.0)
    
    try:
        # Start monitoring
        monitor.start_monitoring()
        
        # Wait a moment for initial data
        time.sleep(2)
        
        # Start real-time display
        monitor.print_real_time_status()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()