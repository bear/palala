.PHONY: help clean lint info server uwsgi

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

update-all: update
	pip install uwsgi
	pip install -Ur requirements-test.txt

install-hook:
	git-pre-commit-hook install --force --plugins json --plugins yaml --plugins flake8 \
                              --flake8_ignore E111,E124,E126,E201,E202,E221,E241,E302,E501,N802,N803

docker-build: update-all docker-stop
	docker-compose build
	docker-compose pull
	docker-compose rm -f

docker-start: docker-build
	docker-compose up -d

docker-stop:
	docker-compose stop

clean:
	@rm -f violations.flake8.txt
	python manage.py clean

lint:
	@rm -f violations.flake8.txt
	flake8 --exclude=env --exclude=archive . > violations.flake8.txt

test: lint
	python manage.py test

integration: lint
	python manage.py integration

webtest: docker-start
	$(eval DRIVER_IP := $(shell ./wait_for_ip.sh))
	DRIVER_IP=$(DRIVER_IP) python manage.py webtest
	docker-compose stop

coverage: lint
	@coverage run --source=palala manage.py test
	@coverage html
	@coverage report

info:
	@python --version
	@pip --version
	@virtualenv --version
	@uname -a

ci: info clean integration coverage webtest
	CODECOV_TOKEN=`cat .codecov-token` codecov

all: integration coverage

server:
	python manage.py server

uwsgi:
	uwsgi --socket 127.0.0.1:5080 --module uwsgi-app --callable application
