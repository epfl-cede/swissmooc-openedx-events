IMAGE ?= swissmooc-openedx-events-dev
DOCKER ?= docker

.PHONY: build test lint shell

build:
	$(DOCKER) build -t $(IMAGE) .

test: build
	$(DOCKER) run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		-e PYTHONPATH=/workspace \
		$(IMAGE) \
		django-admin test --settings=tests.settings

lint: build
	$(DOCKER) run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		-e PYTHONPATH=/workspace \
		$(IMAGE) \
		sh -c "ruff check . && mypy swissmooc_openedx_events tests"

shell: build
	$(DOCKER) run --rm -it \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		-e PYTHONPATH=/workspace \
		$(IMAGE) \
		bash
