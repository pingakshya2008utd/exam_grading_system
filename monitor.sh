#!/bin/bash
# Monitor the grading process

echo "🔍 Monitoring exam grading process..."
echo

count=0
max_checks=30  # 15 minutes max (30 * 30 seconds)

while [ $count -lt $max_checks ]; do
    # Check if output file exists
    if [ -f "data/output/grading_report_unknown.json" ]; then
        echo "✅ GRADING COMPLETE!"
        echo
        echo "=== FINAL RESULTS ==="
        cat data/output/grading_report_unknown.json | python -m json.tool | grep -E '"total_marks|percentage|grade"' | head -10
        echo
        echo "Full report available at: data/output/grading_report_unknown.json"
        exit 0
    fi
    
    # Show progress
    count=$((count + 1))
    echo "[$count/$max_checks] ⏳ Processing... Latest log:"
    tail -2 full_run.log 2>/dev/null | grep -v "^$" | tail -1
    
    sleep 30
done

echo "⚠️  Process taking longer than expected. Check full_run.log for details."
tail -20 full_run.log
