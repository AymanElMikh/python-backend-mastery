#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# python-backend-mastery — One-shot setup script
# Run: bash setup.sh
# ─────────────────────────────────────────────────────────────────

set -e

REPO="python-backend-mastery"

echo "🚀 Setting up $REPO..."

# 1. Create all category folders with .gitkeep
CATEGORIES=(
  "python_core"
  "oop"
  "design_patterns"
  "clean_architecture"
  "fastapi"
  "flask"
  "unit_tests"
  "async_python"
  "databases"
  "security"
  "performance"
  "devops_backend"
  "data_structures_algorithms"
  "api_design"
  "testing_advanced"
)

for cat in "${CATEGORIES[@]}"; do
  mkdir -p "$cat"
  touch "$cat/.gitkeep"
  echo "  ✅ Created folder: $cat/"
done

# 2. Git init
git init
echo "  ✅ Git initialized"

# 3. Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
.env
.venv/
venv/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
dist/
build/
EOF
echo "  ✅ .gitignore created"

# 4. Create requirements.txt (all deps concepts might use)
cat > requirements.txt << 'EOF'
fastapi>=0.110.0
uvicorn>=0.29.0
flask>=3.0.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pydantic>=2.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
httpx>=0.27.0
aiohttp>=3.9.0
redis>=5.0.0
celery>=5.3.0
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
hypothesis>=6.100.0
EOF
echo "  ✅ requirements.txt created"

# 5. Initial commit
git add .
git commit -m "init: python-backend-mastery repo structure"
echo "  ✅ Initial commit done"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. gh repo create python-backend-mastery --public --source=. --push"
echo "  2. Open in VS Code: code ."
echo "  3. Open Claude agent → paste contents of AGENT_PROMPT.md as system prompt"
echo "  4. Type: 'New session — python_core'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"