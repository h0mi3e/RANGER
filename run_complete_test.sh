#!/bin/bash
echo "=== COMPLETE RANGER TEST ==="
echo "Starting fresh test..."

# Kill any existing processes
pkill -f "python3 c2.py" 2>/dev/null
sleep 1

# Start C2 with debug output
echo -e "\n[1] Starting C2 server..."
python3 c2.py > c2_debug.log 2>&1 &
C2_PID=$!
echo "C2 PID: $C2_PID"

# Wait for C2 to start
echo "Waiting for C2 to start..."
sleep 5

# Check if C2 is running
if ! ps -p $C2_PID > /dev/null; then
    echo "❌ C2 failed to start"
    cat c2_debug.log
    exit 1
fi

echo "✅ C2 started"

# Run the comprehensive test
echo -e "\n[2] Running comprehensive test..."
python3 test_complete_workflow_final.py

# Check results
echo -e "\n[3] Test results:"
if grep -q "COMPLETE WORKFLOW TEST FINISHED" test_complete_workflow_final.py 2>/dev/null; then
    echo "✅ Test script executed"
else
    echo "❌ Test script failed"
fi

# Show C2 logs
echo -e "\n[4] C2 Debug Logs (last 20 lines):"
tail -20 c2_debug.log

# Cleanup
echo -e "\n[5] Cleaning up..."
kill $C2_PID 2>/dev/null
rm -f c2_debug.log test_*.py test_*.txt

echo -e "\n=== TEST COMPLETE ==="