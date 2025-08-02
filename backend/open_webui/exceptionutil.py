"""
Modification Log:
------------------
| Date       | Author         | MOD TAG            | Description                                                                                         |
|------------|----------------|--------------------|-----------------------------------------------------------------------------------------------------|
| 2025-12-02 | X1BA          | CWE-209            | Replaced direct exception messages with generic responses in user-facing outputs.                   |
                                                             
"""
def getErrorMsg(e):
  # MOD TAG CWE-209 Generation of Error Message Containing Sensitive Information
  error_msg = e.args[0] if (e and len(e.args) >= 1) else None
  error_msg = error_msg if error_msg else "Internal error occruced while processing request"
  return error_msg