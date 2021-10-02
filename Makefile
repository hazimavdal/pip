.PHONY: build upload clean

build:
	@python3 -m build

upload:
	@python3 -m twine upload --skip-existing --repository pypi dist/*

release: build upload

test:
	@python3 -m unittest

clean:
	@rm -rf **/*/__pycache__
	@rm -rf **/*/*egg*