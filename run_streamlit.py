#!/usr/bin/env python3
"""
Simple Streamlit Dashboard Launcher
This script launches the AKALA dashboard on port 8501
"""

import subprocess
import sys
import time
import os
import signal

def kill_port_8501():
    """Kill any process using port 8501"""
    try:
        # Use lsof to find and kill process on port 8501
        result = subprocess.run(['lsof', '-ti', ':8501'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid and pid.strip():
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        print(f"💀 Killed process on port 8501 (PID: {pid})")
                        time.sleep(1)  # Give it time to die
                    except (OSError, ValueError) as e:
                        print(f"⚠️  Could not kill PID {pid}: {e}")
    except FileNotFoundError:
        print("⚠️  lsof not available, trying alternative method")
        try:
            # Alternative: use netstat and kill
            result = subprocess.run(['netstat', '-anp', 'tcp'], capture_output=True, text=True)
            if ':8501' in result.stdout:
                print("⚠️  Port 8501 appears to be in use, but cannot kill process")
        except FileNotFoundError:
            print("⚠️  Neither lsof nor netstat available")

def main():
    """Main launcher function"""
    print("🚀 Launching AKALA Streamlit Dashboard...")
    print("📊 This will open a web browser with your dashboard")
    print("💡 You can select users, choose metrics, and generate dashboards!")
    
    # Check if Streamlit is installed
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "--version"], 
                      check=True, capture_output=True)
        print("✅ Streamlit is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Streamlit not found. Installing dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                          check=True)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return
    
    # Kill any existing process on port 8501
    print("🧹 Checking port 8501...")
    kill_port_8501()
    
    # Wait a moment for cleanup
    time.sleep(2)
    
    print("🌐 Starting dashboard on port 8501...")
    print("📱 Dashboard will be available at: http://localhost:8501")
    print("🔄 To stop the dashboard, press Ctrl+C in this terminal")
    
    try:
        # Launch Streamlit
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "interactive_dashboard.py",
            "--server.port", "8501",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ])
        
        print("✅ Dashboard started successfully!")
        print("🌐 Open your browser to: http://localhost:8501")
        
        # Wait for the process
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping dashboard...")
        if 'process' in locals():
            process.terminate()
            process.wait(timeout=5)
        print("✅ Dashboard stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'process' in locals():
            process.terminate()
    finally:
        # Final cleanup
        print("🧹 Final cleanup...")
        kill_port_8501()
        print("✅ Cleanup complete!")

if __name__ == "__main__":
    main()
