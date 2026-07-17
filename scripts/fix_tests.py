import os
from pathlib import Path

tests_dir = Path("tests")
for root, dirs, files in os.walk(tests_dir):
    for f in files:
        if f.endswith(".py"):
            path = Path(root) / f
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
            
            new_content = content.replace("app.integrations.crm", "app.integrations.enterprise")
            new_content = new_content.replace("app.integrations.iam", "app.integrations.enterprise")
            new_content = new_content.replace("app.integrations.sso", "app.integrations.enterprise")
            new_content = new_content.replace("MockCRMAdapter", "SQLiteCRMAdapter")
            new_content = new_content.replace("MockIAMAdapter", "SQLiteIAMAdapter")
            new_content = new_content.replace("MockSSOAdapter", "SQLiteSSOAdapter")
            
            if new_content != content:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Updated {path}")
