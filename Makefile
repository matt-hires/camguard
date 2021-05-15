#! /usr/bin/make -f

SHELL = /bin/bash
PYTHON := ${shell which python3}
NAME = camguard

SYSTEMD_SERVICE_NAME = ${NAME}.service
SYSTEMD_SRC_DIR := ${CURDIR}/systemd
SYSTEMD_CONF := ${SYSTEMD_SRC_DIR}/${SYSTEMD_SERVICE_NAME}
SYSTEMD_INSTALL_DIR := ${value HOME}/.config/systemd/user
SYSTEMD_INSTALL_PATH := ${SYSTEMD_INSTALL_DIR}/${SYSTEMD_SERVICE_NAME}
RECORD_PATH := ${CURDIR}/record
SETTINGS_DIR := ${CURDIR}/settings
DUMMY_SETTINGS_PATH := ${SETTINGS_DIR}/dummy.yaml
SETTINGS_FILE := settings.yaml

# ARGS-PRESET
GPIO_PIN_ARG = 23
RECORD_PATH_ARG := ${RECORD_PATH}
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
.PHONY: help
help:
	@echo "*****************************HELP*****************************"
	@echo "all                      clean + install"
	@echo "install                  install modules for raspi + install-systemd"
	@echo "install-debug            install modules for raspi with debugging + install-systemd"
	@echo "install-dev              install modules for development + dummy-settings"
	@echo "install-dummy-settings	install dummy settings"
	@echo "install-systemd          install systemd service"
	@echo "install-systemd-debug    install systemd service with debug args"
	@echo "uninstall                uninstall modules + systemd + dummy-settings"
	@echo "uninstall-systemd        uninstall systemd service"
	@echo "uninstall-dummy-settings uninstall dummy settings"
	@echo "check                    run tests (tox)"
	@echo "build                    build python project to ${BUILD_DIR}"
	@echo "clean                    clean all generated files"

.PHONY: all
all: clean install

.PHONY: install
install: install-systemd
	${PYTHON_PIP} install .[raspi]

.PHONY: uninstall
uninstall: uninstall-systemd uninstall-dummy-settings
	${PYTHON_PIP} uninstall ${NAME}

.PHONY: build
build: 
	${PYTHON_PIP} install -b ${BUILD_DIR} .  

.PHONY: check
check: 
	${PYTHON_TOX}

.PHONY: clean
clean: 
	-rm -r ${GENERATED_FILES}

# additional targets
.PHONY: install-debug
install-debug: install-systemd-debug
	${PYTHON_PIP} install -e .[raspi,debug]

.PHONY: install-dev
install-dev: install-dummy-settings
	${PYTHON_PIP} install -e .[dev]

# dummy settings
.PHONY: install-dummy-settings
install-dummy-settings:
	cp ${DUMMY_SETTINGS_PATH} ${CURDIR}/${SETTINGS_FILE}

.PHONY: uninstall-dummy-settings
uninstall-dummy-settings:
	-rm ${CURDIR}/${SETTINGS_FILE}

# systemd targets
.PHONY: install-systemd
install-systemd:
	mkdir -p ${RECORD_PATH_ARG}
	mkdir -p ${SYSTEMD_INSTALL_DIR}
	cp ${SYSTEMD_CONF} ${SYSTEMD_INSTALL_PATH}
	sed -i 's/$${PYTHON}/${subst /,\/,${PYTHON}}/g' ${SYSTEMD_INSTALL_PATH} 
	sed -i 's/$${RECORD_PATH}/${subst /,\/,${RECORD_PATH_ARG}}/g' ${SYSTEMD_INSTALL_PATH} 
	sed -i 's/$${GPIO_PIN}/${GPIO_PIN_ARG}/g' ${SYSTEMD_INSTALL_PATH} 

.PHONY: install-systemd-debug
install-systemd-debug: install-systemd
	sed -i 's/$${ARGS}/${DEBUG_ARGS}/g' ${SYSTEMD_INSTALL_PATH} 

.PHONY: uninstall-systemd
uninstall-systemd:
	-rm ${SYSTEMD_INSTALL_PATH}
