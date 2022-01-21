# https://stackoverflow.com/a/26339924
.PHONY: list
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'


%:
	@:

install:
	poetry install --remove-untracked

test:
	poetry run pytest tests

mypy:
	poetry run mypy semantic_release

fmt:
	poetry run black $(filter-out $@,$(MAKECMDGOALS))
	poetry run isort $(filter-out $@,$(MAKECMDGOALS))
