chatgpt.zip: chatgpt.py Pipfile.lock
	pylint --max-line-length=120 chatgpt.py
	rm -rf build
	mkdir -p build
	cp chatgpt.py build
	cp -r $(shell pipenv --venv)/lib/python3.9/site-packages/* build
	rm -rf build/boto*
	cd build && zip -r ../chatgpt.zip .
	rm -rf build

chatgpt_dispatch.zip: chatgpt_dispatch.py Pipfile_dispatch.lock
	pylint --max-line-length=120 chatgpt_dispatch.py
	rm -rf build_dispatch
	mkdir -p build_dispatch
	cp chatgpt_dispatch.py build_dispatch
	cp -r $(shell pipenv --venv)/lib/python3.9/site-packages/* build_dispatch
	rm -rf build_dispatch/boto*
	cd build_dispatch && zip -r ../chatgpt_dispatch.zip .
	rm -rf build_dispatch

check:
	pylint --max-line-length=120 *.py
	pytest