#!/bin/bash

echo "🔍 Troubleshooting Flask-Migrate import issue..."

# Check if flask-migrate is properly installed
echo "1. Checking flask-migrate installation:"
pip show flask-migrate

echo ""
echo "2. Testing import in Python:"
python -c "
try:
    import flask_migrate
    print('✅ flask_migrate imported successfully')
    print('Version:', flask_migrate.__version__)
except ImportError as e:
    print('❌ Import failed:', e)
"

echo ""
echo "3. Checking if it's a path issue:"
python -c "
import sys
print('Python path:')
for path in sys.path:
    print('  -', path)
"

echo ""
echo "4. Let's try reinstalling flask-migrate:"
pip uninstall flask-migrate -y
pip install flask-migrate

echo ""
echo "5. Verify the installation again:"
python -c "
try:
    from flask_migrate import Migrate
    print('✅ flask_migrate.Migrate imported successfully')
except ImportError as e:
    print('❌ Import still failed:', e)
    # Try alternative import
    try:
        import flask_migrate
        print('✅ But basic flask_migrate import works')
        print('Available attributes:', dir(flask_migrate))
    except ImportError as e2:
        print('❌ Even basic import fails:', e2)
"

echo ""
echo "6. If still failing, let's check your virtual environment:"
which python
which pip
echo "Virtual env: $VIRTUAL_ENV"

echo ""
echo "7. Try running your Flask app now:"
echo "flask run"
