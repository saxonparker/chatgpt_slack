chatgpt_dispatch.zip: chatgpt_dispatch.py Pipfile.lock
	pylint chatgpt_dispatch.py
	rm -rf build
	mkdir -p build
	cp chatgpt_dispatch.py build
	cp -r $(shell pipenv --venv)/lib/python3.12/site-packages/* build
	rm -rf build/boto*
	cd build && zip -r ../chatgpt_dispatch.zip .
	rm -rf build
