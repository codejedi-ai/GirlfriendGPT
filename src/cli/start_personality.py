#!/usr/bin/env python3
"""Quick start script to load a personality and open chat."""

import json
from pathlib import Path

def load_personality(name: str):
    """Load a personality by name."""
    personalities_dir = Path(__file__).parent / "src" / "templates" / "personalities"
    personality_file = personalities_dir / f"{name.lower().replace(' ', '_')}.json"
    
    if not personality_file.exists():
        print(f"❌ Personality '{name}' not found!")
        print(f"Available: {[f.stem for f in personalities_dir.glob('*.json')]}")
        return None
    
    with open(personality_file) as f:
        return json.load(f)

def main():
    import sys
    
    # Get personality name from argument or default to Sandra
    personality_name = sys.argv[1] if len(sys.argv) > 1 else "Sandra"
    
    print(f"🎯 Loading personality: {personality_name}")
    
    personality = load_personality(personality_name)
    if not personality:
        return 1
    
    # Load or create config
    config_dir = Path.home() / ".gfgpt"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
    else:
        config = {}
    
    # Update with personality
    config.update({
        'name': personality['name'],
        'byline': personality['byline'],
        'identity': personality['identity'],
        'behavior': personality['behavior'],
        'profile_image': personality.get('profile_image', ''),
    })
    
    # Check for API key
    api_key = config.get('model_provider', {}).get('openai', {}).get('api_key', '')
    if not api_key:
        print("\n⚠️  No OpenAI API key found!")
        print("\nPlease add your API key:")
        print(f"  nano {config_file}")
        print("\nAdd this section:")
        print('''  "model_provider": {
    "openai": {
      "api_key": "sk-your-key-here",
      "model": "gpt-4"
    }
  }''')
        print("\nThen run:")
        print("  gfgpt gateway start")
        print("  gfgpt chat")
        return 1
    
    # Save config
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Loaded: {personality['name']}")
    print(f"   {personality['description']}")
    print(f"\n📝 Config: {config_file}")
    print("\n🚀 Next steps:")
    print("  gfgpt gateway start    # Start the gateway")
    print("  gfgpt chat             # Open chat with", personality['name'])
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
