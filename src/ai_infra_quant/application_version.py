"""Application release identity, independent of manifest-covered legacy package bytes."""

from importlib.metadata import version

APP_VERSION = version("ai-infra-quant")
