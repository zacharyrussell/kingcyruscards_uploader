"""
Build script to create executable
Run: python build_exe.py
"""
import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies if not already installed"""
    print("="*60)
    print("📦 Installing dependencies...")
    print("="*60)
    
    try:
        subprocess.check_call([
            sys.executable, 
            '-m', 
            'pip', 
            'install', 
            '-r', 
            'requirements.txt',
            '--quiet'
        ])
        print("✅ Dependencies installed successfully!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def build_executable():
    """Build the executable using PyInstaller"""
    print("="*60)
    print("🔨 Building executable...")
    print("="*60)
    
    import PyInstaller.__main__
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if custom icon exists
    icon_path = os.path.join(script_dir, 'icon.ico')
    icon_arg = f'--icon={icon_path}' if os.path.exists(icon_path) else '--icon=NONE'

    args = [
        'app.py',
        '--name=ImageUploader',
        '--onefile',
        '--windowed',  # Remove this line if you want to see console output
        '--add-data=templates:templates',
        '--hidden-import=qr_window',
        '--hidden-import=PIL._tkinter_finder',
        '--collect-all=qrcode',
        '--collect-all=PIL',
        f'--distpath={script_dir}/dist',
        f'--workpath={script_dir}/build',
        f'--specpath={script_dir}',
    ]
    
    # Only add icon if it exists
    if os.path.exists(icon_path):
        args.append(f'--icon={icon_path}')
        print(f"🎨 Using custom icon: {icon_path}")
    else:
        print("ℹ️  No custom icon found (looking for icon.ico)")

    PyInstaller.__main__.run(args)

    print("\n" + "="*60)
    print("✅ Build complete!")
    print(f"📁 Executable location: {script_dir}/dist/ImageUploader.exe")
    print("="*60)

if __name__ == '__main__':
    # Step 1: Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies. Exiting.")
        sys.exit(1)
    
    # Step 2: Build executable
    try:
        build_executable()
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)