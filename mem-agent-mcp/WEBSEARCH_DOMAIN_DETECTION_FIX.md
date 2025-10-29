# WebSearch Domain Detection Fix

## Problem Identified

When running planning iterations for non-tech domains (like a coffee company), the system was returning 80+ technology-oriented URLs instead of relevant market research for the actual industry.

### Root Cause

The goal analyzer's domain detection was **too simplistic and context-unaware**:

```python
# OLD LOGIC (INCORRECT)
'technology': [
    r'startup',  ← This pattern matched ANY use of "startup"
    r'SaaS', r'platform', r'digital', ...
]
```

When you said **"Coffee startup entering Vietnam"**, the system saw the word **"startup"** and classified it as a technology domain, leading to web searches for:
- "technology market size 2025" ❌
- "technology competitors" ❌
- "tech trends 2025" ❌

Instead of:
- "qsr market size 2025" ✅
- "coffee industry trends" ✅
- "restaurant market analysis" ✅

## Solution Implemented

### New Context-Aware Detection (3-Step Process)

**1. Primary Industry Keywords (High Weight)**
- Specific, domain-defining keywords with higher weights
- Examples:
  - Healthcare: "clinical", "pharmaceutical", "FDA", "medical device"
  - Technology: "software", "AI", "machine learning", "algorithm"
  - QSR: "restaurant", "cafe", "coffee shop", "beverage", "cuisine"
  - Manufacturing: "assembly", "production line", "factory setup"

**2. Contextual Modifiers (Mid Weight)**
- Words that clarify compound phrases
- Example: "coffee startup"
  - "coffee" is a QSR contextual modifier → boosts QSR score
  - "startup" alone is secondary → lower weight
  - Result: QSR wins ✅

**3. Fallback Patterns (Low Weight)**
- Simple pattern matching only if no primary keywords found
- Used as last resort for edge cases

### Code Changes

**File**: `/Users/teije/Desktop/memagent-modular-fixed/mem-agent-mcp/orchestrator/goal_analyzer.py`

**Changes**:
1. Added `primary_industry_patterns` dictionary with domain-specific keywords
2. Added `contextual_modifiers` dictionary for compound phrase clarification
3. Added `pattern_weights` to distinguish between strong and weak indicators
4. Refactored `_detect_domain()` method with 4-step weighted scoring
5. Refactored `_detect_industry()` method with same approach
6. Updated domain_patterns and industry_patterns lists to include QSR keywords

### Before & After Examples

| Goal | Old Detection | New Detection | Web Search |
|------|--------------|---------------|-----------|
| "Coffee startup entering Vietnam" | ❌ Technology | ✅ QSR | qsr market size, restaurant trends, coffee industry |
| "Coffee brand expansion to Southeast Asia" | ❌ Technology | ✅ Retail | retail market size, consumer trends, brand analysis |
| "Tech startup expanding to Vietnam" | ✅ Technology | ✅ Technology | technology market, startup ecosystem, digital innovation |
| "AI startup market entry" | ✅ Technology | ✅ Technology | AI market size, machine learning trends, tech innovation |
| "Healthcare company in Vietnam" | ✅ Healthcare | ✅ Healthcare | healthcare regulations, medical market, clinical trials |

## Why This Fix Is Better

### ✅ Context-Aware
- Understands that "coffee startup" is QSR, not technology
- Recognizes "AI startup" is definitely technology
- Differentiates based on actual domain keywords, not just generic modifiers

### ✅ Weighted Scoring
- Primary industry keywords get 3x weight
- Contextual modifiers get 2x weight
- Fallback patterns get 1x weight
- Prevents generic terms from overriding specific ones

### ✅ Extensible
- Easy to add new domains (just add primary_industry_patterns and contextual_modifiers)
- Easy to adjust weights if needed
- Clear structure makes it maintainable

### ✅ Backwards Compatible
- Existing QSR functionality still works
- Healthcare/Tech/Manufacturing domains still work correctly
- No breaking changes to other parts of the system

## Testing Results

All test cases pass correctly:

```
✅ Coffee company → QSR
✅ Coffee startup → QSR
✅ Coffee shop chain → QSR
✅ Tech startup → Technology
✅ AI startup → Technology
✅ Healthcare company → Healthcare
✅ Manufacturing facility → Manufacturing
```

## How Web Search Is Now Improved

With correct domain detection, the web search will now:

1. **Generate relevant queries** based on actual industry, not false positives
2. **Return appropriate URLs** from coffee/restaurant industry sites instead of tech sites
3. **Provide accurate market data** for planning (coffee trends, QSR growth, etc.)
4. **Support better planning** with real-world research relevant to the domain

## Files Modified

- `orchestrator/goal_analyzer.py` - Core domain detection logic
  - Added primary industry keyword patterns
  - Added contextual modifiers
  - Refactored detection methods with weighted scoring
  - Maintained backwards compatibility

## Impact

This fix ensures that the entire planning pipeline gets the correct domain context from the start:

```
Correct Domain Detection
    ↓
Correct Web Search Queries
    ↓
Relevant Market Research
    ↓
Domain-Appropriate Planning Templates
    ↓
High-Quality Plans ✅
```

Without this fix, the system would have continued returning irrelevant technology research for coffee/retail/manufacturing companies.

## Future Improvements

The architecture now supports:
- Adding new domains easily
- Adjusting pattern weights for better accuracy
- Adding exclusion patterns for edge cases
- Machine learning based refinement of patterns over time

---

**Fix Date**: October 27, 2025
**Status**: ✅ Complete and Tested
