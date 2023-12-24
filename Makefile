.PHONY: build upload clean local

local: 
	@pip3 install .

build:
	@python3 -m build

upload:
	@python3 -m twine upload --skip-existing --repository pypi dist/*

release: local build upload

test:
	@python3 -m unittest

clean:
	@rm -rf **/*/__pycache__
	@rm -rf **/*/*egg*