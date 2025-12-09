# TData Format Proxy Support - Implementation Summary

## Issue Description
The original issue (in Chinese): "所有关于tdata格式的 检查 ，处理 都没有使用代理，并且检查状态也不准确！！！"

Translation: "All checks and processing related to tdata format are not using proxies, and the status checks are inaccurate!!"

## Root Cause Analysis

### Before the Fix
1. **No Proxy Support**: The `check_tdata_with_spambot()` function did not use any proxy configuration, unlike the session checking function `check_account_status()`.

2. **No Retry Mechanism**: TData checking lacked the robust retry mechanism with proxy rotation that was implemented for session checking.

3. **No Fallback**: When connection failed, there was no automatic fallback to try different proxies or local connection.

4. **Inconsistent Accuracy**: Without proxy support and retries, TData checks were more prone to connection timeouts and false negatives.

## Solution Implemented

### 1. Proxy Support Architecture
```
check_tdata_with_spambot(tdata_path, tdata_name, db)
    ↓
    Checks if proxy is enabled (USE_PROXY + db.get_proxy_enabled() + has proxies)
    ↓
    Retry loop (max_proxy_attempts times)
    ↓
    For each attempt:
        ├─→ Get next proxy from ProxyManager
        ├─→ Call _single_tdata_check_with_proxy(with proxy)
        └─→ If fails, retry with next proxy
    ↓
    If all proxies fail:
        └─→ Fallback to local connection (no proxy)
```

### 2. Key Changes

#### A. Refactored `check_tdata_with_spambot()` Function
- **Added Parameters**: 
  - `db: 'Database'` - To access proxy settings
  
- **New Logic**:
  - Check if proxy mode is active
  - Implement retry loop with configurable attempts (via `self.max_retries`)
  - Rotate through available proxies on each retry
  - Fallback to local connection if all proxies fail

#### B. Created `_single_tdata_check_with_proxy()` Helper
This new method handles the actual TData checking with optional proxy:

- **TData to Session Conversion**: 
  - Loads TData using `TDesktop(tdata_path)`
  - Converts to Telethon session
  - Creates new client with proxy support

- **Proxy Configuration**:
  - Supports HTTP, SOCKS4, SOCKS5 proxies
  - Auto-detects residential proxies
  - Adjusts timeout based on proxy type (30s for residential, shorter for others)

- **Enhanced Error Handling**:
  - Connection timeout detection
  - Network error classification (timeout, connection_refused, auth_failed, dns_error)
  - Frozen account detection
  - Proper cleanup of temporary session files

- **SpamBot Detection**:
  - Timeout handling for all operations
  - Proper text translation for multi-language support
  - Accurate status classification

### 3. Configuration Support

The implementation respects all existing proxy configuration:

```python
# .env file settings
USE_PROXY=true                    # Enable/disable proxy globally
PROXY_FILE=proxy.txt             # Proxy list file
PROXY_TIMEOUT=10                 # Standard proxy timeout
RESIDENTIAL_PROXY_TIMEOUT=30     # Residential proxy timeout
PROXY_RETRY_COUNT=2              # Number of retries
PROXY_DEBUG_VERBOSE=false        # Verbose proxy debugging
```

### 4. Proxy Rotation & Retry

- **Max Retries**: Configurable via `self.max_retries` (default: 3)
- **Retry Delay**: 2 seconds between retries (configurable via `self.retry_delay`)
- **Proxy Selection**: Uses `ProxyManager.get_next_proxy()` for round-robin selection
- **Fallback**: Automatic fallback to local connection after all proxy attempts fail

### 5. Error Message Enhancement

All error messages now include proxy status for better debugging:

```
Examples:
- "使用代理 | 连接超时"
- "使用住宅代理 | timeout"
- "本地连接 | 账号已被冻结/删除"
- "手机号:+1234567890 | 使用代理 | 正常无限制"
```

## Code Quality Improvements

1. **Avoided Integer Overflow**: Use `time.time_ns()` instead of `time.time()*1000`
2. **Efficient Client Creation**: Create client with proxy from the start, avoiding disconnect/reconnect
3. **Named Constants**: Extract magic number (0.1) to `SPAMBOT_FAST_WAIT` constant
4. **Direct Method Calls**: Use `self.translate_spambot_reply()` directly instead of conditional access

## Testing Recommendations

### Test Case 1: TData with Proxy Enabled
```bash
# Prerequisites:
# - Valid proxy in proxy.txt
# - USE_PROXY=true in .env
# - Database proxy_enabled=true

# Upload a TData ZIP file
# Expected: Should use proxy for checking
# Verify: Check logs for "使用代理 检测TData" messages
```

### Test Case 2: TData with All Proxies Failed
```bash
# Prerequisites:
# - Invalid proxies in proxy.txt
# - USE_PROXY=true in .env

# Upload a TData ZIP file
# Expected: Should fallback to local connection
# Verify: Check logs for "所有代理失败，回退到本地连接" message
```

### Test Case 3: TData without Proxy
```bash
# Prerequisites:
# - USE_PROXY=false in .env OR no proxies in proxy.txt

# Upload a TData ZIP file
# Expected: Should use local connection directly
# Verify: Status messages should not include proxy information
```

### Test Case 4: Residential Proxy Timeout
```bash
# Prerequisites:
# - Residential proxy in proxy.txt (e.g., *.abcproxy.vip)
# - USE_PROXY=true

# Upload a TData ZIP file
# Expected: Should use 30-second timeout instead of default
# Verify: Check if operation completes within extended timeout
```

## Backward Compatibility

✅ **Fully backward compatible**
- If `USE_PROXY=false`, behaves exactly as before
- If no proxies configured, uses local connection
- If database is not available, defaults to proxy enabled

## Performance Impact

- **With Proxy Enabled**: Slight overhead for proxy connection setup (~1-2 seconds per attempt)
- **With Retry**: Maximum delay = max_retries × (timeout + retry_delay)
- **Fast Mode**: Reduced wait times when `PROXY_FAST_MODE=true`

## Security Considerations

✅ **CodeQL Analysis**: No security vulnerabilities detected
✅ **Proxy Privacy**: Proxy details are hidden in logs for user privacy
✅ **Session Cleanup**: Temporary session files are properly cleaned up
✅ **Error Handling**: All exceptions are caught and handled appropriately

## Related Configuration

### Proxy File Format (proxy.txt)
```
# HTTP Proxy
127.0.0.1:8080
127.0.0.1:8080:username:password

# SOCKS5 Proxy
socks5:127.0.0.1:1080:username:password

# Residential Proxy (auto-detected)
host.abcproxy.vip:4950:username:password
```

## Summary

This implementation brings TData format checking to feature parity with session format checking:

| Feature | Session Checking | TData Checking (Before) | TData Checking (After) |
|---------|-----------------|-------------------------|------------------------|
| Proxy Support | ✅ | ❌ | ✅ |
| Retry Mechanism | ✅ | ❌ | ✅ |
| Proxy Rotation | ✅ | ❌ | ✅ |
| Fallback to Local | ✅ | ❌ | ✅ |
| Residential Proxy Detection | ✅ | ❌ | ✅ |
| Error Classification | ✅ | ⚠️ Partial | ✅ |
| Timeout Handling | ✅ | ⚠️ Partial | ✅ |

## Files Modified

- `tdata.py` (lines 2617-2870)
  - `check_tdata_with_spambot()` - Refactored with proxy support
  - `_single_tdata_check_with_proxy()` - New helper method
  - Updated call site to pass `db` parameter

## Commit History

1. `f1d3369` - Add proxy support to tdata format checking with retry mechanism
2. `620396f` - Address code review feedback - improve client creation and constants
