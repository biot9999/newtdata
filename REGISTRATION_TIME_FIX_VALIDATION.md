# Registration Time Fix Validation

## Issue Description
Registration time queries were showing incorrect dates (2025) for accounts that were actually registered in 2020 and 2022.

## Root Cause
The `get_messages()` API call with only `reverse=True` parameter was not starting from the beginning of chat history. Without explicitly setting `offset_id=0`, Telethon would not retrieve the very first (oldest) message, resulting in recent messages being returned instead.

## Fix Applied
Added `offset_id=0` parameter to both message retrieval methods:

### Before (Incorrect):
```python
messages = await client.get_messages(
    telegram_entity,
    limit=1,
    reverse=True  # This alone doesn't guarantee starting from the beginning!
)
```

### After (Correct):
```python
messages = await client.get_messages(
    telegram_entity,
    limit=1,
    offset_id=0,  # Explicitly start from the very beginning of chat history
    reverse=True  # Get messages in chronological order (oldest first)
)
```

## How offset_id=0 Works
- `offset_id=0` tells Telethon to start iteration from before the first message (message ID 0 doesn't exist, so it starts from ID 1)
- Combined with `reverse=True`, this ensures we get messages in chronological order starting from the very first one
- `limit=1` ensures we only get the first (oldest) message

## What Was Fixed
1. **Telegram Official Chat (777000) retrieval** - Now correctly gets the first welcome message, which represents the account registration date
2. **Saved Messages retrieval** - Now correctly gets the first saved message as a fallback method

## Testing Validation

### Expected Behavior:
- Accounts registered in 2020 should show dates like "2020-05-03" (not "2025-12-08")
- Accounts registered in 2022 should show dates like "2022-03-15" (not "2025-12-08")
- The `registration_source` field should indicate:
  - `"telegram_chat"` - Retrieved from Telegram official chat (most accurate)
  - `"saved_messages"` - Retrieved from Saved Messages (fallback)
  - `"estimated"` - Estimated from user ID (last resort)

### Code Location
File: `tdata.py`
Method: `check_account_registration_time()`
Lines affected: 
- Line 20113-20118: Telegram chat message retrieval
- Line 20140-20145: Saved Messages retrieval

## Impact
This fix ensures that the registration time query feature returns accurate historical dates instead of current dates, making the feature useful for account age verification and classification.

## Related Issue
- Issue: "查询注册时间 不准确" (Registration time query inaccurate)
- Screenshots showed 2020 and 2022 accounts incorrectly displayed as 2025 registrations
