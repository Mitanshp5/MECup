# RAG Accuracy Improvements

## Changes Made to Boost Accuracy from 60% to 90%+

### 1. **Query Expansion** (agent.py)
- **Before**: Single query sent to vector DB
- **After**: Generate 3 variations per query
  - Error codes: "error code X", "fault X", "alarm X"
  - Troubleshooting: "troubleshoot X", "fix X", "resolve X"
  - How-to: "procedure X", "steps X"
- **Impact**: Catches documents that use different terminology

### 2. **Increased Retrieval Depth** (agent.py)
- **Before**: `k=3` (only 3 chunks retrieved)
- **After**: `k=6` (6 chunks retrieved)
- **Before**: `fetch_k=6` (candidate pool)
- **After**: `fetch_k=12` (larger candidate pool)
- **Impact**: More context available for LLM to work with

### 3. **Lower Relevance Threshold** (agent.py)
- **Before**: `threshold=0.25` (strict filtering)
- **After**: `threshold=0.15` (more inclusive)
- **Impact**: Catches marginally relevant chunks that might contain the answer

### 4. **Larger Chunks with More Overlap** (rebuild_vectordb.py)
- **Before**: `chunk_size=400`, `overlap=80`
- **After**: `chunk_size=600`, `overlap=150`
- **Impact**: 
  - Each chunk contains more complete context
  - Higher overlap prevents information loss at chunk boundaries
  - Better continuity for multi-sentence explanations

### 5. **Better Query Classification** (agent.py)
- **Before**: Simple keyword matching
- **After**: Regex patterns + comprehensive keyword lists
- **Query Types**: error_code, troubleshooting, how_to, info, general, greeting, vague
- **Impact**: More accurate prompt selection per query type

### 6. **Improved Prompts** (agent.py)
- **Before**: Generic troubleshooting format for all queries
- **After**: Specialized HTML templates per query type
  - Error codes → Error details + cause + solution
  - Troubleshooting → Issue + diagnostic steps
  - How-to → Procedure + notes
  - Info → Concise explanation
- **Impact**: LLM generates more relevant responses

### 7. **Increased LLM Token Budget** (agent.py)
- **Before**: `num_predict=512`
- **After**: `num_predict=600`
- **Impact**: LLM can generate more detailed, complete answers

## How to Apply These Improvements

### Step 1: Rebuild Vector Database
```bash
cd backend/production_rag
python rebuild_vectordb.py
```
This will re-chunk all PDFs with the new settings (600 char chunks, 150 overlap).

### Step 2: Test the Improved Agent
```bash
python test_accuracy.py
```

### Step 3: Run with Main Server
```bash
cd ../..
npm run dev
```

The improved agent will auto-load at `http://localhost:5001/api/troubleshoot`

## Expected Results

| Metric | Before | After |
|--------|--------|-------|
| Accuracy | 60% (3/5) | 90%+ (4.5/5) |
| Avg Chunks Retrieved | 3 | 6 |
| Context per Chunk | 400 chars | 600 chars |
| Query Variations | 1 | 3 |
| Relevance Threshold | 0.25 (strict) | 0.15 (inclusive) |

## Additional Recommendations

### If Accuracy is Still Below 90%:

1. **Check PDF Quality**
   - Are PDFs scanned images? (OCR quality affects text extraction)
   - Are PDFs password-protected or corrupted?
   - Run: `python -c "from pypdf import PdfReader; print(PdfReader('data/your.pdf').pages[0].extract_text())"`

2. **Manually Review Problem Queries**
   - Which 2 queries are failing?
   - Are they asking about content that doesn't exist in PDFs?
   - Are they using very different terminology?

3. **Further Tuning Options**:
   ```python
   # In agent.py, try:
   TOP_K = 8  # Even more chunks
   RELEVANCE_THRESHOLD = 0.10  # Even more inclusive
   
   # In rebuild_vectordb.py, try:
   chunk_size=800  # Larger chunks
   chunk_overlap=200  # More overlap
   ```

4. **Add Domain-Specific Preprocessing**
   - Extract error code tables separately
   - Create dedicated sections for common issues
   - Add synonyms/aliases for technical terms

5. **Hybrid Search** (Advanced)
   - Combine semantic search with keyword search
   - Requires additional setup with BM25

## Backup & Rollback

Old agent backed up as: `agent_old_backup.py`

To rollback:
```bash
copy agent_old_backup.py agent.py
```

## Testing Checklist

- [ ] Rebuild vector database with new chunking
- [ ] Test 5 sample queries
- [ ] Check source citations are present
- [ ] Verify HTML formatting is correct
- [ ] Measure accuracy improvement
- [ ] Test with `npm run dev` integration
