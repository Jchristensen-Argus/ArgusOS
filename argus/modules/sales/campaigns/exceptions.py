"""
Exceptions for the Argus Sales OS Campaigns package.

Purpose:
    Define the error types argus.modules.sales.campaigns itself can
    raise. Mirrors argus.modules.sales.companies.exceptions's shape.

Responsibilities:
    - CampaignError: the base exception for this package.
    - InvalidCampaignError: raised by CampaignBuilder's with_*()
      methods when given a malformed argument.

Non-Responsibilities:
    - This module performs no logic beyond defining exception types.

Dependencies:
    None.
"""


class CampaignError(Exception):
    """Base exception for the argus.modules.sales.campaigns package."""


class InvalidCampaignError(CampaignError):
    """Raised when CampaignBuilder's with_*() methods are given a
    malformed argument."""
