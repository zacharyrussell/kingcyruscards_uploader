import requests
import json
from packaging import version
import webbrowser

# Your GitHub repo details
GITHUB_REPO = "https://github.com/zacharyrussell/kingcyruscards_uploader"  # Change this to your repo
CURRENT_VERSION = "1.0.8"  # Update this with each release

def check_for_updates():
    """Check GitHub releases for a newer version"""
    try:
        # Get latest release from GitHub API
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        latest_version = data['tag_name'].lstrip('v')  # Remove 'v' prefix if present
        download_url = data['html_url']
        
        # Compare versions
        if version.parse(latest_version) > version.parse(CURRENT_VERSION):
            return {
                'available': True,
                'latest_version': latest_version,
                'current_version': CURRENT_VERSION,
                'download_url': download_url,
                'release_notes': data.get('body', 'No release notes available')
            }
        
        return {'available': False}
    
    except Exception as e:
        print(f"Could not check for updates: {e}")
        return None

def prompt_update(update_info):
    """Show update prompt in terminal"""
    if not update_info or not update_info.get('available'):
        return False
    
    print("\n" + "="*60)
    print("🎉 NEW VERSION AVAILABLE!")
    print("="*60)
    print(f"Current version: {update_info['current_version']}")
    print(f"Latest version:  {update_info['latest_version']}")
    print(f"\nRelease notes:\n{update_info['release_notes'][:200]}...")
    print("="*60)
    
    response = input("\nOpen download page? (y/n): ").lower().strip()
    if response == 'y':
        webbrowser.open(update_info['download_url'])
        return True
    
    return False

def check_for_updates_silent():
    """Check for updates without user prompt, return True if available"""
    update_info = check_for_updates()
    return update_info and update_info.get('available', False)