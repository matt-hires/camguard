#! /usr/bin/make -f

SHELL = /bin/bash
PYTHON := ${shell which python3}
NAME = camguard

SYSTEMD_SERVICE_NAME = ${NAME}.service
SYSTEMD_SRC_DIR := ${CURDIR}/systemd
SYSTEMD_CONF := ${SYSTEMD_SRC_DIR}/${SYSTEMD_SERVICE_NAME}
SYSTEMD_INSTALL_DIR := ${value HOME}/.config/systemd/user
SYSTEMD_INSTALL_PATH := ${SYSTEMD_INSTALL_DIR}/${SYSTEMD_SERVICE_NAME}
SETTINGS_INSTALL_PATH := ${value HOME}/.config/camguard
SETTINGS_DIR := ${CURDIR}/settings
DOCS_DIR := ${CURDIR}/docs
DUMMY_SETTINGS_PATH := ${SETTINGS_DIR}/dummy.yaml
RASPI_SETTINGS_PATH := ${SETTINGS_DIR}/raspi.yaml
SETTINGS_FILE := settings.yaml

# ARGS-PRESET
SETTINGS_ARGS := -c ${SETTINGS_INSTALL_PATH}
DEBUG_ARGS := -l DEBUG

PYTHON_PIP := ${PYTHON} -m pip
PYTHON_TOX := ${PYTHON} -m tox

SOURCE_DIR := ${CURDIR}/src
MODULE_DIR := ${SRC_DIR}/${NAME}
TESTS_DIR := ${CURDIR}/tests
BUILD_DIR := ${CURDIR}/build

GENERATED_FILES := ${BUILD_DIR} 
GENERATED_FILES += ${CURDIR}/dist
GENERATED_FILES += ${CURDIR}/pip-wheel-metadata
GENERATED_FILES += ${SOURCE_DIR}/${NAME}.egg-info
GENERATED_FILES += ${CURDIR}/__pycache__
GENERATED_FILES += ${MODULE_DIR}/__pycache__
GENERATED_FILES += ${TESTS_DIR}/__pycache__
GENERATED_FILES += ${CURDIR}/.tox
GENERATED_FILES += ${CURDIR}/client_secrets.json
GENERATED_FILES += ${CURDIR}/.coverage
GENERATED_FILES += ${CURDIR}/htmlcov

.DEFAULT_GOAL = help
help:
	@echo "*****************************HELP*****************************"
	@echo "all                      clean + check + install + docs-html"
	@echo "install                  install modules for raspi + install-systemd + raspi-settings"
	@echo "install-debug            install modules for raspi with debugging + install-systemd + raspi-settings"
	@echo "install-dev              install modules for development + dummy-settings"
	@echo "install-dummy-settings   install dummy settings"
	@echo "install-raspi-settings   install raspi settings"
	@echo "install-systemd          install systemd service"
	@echo "install-systemd-debug    install systemd service with debug args"
	@echo "uninstall-systemd        uninstall systemd service"
	@echo "uninstall-settings       uninstall settings"
	@echo "uninstall                uninstall modules + systemd + settings"
	@echo "check                    run tests (tox)"
	@echo "build                    build python project to ${BUILD_DIR}"
	@echo "docs-html                build html documentation in ${DOCS_DIR}"
	@echo "clean                    clean all generated files"

.PHONY: help all install uninstall build check install-debug install-dev install-dummy-settings install-raspi-settings \
uninstall-settings install-systemd install-systemd-debug uninstall-systemd docs-html

all: clean check install docs-html

install: install-systemd install-raspi-settings
	${PYTHON_PIP} install .[raspi]

uninstall: uninstall-systemd uninstall-settings
	${PYTHON_PIP} uninstall ${NAME}

build: 
	${PYTHON_PIP} install -b ${BUILD_DIR} .  

check: 
	${PYTHON_TOX}

clean: 
	-rm -r ${GENERATED_FILES}

install-debug: install-systemd-debug install-raspi-settings
	${PYTHON_PIP} install -e .[raspi,debug]

install-dev: install-dummy-settings
	${PYTHON_PIP} install -e .[dev]

install-dummy-settings:
	mkdir -p ${SETTINGS_INSTALL_PATH}
	cp ${DUMMY_SETTINGS_PATH} ${SETTINGS_INSTALL_PATH}/${SETTINGS_FILE}

install-raspi-settings:
	mkdir -p ${SETTINGS_INSTALL_PATH}
	cp -n ${RASPI_SETTINGS_PATH} ${SETTINGS_INSTALL_PATH}/${SETTINGS_FILE}

uninstall-settings:
	rm -r ${SETTINGS_INSTALL_PATH}

install-systemd:
	mkdir -p ${SYSTEMD_INSTALL_DIR}
	cp ${SYSTEMD_CONF} ${SYSTEMD_INSTALL_PATH}
	sed -i 's/$${PYTHON}/${subst /,\/,${PYTHON}}/g' ${SYSTEMD_INSTALL_PATH} 
	sed -i 's/$${SETTINGS}/${subst /,\/,${SETTINGS_ARGS}}/g' ${SYSTEMD_INSTALL_PATH} 

install-systemd-debug: install-systemd
	sed -i 's/$${ARGS}/${DEBUG_ARGS}/g' ${SYSTEMD_INSTALL_PATH} 

uninstall-systemd:
	-rm ${SYSTEMD_INSTALL_PATH}

docs-html:
	@${MAKE} -C ${DOCS_DIR} html 
