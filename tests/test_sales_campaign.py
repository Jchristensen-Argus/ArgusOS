"""Unit tests for argus.modules.sales.campaigns (Campaign, CampaignBuilder)."""

import dataclasses
import unittest
from datetime import datetime, timezone

from argus.modules.sales.campaigns import (
    Campaign,
    CampaignBuilder,
    CampaignMetadata,
    CampaignStatus,
    ICampaignBuilder,
    InvalidCampaignError,
)


class CampaignDefaultsTests(unittest.TestCase):
    def test_defaults(self):
        campaign = Campaign()
        self.assertTrue(campaign.campaign_id)
        self.assertEqual(campaign.name, "")
        self.assertEqual(campaign.description, "")
        self.assertEqual(campaign.status, CampaignStatus.DRAFT)
        self.assertEqual(campaign.territory, "")
        self.assertIsNone(campaign.start_date)
        self.assertIsNone(campaign.end_date)
        self.assertIsInstance(campaign.metadata, CampaignMetadata)

    def test_default_campaign_id_is_unique_per_instance(self):
        self.assertNotEqual(Campaign().campaign_id, Campaign().campaign_id)


class CampaignImmutabilityTests(unittest.TestCase):
    def test_status_field_immutable(self):
        campaign = Campaign()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            campaign.status = CampaignStatus.ACTIVE


class CampaignBuilderIdentityTests(unittest.TestCase):
    def test_is_an_icampaignbuilder(self):
        self.assertIsInstance(CampaignBuilder(), ICampaignBuilder)


class WithNameTests(unittest.TestCase):
    def test_with_name_returns_self_for_chaining(self):
        builder = CampaignBuilder()
        self.assertIs(builder.with_name("Q3 Outreach"), builder)

    def test_with_name_rejects_empty_string(self):
        with self.assertRaises(InvalidCampaignError):
            CampaignBuilder().with_name("")

    def test_with_name_rejects_none(self):
        with self.assertRaises(InvalidCampaignError):
            CampaignBuilder().with_name(None)


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = CampaignBuilder()
        self.assertIs(builder.with_status(CampaignStatus.ACTIVE), builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        campaign = (
            CampaignBuilder()
            .with_name("Q3")
            .with_status(CampaignStatus.ACTIVE)
            .with_status(CampaignStatus.PAUSED)
            .build()
        )
        self.assertEqual(campaign.status, CampaignStatus.PAUSED)

    def test_with_status_rejects_non_status(self):
        with self.assertRaises(InvalidCampaignError):
            CampaignBuilder().with_status("active")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidCampaignError):
            CampaignBuilder().with_status(None)

    def test_default_status_is_draft(self):
        self.assertEqual(CampaignBuilder().with_name("Q3").build().status, CampaignStatus.DRAFT)


class WithDatesTests(unittest.TestCase):
    def test_with_start_date_accepts_datetime(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        campaign = CampaignBuilder().with_name("Q3").with_start_date(start).build()
        self.assertEqual(campaign.start_date, start)

    def test_with_start_date_accepts_none(self):
        campaign = CampaignBuilder().with_name("Q3").with_start_date(None).build()
        self.assertIsNone(campaign.start_date)

    def test_with_start_date_rejects_non_datetime(self):
        with self.assertRaises(InvalidCampaignError):
            CampaignBuilder().with_start_date("2026-01-01")

    def test_with_end_date_rejects_non_datetime(self):
        with self.assertRaises(InvalidCampaignError):
            CampaignBuilder().with_end_date("2026-01-01")


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_populates_extra(self):
        campaign = (
            CampaignBuilder().with_name("Q3").with_metadata("channel", "email").build()
        )
        self.assertEqual(campaign.metadata.extra["channel"], "email")


class BuildTests(unittest.TestCase):
    def test_full_chain_produces_the_expected_campaign(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 3, 31, tzinfo=timezone.utc)
        campaign = (
            CampaignBuilder()
            .with_name("Q3 Outreach")
            .with_description("Third quarter push")
            .with_status(CampaignStatus.ACTIVE)
            .with_territory("West")
            .with_start_date(start)
            .with_end_date(end)
            .with_notes("Kickoff Monday")
            .build()
        )
        self.assertEqual(campaign.name, "Q3 Outreach")
        self.assertEqual(campaign.description, "Third quarter push")
        self.assertEqual(campaign.status, CampaignStatus.ACTIVE)
        self.assertEqual(campaign.territory, "West")
        self.assertEqual(campaign.start_date, start)
        self.assertEqual(campaign.end_date, end)
        self.assertEqual(campaign.notes, "Kickoff Monday")

    def test_build_produces_a_fresh_campaign_id_each_call(self):
        builder = CampaignBuilder().with_name("Q3")
        self.assertNotEqual(builder.build().campaign_id, builder.build().campaign_id)


if __name__ == "__main__":
    unittest.main()
