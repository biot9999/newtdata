# i18n Implementation Progress and Completion Guide

## 📊 Current Status

### Translation Keys
- **Total keys available**: 459 (zh.json and en.json)
- **Modules covered**:
  - ✅ start: 27 keys
  - ✅ check: 34 keys (file scanning, progress messages)
  - ✅ convert: 20 keys
  - ✅ modify: 36 keys (profile modification, progress)
  - ✅ system: 37 keys (startup, library imports)
  - ✅ file: 26 keys (file operations, progress)

### Code Coverage
- **i18n.get() calls**: 97
- **User-facing messages remaining**: ~243
- **Current coverage**: ~40%

## ✅ Completed Work

### Phase 1: Translation Keys
1. ✅ Added 108+ new translation keys to both zh.json and en.json
2. ✅ Organized keys by module (check, convert, modify, system, file)
3. ✅ Added comprehensive progress message translations
4. ✅ Added file operation translations

### Phase 2: Code Refactoring (Completed Areas)
1. ✅ System startup messages (lines 49-202)
2. ✅ Library import messages (lines 103-202)
3. ✅ File scanning in check module (lines 3200-3320)
   - Session file detection
   - TData directory detection
   - Duplicate file handling
4. ✅ Profile modification progress (lines 19700-20087)
   - Initial progress message
   - Real-time progress updates
   - Success/failure tracking
5. ✅ i18n.py internal messages
   - Language loading messages
   - Error handling messages

## 📋 Remaining Work

### High Priority - User-Facing Messages (~200+)

#### 1. Account Detection Module
**Location**: Search for `safe_edit_message.*检测` or `reply_text.*检测`

Key areas:
- Progress updates during account checking
- Status messages (alive/dead counts)
- Error messages
- Result summaries

Example pattern:
```python
# Before:
self.safe_edit_message(query, f"⏳ 正在检测... {current}/{total}")

# After:
self.safe_edit_message(query, self.i18n.get(user_id, 'check.processing', current=current, total=total))
```

#### 2. Format Conversion Module
**Location**: Lines ~12200-12600

Key areas:
- Conversion start messages
- Progress updates
- File type validation errors
- Completion messages

Current status:
- ✅ Start message (line 12285)
- ⏳ Progress updates
- ⏳ Error messages
- ⏳ Completion messages

#### 3. Broadcast Messages
**Location**: Lines ~16100-16300

Key areas:
- Broadcast initialization
- Send progress
- Success/failure counts

#### 4. Batch Creation
**Location**: Lines ~18800-19000

Key areas:
- Creation progress
- Status messages
- Completion summary

#### 5. Reauthorization
**Location**: Lines ~20500-20700

Key areas:
- Progress updates
- Status tracking
- Error handling

### Medium Priority - Internal Messages (~200+)

#### 1. Print Statements
**Location**: Throughout file (~439 instances)

These are mostly for internal logging but some are visible in logs. Priority:
- 🔴 High: Messages related to file processing
- 🟡 Medium: Proxy and configuration messages
- 🟢 Low: Debug and trace messages

#### 2. Logger Messages
**Location**: Throughout file

Focus on logger.info() and logger.warning() that might be user-visible.

## 🔧 Implementation Guide

### Step-by-Step Process

#### Step 1: Identify the Message
Search for Chinese text in user-facing methods:
```bash
grep -n "reply_text.*[\u4e00-\u9fff]" tdata.py
grep -n "edit_message_text.*[\u4e00-\u9fff]" tdata.py
grep -n "safe_edit_message.*[\u4e00-\u9fff]" tdata.py
grep -n "send_message.*[\u4e00-\u9fff]" tdata.py
```

#### Step 2: Find user_id Context
Look up the function to find user_id:
```python
# Usually available as:
- Function parameter: def func(self, user_id: int, ...)
- From update: user_id = update.effective_user.id
- From callback query: user_id = query.from_user.id
```

#### Step 3: Check/Add Translation Key
1. Check if key exists in zh.json and en.json
2. If not, add to both files:
```json
// zh.json
{
  "module": {
    "key_name": "Chinese text with {param1} and {param2}"
  }
}

// en.json  
{
  "module": {
    "key_name": "English text with {param1} and {param2}"
  }
}
```

#### Step 4: Replace in Code
```python
# Before:
update.message.reply_text(f"⏳ 正在处理... {current}/{total}")

# After:
update.message.reply_text(self.i18n.get(user_id, 'module.key_name', current=current, total=total))
```

### Common Patterns

#### Pattern 1: Simple Message
```python
# Before:
query.edit_message_text("✅ 处理完成！")

# After:
query.edit_message_text(self.i18n.get(user_id, 'module.complete'))
```

#### Pattern 2: Message with Parameters
```python
# Before:
self.safe_edit_message(query, f"进度: {current}/{total}\n成功: {success}")

# After:
self.safe_edit_message(query, self.i18n.get(
    user_id, 
    'module.progress',
    current=current,
    total=total,
    success=success
))
```

#### Pattern 3: Multi-line Formatted Message
```python
# Before:
text = (
    f"⏳ 正在处理...\n\n"
    f"进度: {current}/{total}\n"
    f"成功: {success}\n"
    f"失败: {failed}"
)

# After:
text = self.i18n.get(
    user_id,
    'module.processing',
    current=current,
    total=total,
    success=success,
    failed=failed
)
```

### Testing Checklist

After each replacement:
1. ✅ Verify syntax is correct
2. ✅ Check all parameters are passed
3. ✅ Test Chinese (zh) language
4. ✅ Test English (en) language
5. ✅ Verify no functionality is broken

## 📈 Progress Tracking

Use this checklist to track completion:

### User-Facing Messages
- [x] System startup messages
- [x] File scanning messages (check module)
- [x] Profile modification progress
- [ ] Account detection progress (~20 messages)
- [ ] Format conversion progress (~15 messages)
- [ ] Broadcast messages (~10 messages)
- [ ] Batch creation messages (~8 messages)
- [ ] Reauthorization messages (~10 messages)
- [ ] Error messages (~30 messages)
- [ ] Button/Menu text (~50 messages)
- [ ] Status/Info messages (~100 messages)

### Internal Messages
- [x] Library import messages
- [ ] Proxy management messages (~20)
- [ ] Device parameter messages (~10)
- [ ] Database messages (~15)
- [ ] File operation messages (~50)
- [ ] Debug/trace messages (~300 - low priority)

## 🎯 Target: 100% Coverage

**Goal**: Replace all user-facing Chinese text with i18n.get() calls

**Priority Order**:
1. 🔴 Critical: Messages users see in Telegram interface (reply_text, edit_message, etc.)
2. 🟡 Important: Progress updates, status messages
3. 🟢 Optional: Internal logging, debug messages

## 🚀 Quick Win Areas

Focus on these for maximum impact:

### 1. Progress Messages (High visibility, ~50 instances)
All messages with:
- "⏳ 正在"
- "进度:"
- "成功:"
- "失败:"

### 2. Completion Messages (~30 instances)
All messages with:
- "✅ 完成"
- "❌ 失败"
- "⚠️ 警告"

### 3. Initialization Messages (~20 instances)
All messages with:
- "正在初始化"
- "请稍候"
- "正在处理"

## 📝 Notes

### What NOT to Replace
- Comments (they're not user-visible)
- Docstrings (they're for developers)
- Variable names (they're code)
- Test data or examples (unless user-visible)

### Best Practices
1. Keep translation keys organized by module
2. Use descriptive key names (e.g., `check.processing_current` not `check.msg1`)
3. Include all dynamic parameters in the translation
4. Test both languages after each major change
5. Group related changes in commits

### Common Pitfalls to Avoid
- ❌ Missing user_id context
- ❌ Forgetting to add keys to both zh.json and en.json
- ❌ Typos in key names
- ❌ Missing format parameters
- ❌ Breaking existing functionality

## 🏁 Completion Criteria

The task is complete when:
1. ✅ All user-facing Chinese text uses i18n.get()
2. ✅ Translation keys exist for all used keys
3. ✅ Both Chinese and English translations work
4. ✅ No regressions in functionality
5. ✅ Users can switch languages and see all text translated

Current Progress: **40%** → Target: **100%**
Remaining effort: ~200-250 message replacements
