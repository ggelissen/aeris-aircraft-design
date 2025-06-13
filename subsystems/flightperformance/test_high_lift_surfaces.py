# test_flap_sizing.py
import pytest
import numpy as np
from unittest.mock import Mock, patch
from subsystems.flightperformance.high_lift_surfaces import flaps_TE_sizing
