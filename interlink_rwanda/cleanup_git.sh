#!/bin/bash

# Complete Git cleanup script for removing large files and node_modules

echo "=== Git Large File Cleanup Script ==="
echo "This script will completely remove large files from Git history"
echo "WARNING: This will rewrite Git history and require force push"
echo ""
read -p "Do you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Create/update .gitignore
echo "Creating comprehensive .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/
interlink_env/

# Flask
instance/
.webassets-cache

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Database
*.db
*.sqlite3

# Node.js and npm
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
package-lock.json

# WhatsApp Web JS session data
.wwebjs_auth/
.wwebjs_cache/

# Uploads and user data
uploads/
temp/

# IDE and Editor
.vscode/
.idea/
*.swp
*.swo

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Large binaries and cache
*.dmg
*.pkg
*.deb
*.rpm
.local-chromium/
chrome-linux/

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*
EOF

# Step 2: Remove all files from Git tracking
echo "Removing all files from Git tracking..."
git rm -r --cached . 2>/dev/null || true

# Step 3: Add .gitignore to tracking
git add .gitignore

# Step 4: Re-add only the files we want to track
echo "Re-adding project files (excluding ignored files)..."
find . -name "*.py" -not -path "./interlink_env/*" -not -path "./__pycache__/*" | xargs git add 2>/dev/null || true
find . -name "*.html" -not -path "./interlink_env/*" | xargs git add 2>/dev/null || true
find . -name "*.js" -not -path "./node_modules/*" -not -path "./.wwebjs_auth/*" -not -path "./interlink_env/*" | xargs git add 2>/dev/null || true
find . -name "*.json" -not -path "./node_modules/*" -not -path "./.wwebjs_auth/*" -not -path "./interlink_env/*" | xargs git add 2>/dev/null || true
find . -name "*.txt" -not -path "./node_modules/*" -not -path "./interlink_env/*" | xargs git add 2>/dev/null || true
find . -name "*.md" -not -path "./node_modules/*" -not -path "./interlink_env/*" | xargs git add 2>/dev/null || true
find . -name "*.sh" -not -path "./node_modules/*" -not -path "./interlink_env/*" | xargs git add 2>/dev/null || true

# Add migration files if they exist
find . -path "*/migrations/*.py" -not -path "./interlink_env/*" | xargs git add 2>/dev/null || true
find . -path "*/migrations/versions/*.py" -not -path "./interlink_env/*" | xargs git add 2>/dev/null || true

# Add specific important files
git add requirements.txt 2>/dev/null || true
git add README.md 2>/dev/null || true

# Step 5: Create a clean commit
echo "Creating clean commit..."
git commit -m "Clean repository - removed node_modules, large files, and cache

- Added comprehensive .gitignore
- Removed all node_modules and dependencies
- Removed WhatsApp Web JS cache and session data
- Removed Python cache files
- Removed upload files and temporary data
- Ready for fresh deployment"

# Step 6: Create a completely new branch and reset
echo "Creating fresh branch..."
git branch fresh-start
git checkout fresh-start

# Optional: Completely rewrite history to remove large files
echo ""
echo "Do you want to completely rewrite Git history to remove all traces of large files?"
echo "This will make the repository much smaller but will change all commit hashes."
read -p "Rewrite history? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing git-filter-repo if not available..."
    pip install git-filter-repo 2>/dev/null || echo "Please install git-filter-repo manually"
    
    echo "Rewriting history to remove large files and directories..."
    git filter-repo --path node_modules --invert-paths --force 2>/dev/null || echo "git-filter-repo not available, skipping history rewrite"
    git filter-repo --path .wwebjs_auth --invert-paths --force 2>/dev/null || true
    git filter-repo --path uploads --invert-paths --force 2>/dev/null || true
    git filter-repo --path __pycache__ --invert-paths --force 2>/dev/null || true
    git filter-repo --path .local-chromium --invert-paths --force 2>/dev/null || true
fi

echo ""
echo "=== Cleanup Complete ==="
echo ""
echo "Next steps:"
echo "1. Verify your files are present: git ls-files"
echo "2. Check repository size: du -sh .git"
echo "3. Push the clean repository:"
echo "   git push origin fresh-start --force"
echo "4. If everything looks good, make fresh-start your main branch"
echo ""
echo "To set up the environment again:"
echo "1. npm install (to reinstall dependencies)"
echo "2. pip install -r requirements.txt"
echo "3. Set up your .env file with necessary variables"
echo ""
echo "Your original work is preserved, just without the large files!"
