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

.DEFAULT_GOAL = help
.PHONY: help
help:
	@echo "*****************************HELP*****************************"
	@echo "all                      clean + install"
	@echo "install                  install modules for raspi + install-systemd"
	@echo "install-debug            install modules for raspi with debugging + install-systemd"
	@echo "install-dev              install modules for development"
	@echo "install-systemd          install systemd service"
	@echo "install-systemd-debug    install systemd service with debug args"
	@echo "check                    run tests (tox)"
	@echo "build                    build python project to ${BUILD_DIR}"
	@echo "clean                    clean all generated files"

.PHONY: all
all: clean install

.PHONY: install
install: install-systemd
	${PYTHON_PIP} install .[raspi]

.PHONY: uninstall
uninstall: uninstall-systemd 
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
install-dev:
	${PYTHON_PIP} install -e .[dev]

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
