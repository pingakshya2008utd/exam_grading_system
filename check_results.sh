#!/bin/bash
# Check grading results

echo "=== Checking Grading Results ==="
echo

if [ -f "data/output/grading_report_unknown.json" ]; then
    echo "✓ Grading report found!"
    echo
    echo "=== Summary ==="
    cat data/output/grading_report_unknown.json | python -m json.tool | grep -A 20 '"total_marks"'
    echo
    echo "=== Full Report ==="
    cat data/output/grading_report_unknown.json | python -m json.tool
else
    echo "✗ Grading not complete yet. Current status:"
    tail -20 full_run.log
fi
