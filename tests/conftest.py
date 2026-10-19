# -*- coding: utf-8 -*-
"""Dung chung cho cac test: nap tu dien mot lan cho ca phien (moi bo mat 1-2 giay)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import langs  # noqa: E402


@pytest.fixture(scope="session")
def analyzer():
    return langs.Analyzer()


@pytest.fixture(scope="session")
def zh(analyzer):
    return analyzer.zh()


@pytest.fixture(scope="session")
def ko(analyzer):
    return analyzer.ko()


@pytest.fixture(scope="session")
def en(analyzer):
    return analyzer.en()
