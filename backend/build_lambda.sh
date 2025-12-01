#!/bin/bash
set -e

echo "🚀 Building Lambda packages for TaxiWatch..."
echo ""

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Run this script from the backend directory."
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -f lambda_package.zip lambda_layer.zip
echo "✅ Cleaned"
echo ""

# Create build directories
echo "📁 Creating build directories..."
mkdir -p build/lambda build/layer/python
echo "✅ Directories created"
echo ""

# Copy application code
echo "📦 Copying application code..."
cp -r app build/lambda/
cp -r alembic build/lambda/ 2>/dev/null || echo "⚠️  Alembic directory not found, skipping..."
cp alembic.ini build/lambda/ 2>/dev/null || echo "⚠️  alembic.ini not found, skipping..."
echo "✅ Application code copied"
echo ""

# Install dependencies for Lambda layer
echo "📚 Installing Python dependencies for Lambda layer..."
echo "   This may take a few minutes..."
pip install -r requirements.txt \
    -t build/layer/python/ \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --upgrade \
    --quiet

echo "✅ Dependencies installed"
echo ""

# Create Lambda package ZIP
echo "🗜️  Creating Lambda package ZIP..."
cd build/lambda
zip -r ../../lambda_package.zip . -x "*.pyc" "__pycache__/*" "*.DS_Store" -q
cd ../..
echo "✅ lambda_package.zip created"
echo ""

# Create Lambda layer ZIP
echo "🗜️  Creating Lambda layer ZIP..."
cd build/layer
zip -r ../../lambda_layer.zip . -q
cd ../..
echo "✅ lambda_layer.zip created"
echo ""

# Display results
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Lambda packages created successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
ls -lh lambda_package.zip lambda_layer.zip
echo ""
echo "📋 Next steps:"
echo "   1. Review the package sizes above"
echo "   2. cd ../terraform"
echo "   3. terraform init"
echo "   4. terraform plan"
echo "   5. terraform apply"
echo ""
echo "📖 See DEPLOYMENT_AWS.md for full deployment guide"
echo ""
