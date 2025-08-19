
#!/usr/bin/env python3
"""
Security audit script for PyCommerce.
Run this before deploying to production or syncing with GitHub.
"""

import os
import re
import sys
from pathlib import Path

def check_secrets_in_files():
    """Check for hardcoded secrets in files."""
    print("🔍 Checking for hardcoded secrets...")
    
    # Patterns that indicate potential secrets
    secret_patterns = [
        (r'["\']sk_live_[a-zA-Z0-9]+["\']', 'Stripe live secret key'),
        (r'["\']pk_live_[a-zA-Z0-9]+["\']', 'Stripe live public key'),
        (r'["\']AIza[a-zA-Z0-9_-]{35}["\']', 'Google API key'),
        (r'["\']ya29\.[a-zA-Z0-9_-]+["\']', 'Google OAuth token'),
        (r'password\s*=\s*["\'][a-zA-Z0-9!@#$%^&*()_+-=]{12,}["\'](?!.*your_password)', 'Hardcoded password'),
        (r'secret_key\s*=\s*["\'][a-zA-Z0-9!@#$%^&*()_+-=]{32,}["\']', 'Hardcoded secret key'),
        (r'api_key\s*=\s*["\'][a-zA-Z0-9]{32,}["\'](?!.*your_)', 'Hardcoded API key'),
        (r'DATABASE_URL\s*=\s*["\']postgresql://[^"\']*:[^"\']*@[^"\']+["\']', 'Hardcoded database URL'),
    ]
    
    issues = []
    exclude_dirs = {
        'scripts', '.git', '__pycache__', 'node_modules', '.pythonlibs', 
        '.cache', '.uv', 'venv', '.venv', 'env', '.env',
        'site-packages', 'dist-packages', '.pytest_cache'
    }
    
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Skip any directory that contains third-party code or cache
        if any(excluded in root for excluded in ['.cache', '.uv', 'site-packages', 'dist-packages', '.pythonlibs']):
            continue
        
        for file in files:
            if file.endswith(('.py', '.js', '.html', '.yml', '.yaml', '.json', '.env')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern, description in secret_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_number = content[:match.start()].count('\n') + 1
                            issues.append(f"  ⚠️  {file_path}:{line_number} - {description}")
                            
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    if issues:
        print("❌ Found potential hardcoded secrets:")
        for issue in issues:
            print(issue)
        return False
    else:
        print("✅ No hardcoded secrets found")
        return True

def check_environment_variables():
    """Check for required environment variables."""
    print("\n🔍 Checking environment variables...")
    
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  ⚠️  {var}")
        print("\n💡 Add these to your Replit Secrets or .env file")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def check_file_permissions():
    """Check for files with overly permissive permissions."""
    print("\n🔍 Checking file permissions...")
    
    sensitive_files = [
        '.env',
        'config/secrets.json',
        'private_key.pem'
    ]
    
    issues = []
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            # Check if file is readable by others (octal 044)
            if stat.st_mode & 0o044:
                issues.append(f"  ⚠️  {file_path} is readable by others")
    
    if issues:
        print("❌ Found files with overly permissive permissions:")
        for issue in issues:
            print(issue)
        return False
    else:
        print("✅ File permissions look good")
        return True

def check_gitignore():
    """Check if sensitive files are properly ignored."""
    print("\n🔍 Checking .gitignore...")
    
    required_ignores = [
        '.env',
        '*.key',
        '*.pem',
        '*.log',
        'config/secrets.json'
    ]
    
    gitignore_path = '.gitignore'
    if not os.path.exists(gitignore_path):
        print("❌ No .gitignore file found")
        return False
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    missing_ignores = []
    for ignore_pattern in required_ignores:
        if ignore_pattern not in gitignore_content:
            missing_ignores.append(ignore_pattern)
    
    if missing_ignores:
        print("❌ Missing patterns in .gitignore:")
        for pattern in missing_ignores:
            print(f"  ⚠️  {pattern}")
        return False
    else:
        print("✅ .gitignore properly configured")
        return True

def main():
    """Run security audit."""
    print("🛡️  PyCommerce Security Audit")
    print("=" * 40)
    
    checks = [
        check_secrets_in_files(),
        check_environment_variables(), 
        check_file_permissions(),
        check_gitignore()
    ]
    
    print("\n" + "=" * 40)
    if all(checks):
        print("✅ Security audit passed! Safe to sync with GitHub.")
        sys.exit(0)
    else:
        print("❌ Security audit failed! Please fix issues before syncing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
