# Bedrock Error Handling Implementation

## Summary
Added comprehensive error handling for AWS Bedrock access issues in the MCP server to provide clear, actionable error messages to users.

## Changes Made

### 1. bedrock_analyzer.py
Enhanced error handling in all Bedrock client initialization and invocation points:

#### Client Initialization (4 locations updated)
- `select_icons_for_keyword()` - Line ~78
- `_analyze_with_llm_selection()` - Line ~473
- `_analyze_with_local_selection()` - Line ~561
- `initialize_client()` - Line ~1244

**Error handling added:**
```python
try:
    self.bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name=self.region_name
    )
except Exception as e:
    error_msg = f"⚠️ Bedrock Access Error: Unable to initialize Bedrock client. {str(e)}"
    print(error_msg)
    raise RuntimeError(error_msg) from e
```

#### Model Invocation (3 locations updated)
- `select_icons_for_keyword()` - Exception handler
- `_analyze_with_llm_selection()` - Exception handler
- `_analyze_with_local_selection()` - Exception handler

**Enhanced error detection:**
```python
except RuntimeError:
    # Re-raise Bedrock access errors
    raise
except Exception as e:
    error_type = type(e).__name__
    error_msg = str(e)
    
    # Check for common Bedrock access issues
    if 'AccessDenied' in error_msg or 'UnauthorizedOperation' in error_msg:
        detailed_error = f"⚠️ Bedrock Access Denied: Check IAM permissions for bedrock:InvokeModel"
    elif 'ValidationException' in error_msg and 'model' in error_msg.lower():
        detailed_error = f"⚠️ Bedrock Model Access: Model '{self.model_id}' not accessible. Enable model access in Bedrock console"
    elif 'ResourceNotFoundException' in error_msg:
        detailed_error = f"⚠️ Bedrock Not Available: Bedrock service not available in region '{self.region_name}'"
    elif 'ExpiredToken' in error_msg or 'InvalidClientTokenId' in error_msg:
        detailed_error = f"⚠️ AWS Credentials Error: Invalid or expired AWS credentials"
    else:
        detailed_error = f"❌ Bedrock Error ({error_type}): {error_msg}"
    
    print(detailed_error)
    raise RuntimeError(detailed_error) from e
```

### 2. server.py
Updated the MCP server to properly catch and display Bedrock errors:

```python
except RuntimeError as e:
    # Bedrock access errors
    error_msg = str(e)
    logger.log_mcp_response([], error=error_msg)
    return [TextContent(type="text", text=error_msg)]
except Exception as e:
    import traceback
    error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
    logger.log_mcp_response([], error=error_msg)
    return [TextContent(type="text", text=error_msg)]
```

## Error Messages

The implementation now provides specific, actionable error messages for common issues:

1. **Access Denied**: `⚠️ Bedrock Access Denied: Check IAM permissions for bedrock:InvokeModel`
2. **Model Access**: `⚠️ Bedrock Model Access: Model 'model-id' not accessible. Enable model access in Bedrock console`
3. **Region Unavailable**: `⚠️ Bedrock Not Available: Bedrock service not available in region 'region-name'`
4. **Credentials**: `⚠️ AWS Credentials Error: Invalid or expired AWS credentials`
5. **Generic**: `❌ Bedrock Error (ErrorType): error details`

## Testing

To test the error handling:

1. **Invalid credentials**: Remove/corrupt AWS credentials
2. **Wrong region**: Set region to one without Bedrock (e.g., af-south-1)
3. **Model not enabled**: Use a model ID that hasn't been enabled in Bedrock console
4. **No permissions**: Use IAM role without bedrock:InvokeModel permission

## Benefits

- Users now receive clear, actionable error messages instead of generic "No matching icons found"
- Errors are properly logged for debugging
- RuntimeError exceptions propagate correctly through the call stack
- Distinguishes between different types of Bedrock access issues
