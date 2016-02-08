.PHONY: help clean info

help:
	@echo "This project assumes that an active Python virtualenv is present."
	@echo "The following make targets are available:"
	@echo "  update      update python dependencies"
	@echo "  clean       remove unwanted files"
	@echo "  lint        flake8 lint check"
	@echo "  test        run unit tests"
	@echo "  integration run integration tests"
	@echo "  all         refresh and run all tests and generate coverage reports"

update:
	pip install -U pip
	pip install -Ur requirements.txt

update-uwsgi: update
	pip install -Ur requirements-uwsgi.txt

update-all: update-uwsgi
	pip install -Ur requirements-test.txt

clean:
	python manage.py clean

lint: clean
	flake8 --exclude=env . > violations.flake8.txt

# FIXME right now integration tests are run
test: lint
	python manage.py test

integration: lint
	python manage.py integration

coverage: lint
	@coverage run --source=tenki manage.py test
	@coverage html
	@coverage report

info:
	@python --version
	@pip --version
	@virtualenv --version

ci: info clean integration coverage
	CODECOV_TOKEN=`cat .codecov-token` codecov

all: update-all integration coverage

server:
	python manage.py server

uwsgi:
	uwsgi --socket 127.0.0.1:5080 --wsgi-file wsgi.py
