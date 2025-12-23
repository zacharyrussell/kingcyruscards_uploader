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
    print("Installing dependencies...")
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
        print("Dependencies installed successfully!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def build_executable():
    """Build the executable using PyInstaller"""
    print("="*60)
    print("Building executable...")
    print("="*60)
    
    import PyInstaller.__main__
    import platform
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine icon file based on OS
    is_mac = platform.system() == 'Darwin'
    is_windows = platform.system() == 'Windows'
    
    icon_file = 'icon.icns' if is_mac else 'icon.ico'
    icon_path = os.path.join(script_dir, icon_file)
    
    # Determine separator for add-data (different on Windows vs Unix)
    separator = ';' if is_windows else ':'
    
    # Base arguments
    app_name = 'ImageUploader'
    args = [
        'app.py',
        f'--name={app_name}',
        '--onefile',
        '--windowed',  # Remove this line if you want to see console output
        f'--add-data=templates{separator}templates',
        '--hidden-import=qr_window',
        '--hidden-import=update_checker',
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
        print(f"Using custom icon: {icon_path}")
    else:
        print(f"No custom icon found (looking for {icon_file})")

    PyInstaller.__main__.run(args)

    print("\n" + "="*60)
    print("Build complete!")
    print(f"Executable location: {script_dir}/dist/ImageUploader.exe")
    print("="*60)

if __name__ == '__main__':
    # Step 1: Install dependencies
    if not install_dependencies():
        print("\nFailed to install dependencies. Exiting.")
        sys.exit(1)
    
    # Step 2: Build executable
    try:
        build_executable()
    except Exception as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)