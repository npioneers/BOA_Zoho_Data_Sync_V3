# MAPPING ANALYSIS TOOLS REFERENCE

## 📋 TOOL INVENTORY & USAGE GUIDE

### 🔍 **comprehensive_mapping_analyzer.py** - PRIMARY ANALYSIS ENGINE
**Purpose:** Complete mapping quality assessment and rule compliance check
**Last Updated:** July 8, 2025

#### Features:
- ✅ Analyzes all 835 fields across 16 mapping tables
- ✅ Categorizes: Perfect, Good, Questionable, Unmapped
- ✅ Detects duplicate mapping violations (one-to-one rule)
- ✅ Flags critical issues (unmapped fields with CSV data)
- ✅ Generates comprehensive quality reports

#### Usage:
```bash
python comprehensive_mapping_analyzer.py
```

#### Outputs:
- `comprehensive_mapping_report_YYYYMMDD_HHMMSS.md` - Detailed findings
- `comprehensive_mapping_analysis_YYYYMMDD_HHMMSS.json` - Structured data
- Console summary with quality metrics

#### Example Output:
```
📊 OVERALL ANALYSIS SUMMARY
📋 Total fields analyzed: 835
🎯 Perfect mappings: 140
✅ Good mappings: 108
⚠️ Questionable mappings: 124
❌ Unmapped fields: 463
🔄 Duplicate mappings: 0
🚨 Critical issues: 574
📈 Quality score: 29.7%
```

---

### 🔧 **duplicate_mapping_resolver.py** - DUPLICATE VIOLATION FIXER
**Purpose:** Resolve duplicate CSV field mappings using domain knowledge
**Status:** Mission completed - 178 duplicates resolved to 0

#### Features:
- ✅ Intelligent mapping selection using business rules
- ✅ Domain knowledge prioritization (names > IDs, exact matches, etc.)
- ✅ Automatic CSV_data_count synchronization
- ✅ Complete correction logging and reporting

#### Usage:
```bash
python duplicate_mapping_resolver.py
```

#### Domain Knowledge Rules Applied:
- **Exact Matches:** Prefer JSON fields matching CSV field names
- **Time Fields:** created_time > created_timestamp > created_by
- **Status Fields:** Main status > sub_status > formatted_status
- **Currency:** currency_code > currency_id > currency_symbol
- **Names:** Always prefer name fields over ID fields

#### Outputs:
- `duplicate_resolution_report_YYYYMMDD_HHMMSS.md` - Correction details
- `duplicate_resolution_log_YYYYMMDD_HHMMSS.json` - Structured corrections
- Database updates with corrected mappings

---

### 🚨 **critical_issues_analyzer.py** - DATA LOSS RISK IDENTIFIER
**Purpose:** Identify unmapped JSON fields that have available CSV data
**Use Case:** Prevent data loss by finding mapping gaps

#### Features:
- ✅ Scans all JSON fields for missing CSV mappings
- ✅ Checks CSV data availability and volume
- ✅ Prioritizes issues by data count (highest impact first)
- ✅ Suggests potential mapping candidates

#### Usage:
```bash
python critical_issues_analyzer.py
```

#### Outputs:
- `critical_issues_report_YYYYMMDD_HHMMSS.md` - Prioritized issues list
- `critical_issues_analysis_YYYYMMDD_HHMMSS.json` - Structured findings
- Console summary of critical mappings needed

#### Example Output:
```
🚨 CRITICAL: has_attachment - UNMAPPED but CSV data available
📊 Available CSV fields with data:
   - created_timestamp: 3097 records
   - updated_timestamp: 3097 records  
   - bill_date: 3097 records
```

---

### ✏️ **manual_mapping_corrector.py** - PRECISION CORRECTION TOOL
**Purpose:** Apply specific mapping corrections with complete audit trail
**Use Case:** Implement targeted mapping improvements

#### Features:
- ✅ Interactive and batch correction modes
- ✅ Before/after value logging
- ✅ CSV_data_count synchronization from map_csv_* tables
- ✅ Validation of mapping changes
- ✅ Complete audit trail generation

#### Usage:
```bash
python manual_mapping_corrector.py
```

#### Correction Types Supported:
- **Map Unmapped Field:** Assign CSV field to unmapped JSON field
- **Change Existing Mapping:** Update current CSV field mapping
- **Clear Mapping:** Remove inappropriate mapping
- **Update Data Count:** Synchronize CSV_data_count values

#### Outputs:
- `manual_corrections_report_YYYYMMDD_HHMMSS.md` - Correction log
- `manual_corrections_log_YYYYMMDD_HHMMSS.json` - Structured changes
- Database updates with new mappings

---

### ✅ **post_correction_analyzer.py** - VALIDATION & QUALITY CHECKER
**Purpose:** Verify mapping quality improvements after corrections
**Use Case:** Measure progress and identify remaining issues

#### Features:
- ✅ Quality score calculation and comparison
- ✅ Before/after improvement metrics
- ✅ Remaining issues identification
- ✅ Mapping coverage analysis

#### Usage:
```bash
python post_correction_analyzer.py
```

#### Metrics Tracked:
- **Quality Score:** Percentage of well-mapped fields
- **Coverage:** Percentage of fields with mappings
- **Improvement:** Delta from previous analysis
- **Remaining Issues:** Outstanding problems by priority

#### Outputs:
- `post_correction_quality_report_YYYYMMDD_HHMMSS.md` - Quality analysis
- `post_correction_analysis_YYYYMMDD_HHMMSS.json` - Metrics data
- Console quality dashboard

---

## 🔄 RECOMMENDED WORKFLOW

### 1. **Initial Assessment**
```bash
python comprehensive_mapping_analyzer.py
```
→ Understand current state and identify all issues

### 2. **Rule Compliance** (✅ COMPLETED)
```bash
python duplicate_mapping_resolver.py
```
→ Ensure one-to-one CSV-to-JSON mapping compliance

### 3. **Critical Gap Analysis**
```bash
python critical_issues_analyzer.py
```
→ Identify highest-priority unmapped fields

### 4. **Targeted Corrections**
```bash
python manual_mapping_corrector.py
```
→ Apply specific mapping improvements

### 5. **Progress Validation**
```bash
python post_correction_analyzer.py
```
→ Measure improvements and plan next steps

### 6. **Iterate** (Steps 3-5)
Repeat correction cycle until quality targets achieved

---

## 📊 DATABASE SCHEMA REFERENCE

### **map_json_*** Tables Structure:
```sql
- id (INTEGER PRIMARY KEY)
- field_name (TEXT) -- JSON field name
- field_type (TEXT)
- CSV_field (TEXT) -- Mapped CSV field name
- CSV_data_count (INTEGER) -- Record count in CSV
```

### **map_csv_*** Tables Structure:
```sql
- field_name (TEXT) -- CSV field name  
- CSV_data_count (INTEGER) -- Actual record count
```

### **Key Relationships:**
- `map_json_*.CSV_field` → `map_csv_*.field_name`
- `map_json_*.CSV_data_count` should match `map_csv_*.CSV_data_count`

---

## 🎯 QUALITY TARGETS

### **SUCCESS CRITERIA:**
- ✅ **Zero Duplicate Mappings** (ACHIEVED)
- 📋 **>90% Field Coverage** (463 unmapped fields to address)
- 📋 **>80% Quality Score** (currently 29.7%)  
- 📋 **<5% Questionable Mappings** (124 fields to review)

### **CURRENT PROGRESS:**
- **Rule Compliance:** 100% ✅
- **Duplicate Violations:** 0 ✅  
- **Tools Created:** 5/5 ✅
- **Corrections Applied:** 329 ✅

**NEXT FOCUS:** Map 463 unmapped fields with available CSV data
