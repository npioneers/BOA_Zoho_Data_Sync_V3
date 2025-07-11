# MANUAL MAPPING INSTRUCTIONS FOR AI AGENT

## 🎯 MISSION OBJECTIVE
Manually review and improve ALL field mappings in `map_json_*` tables using domain knowledge and business logic to ensure accurate data synchronization between CSV and JSON sources.
*** It is a manual mapping task for you. It required your direct involvement. you can create tools to assist though. the updates has to be done you you alone for this exercise. ***

## 📋 CORE REQUIREMENTS

### 🚨 CRITICAL RULE (NON-NEGOTIABLE)
**ONLY ONE CSV_field CAN BE MAPPED TO EACH JSON FIELD - NO DUPLICATES ALLOWED**

### 📊 MAPPING QUALITY CATEGORIES
Categorize every field mapping as:
- **✅ Perfect:** Exact semantic match with correct data type
- **✅ Good:** Semantically correct with minor differences
- **⚠️ Questionable:** Unclear semantic relationship or data type mismatch
- **❌ Unmapped:** JSON field has no CSV mapping

### 🚨 CRITICAL ISSUES TO FLAG
1. **Duplicate Mappings:** Multiple JSON fields mapped to same CSV field
2. **Missing Mappings:** Unmapped JSON fields that have available CSV data
3. **Semantic Mismatches:** Incorrectly mapped fields (e.g., name → id)
4. **Data Loss Risk:** CSV data available but JSON field unmapped

## 🛠️ ANALYSIS TOOLS CREATED

### 1. **comprehensive_mapping_analyzer.py** (PRIMARY ANALYSIS TOOL)
**Purpose:** Complete mapping quality assessment with duplicate detection
**Usage:**
```bash
python comprehensive_mapping_analyzer.py
```
**Output:**
- Categorizes all 835 fields across 16 tables
- Detects duplicate mapping violations
- Flags critical issues requiring attention
- Generates comprehensive reports

### 2. **duplicate_mapping_resolver.py** (DUPLICATE FIXER)
**Purpose:** Resolve duplicate mapping violations using domain knowledge
**Usage:**
```bash
python duplicate_mapping_resolver.py
```
**Features:**
- Applies intelligent selection rules (exact matches, names > IDs, etc.)
- Clears inappropriate duplicates while preserving best mappings
- Updates CSV_data_count accurately
- Generates detailed correction logs

### 3. **critical_issues_analyzer.py** (ISSUE IDENTIFIER)
**Purpose:** Identify unmapped fields with available CSV data
**Usage:**
```bash
python critical_issues_analyzer.py
```
**Output:**
- Flags fields at risk of data loss
- Prioritizes issues by data volume
- Suggests mapping candidates

### 4. **manual_mapping_corrector.py** (MANUAL CORRECTION TOOL)
**Purpose:** Apply specific mapping corrections with full logging
**Usage:**
```bash
python manual_mapping_corrector.py
```
**Features:**
- Interactive or batch correction mode
- Complete before/after logging
- CSV_data_count synchronization

### 5. **post_correction_analyzer.py** (VALIDATION TOOL)
**Purpose:** Verify mapping quality after corrections
**Usage:**
```bash
python post_correction_analyzer.py
```
**Output:**
- Quality score calculation
- Improvement metrics
- Remaining issues identification

## 📋 STEP-BY-STEP PROCESS

### Phase 1: Assessment (COMPLETED ✅)
1. Run `comprehensive_mapping_analyzer.py` to assess current state
2. Identify duplicate violations and critical issues
3. Categorize all mappings by quality

### Phase 2: Rule Compliance (COMPLETED ✅)
1. Run `duplicate_mapping_resolver.py` to fix duplicate violations
2. Verify zero duplicate mappings remain
3. Ensure one-to-one CSV-to-JSON mapping compliance

### Phase 3: Mapping Completion (NEXT PRIORITY)
1. Use `critical_issues_analyzer.py` to identify unmapped fields with CSV data
2. Apply domain knowledge to create appropriate mappings
3. Use `manual_mapping_corrector.py` to implement corrections
4. Update CSV_data_count from corresponding map_csv_* tables

### Phase 4: Quality Review
1. Review questionable mappings for semantic accuracy
2. Test mappings with sample data
3. Run `post_correction_analyzer.py` for final validation

## 🧠 DOMAIN KNOWLEDGE RULES

### Field Mapping Priorities
1. **Exact Matches:** JSON field name = CSV field name
2. **Semantic Matches:** Fields with same business meaning
3. **Data Type Consistency:** Matching data types and formats
4. **Name over ID:** Prefer name fields over ID fields when both available
5. **Unformatted over Formatted:** Prefer raw data over formatted versions

### Business Logic Guidelines
- **Time Fields:** created_time > created_timestamp > created_by
- **Status Fields:** main status > sub_status > formatted_status
- **Currency:** currency_code > currency_id > currency_symbol
- **Templates:** template_name > template_id > template_type
- **Accounts:** account_name > account_code > account_id

## 📊 CURRENT STATUS (as of July 8, 2025)

### ✅ COMPLETED
- **Duplicate Mappings:** 178 → 0 (100% RESOLVED)
- **Rule Compliance:** 100% adherent to one-to-one mapping
- **Analysis Tools:** All 5 tools created and tested
- **Corrections Applied:** 329 total corrections

### 📋 REMAINING WORK
- **Unmapped Fields:** 463 fields with available CSV data need mapping
- **Questionable Mappings:** 124 fields need semantic review
- **Quality Score:** Currently 29.7% (will improve as unmapped fields are addressed)

## 📁 FILE LOCATIONS
- **Analysis Scripts:** `json_db_mapper/manual_ai_analysis/`
- **Reports:** `json_db_mapper/manual_ai_analysis/`
- **Database:** `data/database/production.db`
- **CSV Reference:** `map_csv_*` tables contain field data counts

## 🎯 SUCCESS CRITERIA
1. **Zero duplicate mappings** (✅ ACHIEVED)
2. **All unmapped fields with CSV data are mapped**
3. **Quality score > 80%**
4. **All questionable mappings reviewed and justified**
5. **Complete audit trail of all changes**

## 📝 REPORTING REQUIREMENTS
- Log all changes with before/after values
- Update CSV_data_count for all modified mappings
- Generate comprehensive mapping quality report
- Document rationale for questionable mappings
- Create final compliance certification

---
**NOTE:** This is manual review work requiring AI domain knowledge and judgment. Tools assist with analysis and implementation, but mapping decisions require intelligent evaluation of semantic relationships and business logic.