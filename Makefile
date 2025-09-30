publish:
	# Entrypoint to build and publish the package to PyPI.

	# Clean previous builds.
	rm -rf build/ dist/ *.egg-info/

	# Build the package.
	echo "Building package..."
	pip install --upgrade build
	python -m build

	# Check the package.
	echo "Checking package with twine..."
	pip install --upgrade twine
	python -m twine check dist/*

	# Upload to PyPI (uncomment when ready).
	echo "Ready to upload to PyPI"
	echo "Run the following command when you're ready:"
	echo "python -m twine upload dist/*"
	# python -m twine upload dist/*

prepare-dev:
	pip install -r requirements-dev.txt

test:
	PYTHONPATH=src pytest -v tests

lint:
	ruff check src --fix --unsafe-fixes
	ruff format src
	pylint src
