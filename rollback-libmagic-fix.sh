#!/bin/bash
set -e

echo "🔄 Rolling back LibMagic Fix"
echo "==========================="

# Restore original Dockerfile CMD
echo "🔧 Restoring original Dockerfile..."
sed -i 's/CMD \["\.\/start-with-debug\.sh"\]/CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]/' Dockerfile

# Remove test files
echo "🗑️  Removing test files..."
rm -f test-libmagic.py start-with-debug.sh deploy-libmagic-fix.sh

echo "✅ Rollback complete!"
echo ""
echo "🚀 To deploy rollback:"
echo "   git add ."
echo "   git commit -m 'Rollback libmagic debugging'"
echo "   git push" 