

ARG ERIC_ENM_SLES_BASE_IMAGE_NAME=eric-enm-sles-base
ARG ERIC_ENM_SLES_BASE_IMAGE_REPO=armdocker.rnd.ericsson.se/proj-enm
ARG ERIC_ENM_SLES_BASE_IMAGE_TAG=1.40.0-10
FROM ${ERIC_ENM_SLES_BASE_IMAGE_REPO}/${ERIC_ENM_SLES_BASE_IMAGE_NAME}:${ERIC_ENM_SLES_BASE_IMAGE_TAG}



ARG BUILD_DATE=
ARG IMAGE_BUILD_VERSION=
ARG GIT_COMMIT=
ARG ISO_VERSION=
ARG RSTATE=

LABEL \
com.ericsson.product-number= "123456" \
com.ericsson.product-revision=$RSTATE \
enm_iso_version=$ISO_VERSION \
org.label-schema.name="TestSG" \
org.label-schema.build-date=$BUILD_DATE \
org.label-schema.vcs-ref=$GIT_COMMIT \
org.label-schema.vendor="Ericsson" \
org.label-schema.version=$IMAGE_BUILD_VERSION \
org.label-schema.schema-version="1.0.0-rc1"

# Docker file content goes here.. #
