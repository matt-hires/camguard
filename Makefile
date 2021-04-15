#! /usr/bin/make -f

SHELL = /bin/bash
PYTHON := ${shell which python3}
NAME = camguard

SYSTEMD_SERVICE_NAME = ${NAME}.service
SYSTEMD_SRC_DIR := ${CURDIR}/systemd
SYSTEMD_CONF := ${SYSTEMD_SRC_DIR}/${SYSTEMD_SERVICE_NAME}
#SYSTEMD_INSTALL_PATH := /etc/systemd/system/${SYSTEMD_SERVICE_NAME}
SYSTEMD_INSTALL_PATH := ${CURDIR}/${SYSTEMD_SERVICE_NAME}
# ARGS-PRESET
GPIO_PIN = 23
RECORD_PATH := ${CURDIR}/record
PYTHON_PIP := ${PYTHON} -m pip

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
	@echo "all                clean + install"
	@echo "install            install modules for raspi + install-systemd"
	@echo "install-debug      install modules for raspi with debugging"
	@echo "install-dev        install modules for development"
	@echo "install-systemd    install systemd service"
	@echo "build              build python project to ${BUILD_DIR}"
	@echo "clean              clean all generated files"

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

.PHONY: clean
clean: 
	-rm -r ${GENERATED_FILES}

# additional targets
.PHONY: install-debug
install-debug:
	${PYTHON_PIP} install -e .[raspi,debug]

.PHONY: install-dev
install-dev:
	${PYTHON_PIP} install -e .[dev]

# systemd targets
.PHONY: install-systemd
install-systemd:
	cp ${SYSTEMD_CONF} ${SYSTEMD_INSTALL_PATH}
	sed -i 's/$${PYTHON}/${subst /,\/,${PYTHON}}/g' ${SYSTEMD_INSTALL_PATH} 
	sed -i 's/$${RECORD_PATH}/${subst /,\/,${RECORD_PATH}}/g' ${SYSTEMD_INSTALL_PATH} 
	sed -i 's/$${GPIO_PIN}/${GPIO_PIN}/g' ${SYSTEMD_INSTALL_PATH} 

.PHONY: uninstall-systemd
uninstall-systemd:
	-rm ${SYSTEMD_INSTALL_PATH}
