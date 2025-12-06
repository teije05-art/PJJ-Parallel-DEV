#!/bin/bash
# Monitor Tesseract extraction v2 progress in real-time

echo "=================================="
echo "EXTRACTION PROGRESS MONITOR"
echo "=================================="
echo ""

# Check if process is running
if ps aux | grep -q "extract_metadata_v2.py" | grep -v grep; then
    echo "✓ Extraction RUNNING"
else
    echo "✗ Extraction NOT running"
fi

echo ""
echo "--- Current Progress ---"
echo ""

# Count populated files before extraction started
BEFORE=2677

# Count current populated files
AFTER=$(find /Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database -name "*.md" -size +500c 2>/dev/null | wc -l)

# Calculate newly extracted
EXTRACTED=$((AFTER - BEFORE))

echo "Files with content: $AFTER (was $BEFORE)"
echo "Newly extracted: $EXTRACTED / 731"
echo "Progress: $(echo "scale=1; $EXTRACTED * 100 / 731" | bc)%"

echo ""
echo "--- By Category ---"
echo ""

for cat in 02_VAT 03_Customs 05_DTA 04_PIT 08_Tax_Administration 10_Natural_Resources_SHUI 13_Environmental_Protection_EPT 14_Immigration_Work_Permits 06_Transfer_Pricing 07_FCT 09_Excise_Tax_SST 11_Draft_Regulations 12_Capital_Gains_Tax_CGT 15_E_Commerce 16_Business_Support_Measures 17_General_Policies 18_Miscellaneous; do
    cat_path="/Users/teije/Desktop/memagent-modular-fixed/local-memory/tax_legal/tax_database/$cat"

    if [ -d "$cat_path" ]; then
        total=$(find "$cat_path" -name "*.md" -type f 2>/dev/null | wc -l)
        populated=$(find "$cat_path" -name "*.md" -size +500c 2>/dev/null | wc -l)
        empty=$((total - populated))
        pct=$((100 * populated / (total > 0 ? total : 1)))

        if [ $empty -gt 0 ]; then
            printf "%-40s: %3d/%3d populated  (%3d%% complete)\n" "$cat" "$populated" "$total" "$pct"
        fi
    fi
done

echo ""
echo "--- Latest Log Activity ---"
echo ""
tail -10 /Users/teije/Desktop/memagent-modular-fixed/tesseract_metadata_extraction_v2.log | grep -E "Processing|Results:|Successful:|Failed:|Found"

echo ""
echo "=================================="
echo "Run 'tail -f tesseract_metadata_extraction_v2.log' for real-time updates"
echo "=================================="
