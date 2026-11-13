"""Keep the entire automated test suite offline."""

import socket

import matplotlib
import pytest

matplotlib.use("Agg")


def _block_network(*args, **kwargs):
    pytest.fail("Network access is forbidden during automated tests.")


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    monkeypatch.setattr(socket, "create_connection", _block_network)
    monkeypatch.setattr(socket.socket, "connect", _block_network)
    monkeypatch.setattr(socket.socket, "connect_ex", _block_network)
