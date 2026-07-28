"""Unit tests for argus.modules.sales.leads (Lead, LeadBuilder)."""

import dataclasses
import unittest
from datetime import datetime, timezone

from argus.modules.sales.leads import (
    ILeadBuilder,
    InvalidLeadError,
    Lead,
    LeadBuilder,
    LeadMetadata,
    LeadStatus,
    LeadSyncState,
)


class LeadDefaultsTests(unittest.TestCase):
    def test_defaults(self):
        lead = Lead()
        self.assertTrue(lead.lead_id)
        self.assertEqual(lead.company_id, "")
        self.assertEqual(lead.contact_id, "")
        self.assertEqual(lead.campaign_id, "")
        self.assertEqual(lead.status, LeadStatus.NEW)
        self.assertEqual(lead.territory, "")
        self.assertEqual(lead.source, "")
        self.assertIsNone(lead.next_touch_date)
        self.assertIsNone(lead.last_touch_date)
        self.assertEqual(lead.dynamics_record_id, "")
        self.assertEqual(lead.sync_state, LeadSyncState.NOT_SYNCED)
        self.assertEqual(lead.notes, "")
        self.assertIsInstance(lead.metadata, LeadMetadata)

    def test_default_lead_id_is_unique_per_instance(self):
        self.assertNotEqual(Lead().lead_id, Lead().lead_id)

    def test_no_field_is_required_a_bare_lead_is_valid(self):
        lead = LeadBuilder().build()
        self.assertEqual(lead.company_id, "")
        self.assertEqual(lead.status, LeadStatus.NEW)


class LeadImmutabilityTests(unittest.TestCase):
    def test_status_field_immutable(self):
        lead = Lead()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            lead.status = LeadStatus.WON

    def test_lead_id_field_immutable(self):
        lead = Lead()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            lead.lead_id = "mutated"


class LeadBuilderIdentityTests(unittest.TestCase):
    def test_is_an_ileadbuilder(self):
        self.assertIsInstance(LeadBuilder(), ILeadBuilder)


class WithReferenceFieldsTests(unittest.TestCase):
    def test_with_company_id_returns_self_for_chaining(self):
        builder = LeadBuilder()
        self.assertIs(builder.with_company_id("company-1"), builder)

    def test_with_contact_id_rejects_non_string(self):
        with self.assertRaises(InvalidLeadError):
            LeadBuilder().with_contact_id(123)

    def test_with_campaign_id_rejects_none(self):
        with self.assertRaises(InvalidLeadError):
            LeadBuilder().with_campaign_id(None)


class WithStatusTests(unittest.TestCase):
    def test_with_status_returns_self_for_chaining(self):
        builder = LeadBuilder()
        self.assertIs(builder.with_status(LeadStatus.CONTACTED), builder)

    def test_with_status_is_overwritten_not_accumulated(self):
        lead = (
            LeadBuilder()
            .with_status(LeadStatus.CONTACTED)
            .with_status(LeadStatus.QUALIFIED)
            .build()
        )
        self.assertEqual(lead.status, LeadStatus.QUALIFIED)

    def test_with_status_rejects_non_status(self):
        with self.assertRaises(InvalidLeadError):
            LeadBuilder().with_status("won")

    def test_with_status_rejects_none(self):
        with self.assertRaises(InvalidLeadError):
            LeadBuilder().with_status(None)


class WithSyncStateTests(unittest.TestCase):
    def test_with_sync_state_returns_self_for_chaining(self):
        builder = LeadBuilder()
        self.assertIs(builder.with_sync_state(LeadSyncState.SYNCED), builder)

    def test_with_sync_state_rejects_non_sync_state(self):
        with self.assertRaises(InvalidLeadError):
            LeadBuilder().with_sync_state("synced")

    def test_default_sync_state_is_not_synced(self):
        self.assertEqual(LeadBuilder().build().sync_state, LeadSyncState.NOT_SYNCED)


class WithTouchDatesTests(unittest.TestCase):
    def test_with_next_touch_date_accepts_datetime(self):
        touch = datetime(2026, 8, 1, tzinfo=timezone.utc)
        lead = LeadBuilder().with_next_touch_date(touch).build()
        self.assertEqual(lead.next_touch_date, touch)

    def test_with_next_touch_date_accepts_none(self):
        lead = LeadBuilder().with_next_touch_date(None).build()
        self.assertIsNone(lead.next_touch_date)

    def test_with_next_touch_date_rejects_non_datetime(self):
        with self.assertRaises(InvalidLeadError):
            LeadBuilder().with_next_touch_date("2026-08-01")

    def test_with_last_touch_date_rejects_non_datetime(self):
        with self.assertRaises(InvalidLeadError):
            LeadBuilder().with_last_touch_date("2026-08-01")


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_populates_extra(self):
        lead = LeadBuilder().with_metadata("source", "zoominfo").build()
        self.assertEqual(lead.metadata.extra["source"], "zoominfo")

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidLeadError):
            LeadBuilder().with_metadata("", "v")


class BuildTests(unittest.TestCase):
    def test_full_chain_produces_the_expected_lead(self):
        lead = (
            LeadBuilder()
            .with_company_id("company-1")
            .with_contact_id("contact-1")
            .with_campaign_id("campaign-1")
            .with_status(LeadStatus.QUALIFIED)
            .with_territory("West")
            .with_source("zoominfo")
            .with_dynamics_record_id("dyn-123")
            .with_sync_state(LeadSyncState.SYNCED)
            .with_notes("Ready to call")
            .build()
        )
        self.assertEqual(lead.company_id, "company-1")
        self.assertEqual(lead.contact_id, "contact-1")
        self.assertEqual(lead.campaign_id, "campaign-1")
        self.assertEqual(lead.status, LeadStatus.QUALIFIED)
        self.assertEqual(lead.territory, "West")
        self.assertEqual(lead.source, "zoominfo")
        self.assertEqual(lead.dynamics_record_id, "dyn-123")
        self.assertEqual(lead.sync_state, LeadSyncState.SYNCED)
        self.assertEqual(lead.notes, "Ready to call")

    def test_build_produces_a_fresh_lead_id_each_call(self):
        builder = LeadBuilder().with_source("zoominfo")
        self.assertNotEqual(builder.build().lead_id, builder.build().lead_id)

    def test_build_after_build_does_not_mutate_the_earlier_lead(self):
        builder = LeadBuilder().with_status(LeadStatus.NEW)
        first = builder.build()
        builder.with_status(LeadStatus.WON)
        second = builder.build()
        self.assertEqual(first.status, LeadStatus.NEW)
        self.assertEqual(second.status, LeadStatus.WON)


if __name__ == "__main__":
    unittest.main()
