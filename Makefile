init:
	pipenv install -d

test:
	pipenv run pytest tests

coverage:
	pipenv run pytest --cov=redfish_client --cov-report=html tests
	xdg-open htmlcov/index.html

lint:
	pipenv run pylint redfish_client

publish:
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload dist/*
