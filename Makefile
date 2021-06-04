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
DUMMY_SETTINGS_PATH := ${SETTINGS_DIR}/dummy.yaml
RASPI_SETTINGS_PATH := ${SETTINGS_DIR}/raspi.yaml
SETTINGS_FILE := settings.yaml

# ARGS-PRESET
SETTINGS_ARGS := -c ${SETTINGS_INSTALL_PATH}/${SETTINGS_FILE}
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
	@echo "install                  install modules for raspi + install-systemd + raspi-settings"
	@echo "install-debug            install modules for raspi with debugging + install-systemd + raspi-settings"
	@echo "install-dev              install modules for development + dummy-settings"
	@echo "install-dummy-settings	install dummy settings"
	@echo "install-raspi-settings	install raspi settings"
	@echo "install-systemd          install systemd service"
	@echo "install-systemd-debug    install systemd service with debug args"
	@echo "uninstall-systemd        uninstall systemd service"
	@echo "uninstall-settings       uninstall settings"
	@echo "uninstall                uninstall modules + systemd + settings"
	@echo "check                    run tests (tox)"
	@echo "build                    build python project to ${BUILD_DIR}"
	@echo "clean                    clean all generated files"

.PHONY: all
all: clean install

.PHONY: install
install: install-systemd install-raspi-settings
	${PYTHON_PIP} install .[raspi]

.PHONY: uninstall
uninstall: uninstall-systemd uninstall-settings
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
install-debug: install-systemd-debug install-raspi-settings
	${PYTHON_PIP} install -e .[raspi,debug]

.PHONY: install-dev
install-dev: install-dummy-settings
	${PYTHON_PIP} install -e .[dev]

# settings
.PHONY: install-dummy-settings
install-dummy-settings:
	mkdir -p ${SETTINGS_INSTALL_PATH}
	cp ${DUMMY_SETTINGS_PATH} ${SETTINGS_INSTALL_PATH}/${SETTINGS_FILE}

.PHONY: install-raspi-settings
install-raspi-settings:
	mkdir -p ${SETTINGS_INSTALL_PATH}
	cp ${RASPI_SETTINGS_PATH} ${SETTINGS_INSTALL_PATH}/${SETTINGS_FILE}

.PHONY: uninstall-settings
uninstall-settings:
	rm -r ${SETTINGS_INSTALL_PATH}

# systemd targets
.PHONY: install-systemd
install-systemd:
	mkdir -p ${SYSTEMD_INSTALL_DIR}
	cp ${SYSTEMD_CONF} ${SYSTEMD_INSTALL_PATH}
	sed -i 's/$${PYTHON}/${subst /,\/,${PYTHON}}/g' ${SYSTEMD_INSTALL_PATH} 
	sed -i 's/$${SETTINGS}/${subst /,\/,${SETTINGS_ARGS}}/g' ${SYSTEMD_INSTALL_PATH} 

.PHONY: install-systemd-debug
install-systemd-debug: install-systemd
	sed -i 's/$${ARGS}/${DEBUG_ARGS}/g' ${SYSTEMD_INSTALL_PATH} 

.PHONY: uninstall-systemd
uninstall-systemd:
	-rm ${SYSTEMD_INSTALL_PATH}
