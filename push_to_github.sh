#!/bin/bash

echo "============================================"
echo "Push to GitHub Helper Script"
echo "============================================"
echo ""
echo "Have you created a GitHub repository yet?"
echo "If not, go to: https://github.com/new"
echo ""
echo "Repository settings:"
echo "  - Name: option_chain"
echo "  - Public (for GitHub Pages)"
echo "  - Don't initialize with README"
echo ""
read -p "Enter your GitHub username: " username
echo ""

if [ -z "$username" ]; then
    echo "❌ Username cannot be empty"
    exit 1
fi

# Add remote
echo "📡 Adding remote repository..."
git remote add origin "https://github.com/$username/option_chain.git" 2>/dev/null || echo "Remote already exists"

# Push
echo ""
echo "🚀 Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "============================================"
echo "✅ Done!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Go to: https://github.com/$username/option_chain"
echo "2. Click 'Settings' > 'Pages'"
echo "3. Source: Deploy from branch 'main'"
echo "4. Folder: / (root)"
echo "5. Click 'Save'"
echo ""
echo "Your site will be live at:"
echo "https://$username.github.io/option_chain/"
echo ""
