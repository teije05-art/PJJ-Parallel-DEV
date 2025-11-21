# KPMG Tax Team Workflow Analysis & Jupiter Enhancement

**Prepared for**: Partner Meeting on Nov 20, 2025
**Purpose**: Understand current workflow + propose Jupiter integration
**Outcome Goal**: Clear requirements for implementation

---

## CURRENT KPMG TAX WORKFLOW (3 Steps)

### Step 1: Topic Classification
```
CLIENT QUESTION ARRIVES
│
├─ Example: "How is capital gains tax calculated for share transfer transactions?"
├─ Tax professional reads/listens to question
├─ Classifies into topic category
│  (e.g., "Corporate Tax", "Capital Gains", "International", etc.)
│
└─ Output: Topic classification for next step
```

**Questions to Ask the Partner:**
- How are topics classified? Is there a standardized list?
- Is this done consistently across all team members?
- Could a client question map to multiple topics?
- How much time does this step typically take?

---

### Step 2: Relevant Document Search
```
TOPIC CLASSIFIED
│
├─ Goes to SharePoint Online
├─ Searches manually for documents containing:
│  • Topic keywords ("capital gains", "share transfer")
│  • Relevant regulations
│  • KPMG advice letters
│  • Official guidance
│
├─ Method: Mix of automated search + manual folder browsing
├─ Result: Returns 10-50+ documents (varies)
├─ Challenge: Finding "truly relevant" docs among many results
│
└─ Output: Curated list of relevant source documents
```

**Questions to Ask the Partner:**
- On average, how many documents are reviewed per query?
- How long does the search typically take?
- What makes a document "relevant" vs "not relevant"?
- Are documents tagged with metadata? (e.g., date, category, confidence level)
- Do you ever miss important documents?
- Are some documents searched more frequently? (Could indicate patterns)

---

### Step 3: Response Compilation & Building
```
RELEVANT DOCUMENTS COLLECTED
│
├─ Tax professional reviews all docs
├─ Extracts key information
├─ Considers multiple perspectives
├─ Ensures consistency with KPMG position
│
├─ Response building approach:
│  ├─ Copy key passages from source documents
│  ├─ Synthesize information from multiple sources
│  ├─ Apply legal reasoning/interpretation
│  ├─ Format professionally with citations
│  └─ Quality check for accuracy
│
├─ Output format: Professional response document
│  • What client should do / not do
│  • Relevant regulations cited
│  • KPMG recommendations
│  • Risk considerations
│  • Timeline / next steps
│
└─ Delivered to Client
```

**Questions to Ask the Partner:**
- Who writes the final response? (Same person who searched, or someone else?)
- What's the typical length/depth of a response?
- Are responses reviewed/approved by anyone? (Quality control process?)
- What format do clients expect? (Memo, analysis, presentation, etc.)
- How long does Step 3 typically take per question?
- Are there common response templates you use?

---

## PAIN POINTS IN CURRENT WORKFLOW

**Suspected Pain Points** (to validate with partner):

1. **Time-Intensive Search**
   - Manual SharePoint search + folder browsing is slow
   - Multiple queries needed to find all relevant docs
   - Easy to miss important documents

2. **Inconsistent Results**
   - Different team members may search differently
   - Same question could have different results depending on who searches
   - Keyword matching may miss conceptually relevant docs

3. **Repetitive Work**
   - Similar questions asked by different clients
   - Each requires starting from scratch (no pattern learning)
   - No system for capturing "how we typically answer X"

4. **Knowledge Bottleneck**
   - Depends on individual team member expertise
   - New team members take longer to find right docs
   - Senior tax professionals' time is expensive/scarce

5. **Quality Variance**
   - Depends on how thorough the search was
   - No consistency check across responses
   - Compilation quality varies by person

6. **No Learning Loop**
   - Same searches repeated by different people
   - Successful approaches not captured systematically
   - Errors not prevented for next similar question

---

## HOW JUPITER ENHANCES THIS WORKFLOW

### The Transformation

```
CURRENT (Manual):                    JUPITER-ENHANCED:
─────────────────────────           ──────────────────────────
Client Question                      Client Question
    ↓                                    ↓
Manual Classification                Guided Classification
    ↓                                (or auto-classification)
Manual Search (30-60 min)            Automated Search (<1 min)
    ↓                                    ↓
Manual Compilation (30-60 min)       AI Synthesis (1-2 min)
    ↓                                    ↓
Response                             Response with:
                                     • Full audit trail
                                     • Source citations
                                     • Confidence scores
                                     ↓
                                     PARTNER REVIEW
                                     (Quick approval)
                                     ↓
                                     Response + Learning
                                     System captures patterns
```

**Time Saved**: 60-120 minutes → 5-10 minutes (10-20x improvement)

---

## JUPITER'S ROLE IN EACH STEP

### Step 1: Enhanced Classification
**Jupiter's Role**: Support consistent classification

```
Approach 1 (If manual classification preferred):
• Streamlit interface with dropdown of standard topics
• User selects topic(s)
• System records selection for learning

Approach 2 (If auto-classification preferred):
• User enters client question
• Jupiter analyzes question
• Suggests topic classification
• User confirms or corrects
```

**Benefit**: Consistency across all responses

---

### Step 2: Intelligent Document Retrieval (THE BIG AUTOMATION)

**Jupiter's Role**: Automate and enhance the search

```
Current Process:                 Jupiter Process:
─────────────────               ────────────────
1. Think of keywords            1. Understand topic/question
2. Search SharePoint            2. Query entire database semantically
3. Browse folders manually       3. Rank documents by relevance
4. Review 20-50 docs            4. Auto-rank top 10-15 most relevant
5. Curate results               5. Instant ready-to-use set

HOW IT WORKS:
━━━━━━━━━━━━━
Your Database (KPMG PDFs, CSVs, Excel files)
    ↓ (Import once)
Local Memory System
    ├─ All docs searchable
    ├─ Semantic understanding (not just keywords)
    └─ Organized by type/topic/date

User Selects Topic
    ↓
Jupiter queries with:
    ├─ Topic keywords
    ├─ Related concepts (legal, regulatory, industry)
    └─ Historical patterns (what worked for similar questions)

System Returns:
    ├─ Top 15 most relevant documents
    ├─ Relevance scores
    ├─ Why each doc was selected
    └─ Ready for next step

Time: ~30-60 seconds (vs. manual 30-60 minutes)
Quality: Finds docs humans might miss
Consistency: Same approach every time
```

**Benefits**:
- No missed documents (searches entire database semantically)
- Faster (automated vs. manual browsing)
- Consistent (same logic every time)
- Traceable (can see why docs were selected)

---

### Step 3: Intelligent Response Synthesis (THE QUALITY ENHANCER)

**Jupiter's Role**: Synthesize response from retrieved documents

```
Current Process:                 Jupiter Process:
─────────────────               ────────────────
1. Read all 20-50 docs          1. Receives top 15 docs
2. Extract key points           2. AI synthesizes response
3. Write analysis               3. Organizes by topic
4. Cite sources                 4. Cites all sources
5. Format professionally        5. Formats professionally
6. Send to partner for review   6. Sends to partner for review

TIME: 30-60 minutes              TIME: 2-5 minutes

QUALITY IMPROVEMENTS:
━━━━━━━━━━━━━━━━━━━━━
✓ Consistent structure (same format every time)
✓ Never misses source (all docs analyzed)
✓ Better organization (AI synthesizes relationships)
✓ Clearer logic (connects points across docs)
✓ Complete citations (every claim tracked to source)
✓ Risk assessment (flags contradictions or gaps)
✓ Learning loop (system learns what works)
```

**Output Format** (customizable to KPMG preferences):
```markdown
# Tax Analysis: [Topic]

## Executive Summary
[Jupiter's synthesis of the answer]

## Relevant Regulations & Guidance
### Regulation 1
- Source: [Document name]
- Key Point: [Citation]
- Applies Because: [Reasoning]

### Regulation 2
- Source: [Document name]
- Key Point: [Citation]
- Applies Because: [Reasoning]

## KPMG Analysis & Recommendation
[Synthesized analysis from all sources]

## Risk Considerations
[Potential issues flagged by synthesis]

## Next Steps
[Recommended actions]

## Sources Reviewed
- Document 1 (Relevance: High)
- Document 2 (Relevance: High)
- ...
```

---

## END-TO-END FLOW WITH JUPITER

```
CLIENT QUESTION ARRIVES
│
├─ Email/Phone/Form: "How is capital gains tax calculated for share transfers?"
│
├─ Tax Professional using Jupiter:
│  1. Opens Jupiter Streamlit interface
│  2. Enters client question
│  3. Selects topic: "Corporate Tax - Capital Gains"
│  4. Selects memory scope: "Shared" (departmental knowledge)
│  5. Confirms: "Search for relevant documents and draft response"
│
├─ Jupiter Automated Search (1 minute)
│  ├─ Searches entire KPMG database
│  ├─ Returns top 12 most relevant documents:
│  │  • 3 official tax regulations
│  │  • 2 KPMG advice letters on similar transactions
│  │  • 4 previous client analysis memos
│  │  • 3 court rulings/guidance documents
│  └─ Ranking shown with relevance scores
│
├─ Jupiter AI Synthesis (3-5 minutes)
│  ├─ Reads all 12 documents
│  ├─ Synthesizes comprehensive response
│  ├─ Organizes by key topics
│  ├─ Cites every source
│  └─ Flags any contradictions or gaps
│
├─ Partner Review & Approval (5-10 minutes)
│  ├─ Reviews Jupiter's analysis
│  ├─ Can approve as-is, or request modifications
│  ├─ If approved: System records this as a success
│  ├─ Learning captured: "For capital gains + share transfer, use these docs"
│  └─ Response sent to client
│
├─ System Learning (automatic)
│  ├─ Next time someone asks about capital gains
│  ├─ Jupiter will remember: "We successfully used these 12 docs"
│  ├─ Will recommend similar docs automatically
│  ├─ Response quality improves over time
│  └─ New team members get same quality as senior staff
│
└─ RESULT:
   ✓ 10-15 min total (vs. 2-3 hours manual)
   ✓ Comprehensive (all docs considered)
   ✓ Professional (consistent format)
   ✓ Traceable (complete audit trail)
   ✓ Improving (system learns)
```

---

## REQUIRED INPUTS FROM KPMG

For Jupiter to work, we need:

1. **Database Files** (You have this!)
   - All PDFs, CSVs, Excel files with tax/legal information
   - Organized into local-memory/entities/ directory
   - Tagged with metadata (optional but helpful)

2. **Workflow Details**
   - How topics are classified (list of standard topics)
   - What format responses should be in
   - Who approves final response?
   - Any compliance requirements?

3. **Integration Points**
   - Does this need to integrate with existing systems?
   - Do responses get sent through a specific tool/process?
   - Any security/access control requirements?

4. **Success Metrics**
   - What does "success" look like?
   - Time savings target?
   - Quality metrics?
   - User adoption goals?

---

## PROPOSAL: 3-PHASE IMPLEMENTATION

### Phase 1: Database Import & Setup (3-5 days)
- Import KPMG database files into local-memory system
- Organize documents by topic/type
- Index for semantic search
- Tag with metadata for learning

### Phase 2: Integration Testing (5-7 days)
- Test with 10-15 real client questions
- Validate response quality
- Get KPMG team feedback
- Refine as needed

### Phase 3: Approval Gate Setup & Launch (3-5 days)
- Configure approval workflow (who reviews, how?)
- Train team on Jupiter interface
- Go live with pilot group
- Monitor and optimize

**Total Timeline**: 2-3 weeks to full launch

**Success Indicator**:
- Responses taking <15 min vs. 2-3 hours
- Same or better quality
- Team adoption rate >80%

---

## KEY VALUE PROPOSITIONS FOR THE PARTNER

1. **Dramatic Time Savings**
   - Current: 60-120 min per question
   - With Jupiter: 5-15 min per question
   - Savings: 8-10 hours per day for small team

2. **Quality Improvement**
   - Consistent approach every time
   - No missed documents
   - Better synthesis of complex information
   - Full audit trail

3. **Scalability**
   - Same 5 professionals can handle 3-5x more questions
   - No need to hire more staff
   - Especially valuable during busy seasons

4. **Knowledge Preservation**
   - System learns from each successful response
   - New team members perform like senior staff
   - Reduces dependency on key individuals
   - Institutional memory preserved

5. **Compliance & Risk**
   - Complete audit trail (who reviewed what)
   - Consistency check across responses
   - Source documentation always available
   - Reduces liability from missed regulations

6. **Competitive Advantage**
   - Faster turnaround = happier clients
   - Better quality = fewer revision requests
   - Can take on more clients
   - Positions KPMG as innovative

---

## QUESTIONS FOR THE PARTNER

**To Ask During the Meeting:**

### About Current Workflow
- [ ] Walk me through your last client question - how long did the whole process take?
- [ ] How many documents did you review to find the answer?
- [ ] Is the search process always the same, or does it vary?
- [ ] What makes a document "relevant" in your field?

### About the Team
- [ ] How many tax professionals spend time on this search-and-compile work?
- [ ] How much of their day is spent searching vs. analyzing?
- [ ] Do you find that different people get different results for the same question?
- [ ] Are there documents you search for repeatedly?

### About the Database
- [ ] How are your documents currently organized?
- [ ] Do they have metadata (date, type, topic)?
- [ ] How frequently is the database updated?
- [ ] Approximately how many documents are in the database?

### About Quality & Approval
- [ ] How do you ensure responses are accurate and complete?
- [ ] Who reviews the final response before it goes to the client?
- [ ] Are there any responses that were wrong/incomplete?
- [ ] How do you currently prevent repeating past mistakes?

### About Pain Points
- [ ] If you could automate one part of this process, what would it be?
- [ ] What's the biggest bottleneck right now?
- [ ] What would make this process easier?
- [ ] Are there clients complaining about turnaround time?

### About Implementation
- [ ] What would success look like for you?
- [ ] What's your timeline for implementation?
- [ ] Who would be the main users? How many people?
- [ ] What security/compliance requirements do we need to meet?
- [ ] Do you need integration with SharePoint or other systems?

---

## NEXT STEPS AFTER MEETING

1. **Document Requirements** (today/tomorrow)
   - Write down everything the partner told you
   - Clarify any ambiguous points via email
   - Get sign-off on requirements

2. **Create Implementation Plan** (tomorrow)
   - Specific Phase 1, 2, 3 timelines
   - Resource needs (your time, KPMG time)
   - Success metrics and measurements

3. **Start Database Import** (immediately after requirements finalized)
   - Import KPMG files into local-memory
   - Begin testing with real questions
   - Get feedback from tax team early and often

4. **Keep Partner Informed** (weekly updates)
   - Progress on import
   - Early test results
   - Any blockers or questions

---

**Good luck with the meeting! You've got this.**
