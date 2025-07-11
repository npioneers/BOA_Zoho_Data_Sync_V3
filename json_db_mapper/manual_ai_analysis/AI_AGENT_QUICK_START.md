# AI AGENT QUICK START GUIDE

## 🚀 IMMEDIATE ACTION COMMANDS

### 1. ASSESS CURRENT STATE
```bash
cd json_db_mapper/manual_ai_analysis
python comprehensive_mapping_analyzer.py
```
**Output:** Current mapping quality, duplicates, critical issues

### 2. FIX DUPLICATE VIOLATIONS (if any)
```bash
python duplicate_mapping_resolver.py
```
**Output:** Zero duplicate mappings (one-to-one compliance)

### 3. IDENTIFY CRITICAL GAPS
```bash
python critical_issues_analyzer.py
```
**Output:** Unmapped fields with available CSV data (data loss risk)

### 4. APPLY CORRECTIONS
```bash
python manual_mapping_corrector.py
```
**Usage:** Implement specific mapping improvements

### 5. VALIDATE RESULTS
```bash
python post_correction_analyzer.py
```
**Output:** Quality metrics and remaining issues

## 📊 CURRENT SITUATION (July 8, 2025)

### ✅ RESOLVED
- **Duplicate Mappings:** 0 (was 178) 
- **Rule Compliance:** 100%
- **Tools Created:** 5 analysis tools ready

### 🎯 NEXT PRIORITY
- **Unmapped Fields:** 463 fields need mapping
- **Questionable Fields:** 124 need review  
- **Target Quality:** >80% (currently 29.7%)

## 🧠 DOMAIN LOGIC QUICK REFERENCE

### PRIORITY ORDER
1. **Exact name match** (customer_name → customer_name)
2. **Semantic match** (customer_name → client_name) 
3. **Type consistency** (date fields → date fields)
4. **Name over ID** (customer_name > customer_id)
5. **Raw over formatted** (status > status_formatted)

### BUSINESS RULES
- **Time:** created_time > created_timestamp > created_by
- **Status:** status > sub_status > status_formatted  
- **Currency:** currency_code > currency_id > currency_symbol
- **Names:** Always prefer name fields over ID fields
- **Templates:** template_name > template_id > template_type

## 🎯 SUCCESS METRICS
- **Zero duplicates** ✅ ACHIEVED
- **Zero unmapped fields with CSV data** (TARGET)
- **Quality score >80%** (TARGET)
- **All questionable mappings justified** (TARGET)

## 📁 KEY FILES
- **Database:** `../../data/database/production.db`
- **CSV Counts:** Tables `map_csv_*` 
- **JSON Mappings:** Tables `map_json_*`
- **Reports:** Generated in current directory

## ⚡ FASTEST PATH TO COMPLETION

1. **Run comprehensive analyzer** → See current state
2. **Focus on unmapped fields** → Biggest impact on quality
3. **Use critical issues analyzer** → Prioritize by data volume
4. **Apply corrections systematically** → One table at a time
5. **Validate frequently** → Catch issues early

**REMEMBER:** Every change must maintain one-to-one CSV-to-JSON mapping rule!
