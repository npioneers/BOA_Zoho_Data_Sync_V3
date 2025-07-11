# AI AGENT PROCESS CHECKLIST

## 📋 MANDATORY STEPS FOR MAPPING ANALYSIS

### ✅ PRE-FLIGHT CHECK
- [ ] Verify database connection: `data/database/production.db`
- [ ] Confirm all 16 map_json_* tables exist
- [ ] Check working directory: `json_db_mapper/manual_ai_analysis/`
- [ ] Validate Python environment and dependencies

### 🔍 PHASE 1: ASSESSMENT
- [ ] Run `comprehensive_mapping_analyzer.py`
- [ ] Review generated reports for current state
- [ ] Document baseline metrics:
  - Total fields: ___
  - Perfect mappings: ___
  - Duplicate violations: ___
  - Quality score: ___%

### 🚨 PHASE 2: RULE COMPLIANCE (✅ COMPLETED)
- [x] Check for duplicate mapping violations
- [x] Run `duplicate_mapping_resolver.py` if needed
- [x] Verify zero duplicate mappings remain
- [x] Confirm one-to-one CSV-to-JSON mapping compliance

### 🎯 PHASE 3: CRITICAL ISSUE RESOLUTION
- [ ] Run `critical_issues_analyzer.py`
- [ ] Prioritize unmapped fields by CSV data volume
- [ ] Focus on fields with >1000 records first
- [ ] Use `manual_mapping_corrector.py` for high-impact fixes

### 📊 PHASE 4: SYSTEMATIC MAPPING
For each table with unmapped fields:
- [ ] Analyze JSON field semantics
- [ ] Check available CSV field options
- [ ] Apply domain knowledge rules
- [ ] Update mapping using corrector tool
- [ ] Verify CSV_data_count synchronization

### ✅ PHASE 5: QUALITY REVIEW
- [ ] Run `post_correction_analyzer.py`
- [ ] Check quality score improvement
- [ ] Review questionable mappings
- [ ] Validate semantic accuracy

### 📝 PHASE 6: DOCUMENTATION
- [ ] Generate final mapping report
- [ ] Document all changes made
- [ ] Update instruction files if needed
- [ ] Commit changes to version control

## 🧠 DECISION MATRIX FOR MAPPING

### HIGH PRIORITY (Map Immediately)
✅ **Exact Name Match**
- JSON: `customer_name` → CSV: `customer_name`

✅ **Clear Semantic Match**  
- JSON: `invoice_date` → CSV: `bill_date`

### MEDIUM PRIORITY (Review & Map)
⚠️ **Partial Name Match**
- JSON: `customer_id` → CSV: `customer_identifier`

⚠️ **Type Similar**
- JSON: `total_amount` → CSV: `amount_total`

### LOW PRIORITY (Manual Review)
❌ **Unclear Relationship**
- JSON: `status` → CSV: `workflow_stage`

❌ **Data Type Mismatch**
- JSON: `created_date` → CSV: `created_timestamp`

## 🚫 NEVER MAP THESE
- Different business concepts (customer_name → vendor_name)
- Wrong data types (date → text fields)
- Deprecated/legacy fields
- Empty or null CSV fields

## 🎯 QUALITY GATES

### GATE 1: Rule Compliance
- ✅ Zero duplicate mappings
- ✅ No multiple JSON fields → same CSV field

### GATE 2: Coverage 
- 📋 >90% of JSON fields with CSV data have mappings
- 📋 <10% unmapped fields remain

### GATE 3: Quality
- 📋 >80% overall quality score
- 📋 <5% questionable mappings
- 📋 All questionable mappings documented/justified

### GATE 4: Validation
- 📋 Sample data testing passes
- 📋 No data type conflicts
- 📋 Business logic validation complete

## 🚨 ESCALATION TRIGGERS

### STOP & REVIEW IF:
- Quality score decreases after corrections
- Duplicate mappings reappear
- CSV_data_count mismatches occur
- Database constraint violations happen

### IMMEDIATE ATTENTION REQUIRED:
- Any mapping that could cause data loss
- Business-critical fields left unmapped
- Contradictory field relationships
- System performance impacts

## 📊 SUCCESS METRICS TRACKING

### **CURRENT STATUS (July 8, 2025):**
- **Total Fields:** 835
- **Perfect Mappings:** 140 (16.8%)
- **Good Mappings:** 108 (12.9%) 
- **Questionable:** 124 (14.9%)
- **Unmapped:** 463 (55.4%)
- **Duplicate Violations:** 0 ✅
- **Quality Score:** 29.7%

### **TARGET METRICS:**
- **Perfect + Good:** >80% (currently 29.7%)
- **Unmapped:** <10% (currently 55.4%)
- **Questionable:** <5% (currently 14.9%)
- **Duplicates:** 0 (achieved ✅)

## 🔄 ITERATIVE IMPROVEMENT CYCLE

1. **Analyze** → Run comprehensive analyzer
2. **Prioritize** → Focus on highest-impact unmapped fields  
3. **Map** → Apply domain knowledge corrections
4. **Validate** → Check quality improvements
5. **Repeat** → Until quality targets achieved

**REMEMBER:** Each iteration should show measurable quality improvement!
