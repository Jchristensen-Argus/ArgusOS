"""
Unit tests for argus.modules.sales.persistence (SalesRepository,
serialization, session orchestration).

Covers: save/load round trips for all five entities, restart behavior
(a fresh SalesRepository/WorkQueue reading back what an earlier one
wrote), and corrupt-data handling. Event publishing during
import_and_persist is covered by test_sales_events.py.
"""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from argus.modules.sales.campaigns import Campaign, CampaignStatus
from argus.modules.sales.companies import Company
from argus.modules.sales.contacts import Contact
from argus.modules.sales.leads import Lead, LeadStatus, LeadSyncState
from argus.modules.sales.persistence import (
    SalesPersistenceError,
    SalesRepository,
    import_and_persist,
    load_work_queue,
    save_work_queue,
)
from argus.modules.sales.work_items import WorkItemBuilder, WorkItemStatus, WorkItemType


class RepositoryEmptyStateTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.repo = SalesRepository(base_dir=Path(self._tmp_dir.name))

    def test_load_companies_returns_empty_list_when_file_does_not_exist(self):
        self.assertEqual(self.repo.load_companies(), [])

    def test_load_work_items_returns_empty_list_when_file_does_not_exist(self):
        self.assertEqual(self.repo.load_work_items(), [])


class RepositoryRoundTripTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.repo = SalesRepository(base_dir=Path(self._tmp_dir.name))

    def test_company_round_trips(self):
        company = Company(name="Acme", industry="Manufacturing", territory="West")
        self.repo.save_companies([company])
        loaded = self.repo.load_companies()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].company_id, company.company_id)
        self.assertEqual(loaded[0].name, "Acme")
        self.assertEqual(loaded[0].industry, "Manufacturing")

    def test_contact_round_trips(self):
        contact = Contact(first_name="Jane", last_name="Doe", email="jane@acme.com")
        self.repo.save_contacts([contact])
        loaded = self.repo.load_contacts()
        self.assertEqual(loaded[0].email, "jane@acme.com")
        self.assertEqual(loaded[0].contact_id, contact.contact_id)

    def test_campaign_round_trips_status_and_dates(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        campaign = Campaign(name="Q3", status=CampaignStatus.ACTIVE, start_date=start)
        self.repo.save_campaigns([campaign])
        loaded = self.repo.load_campaigns()
        self.assertEqual(loaded[0].status, CampaignStatus.ACTIVE)
        self.assertEqual(loaded[0].start_date, start)

    def test_campaign_round_trips_none_dates(self):
        campaign = Campaign(name="Q3")
        self.repo.save_campaigns([campaign])
        loaded = self.repo.load_campaigns()
        self.assertIsNone(loaded[0].start_date)
        self.assertIsNone(loaded[0].end_date)

    def test_lead_round_trips_status_and_sync_state(self):
        lead = Lead(status=LeadStatus.QUALIFIED, sync_state=LeadSyncState.SYNCED)
        self.repo.save_leads([lead])
        loaded = self.repo.load_leads()
        self.assertEqual(loaded[0].status, LeadStatus.QUALIFIED)
        self.assertEqual(loaded[0].sync_state, LeadSyncState.SYNCED)

    def test_work_item_round_trips_type_status_and_dates(self):
        due = datetime(2026, 8, 1, tzinfo=timezone.utc)
        work_item = (
            WorkItemBuilder()
            .with_work_type(WorkItemType.CALL)
            .with_status(WorkItemStatus.PENDING)
            .with_due_date(due)
            .build()
        )
        self.repo.save_work_items([work_item])
        loaded = self.repo.load_work_items()
        self.assertEqual(loaded[0].work_type, WorkItemType.CALL)
        self.assertEqual(loaded[0].due_date, due)

    def test_metadata_round_trips(self):
        company = Company(name="Acme")
        self.repo.save_companies([company])
        loaded = self.repo.load_companies()
        self.assertEqual(loaded[0].metadata.correlation_id, company.metadata.correlation_id)
        self.assertEqual(loaded[0].metadata.version, company.metadata.version)

    def test_save_replaces_the_full_collection(self):
        first = Company(name="First")
        second = Company(name="Second")
        self.repo.save_companies([first])
        self.repo.save_companies([second])
        loaded = self.repo.load_companies()
        self.assertEqual([c.name for c in loaded], ["Second"])

    def test_save_creates_parent_directory_if_missing(self):
        nested = SalesRepository(base_dir=Path(self._tmp_dir.name) / "nested" / "dir")
        nested.save_companies([Company(name="Acme")])
        self.assertEqual(len(nested.load_companies()), 1)


class RestartBehaviorTests(unittest.TestCase):
    """A fresh SalesRepository/WorkQueue must see exactly what an
    earlier one wrote - simulating a process restart."""

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.base_dir = Path(self._tmp_dir.name)

    def test_second_repository_instance_sees_first_instances_writes(self):
        first_repo = SalesRepository(base_dir=self.base_dir)
        first_repo.save_companies([Company(name="Acme")])

        second_repo = SalesRepository(base_dir=self.base_dir)
        self.assertEqual([c.name for c in second_repo.load_companies()], ["Acme"])

    def test_work_queue_resumes_with_prior_completion_status(self):
        repo = SalesRepository(base_dir=self.base_dir)
        queue = load_work_queue(repo)
        item = WorkItemBuilder().with_notes("call them").build()
        queue.add(item)
        queue.complete(item.work_item_id, notes="closed won")
        save_work_queue(repo, queue)

        # Simulate a restart: new repository, new queue.
        resumed_repo = SalesRepository(base_dir=self.base_dir)
        resumed_queue = load_work_queue(resumed_repo)

        self.assertEqual(len(resumed_queue.all_items()), 1)
        resumed_item = resumed_queue.all_items()[0]
        self.assertEqual(resumed_item.status, WorkItemStatus.COMPLETED)
        self.assertEqual(resumed_item.notes, "closed won")
        self.assertEqual(resumed_queue.pending_items(), [])

    def test_work_queue_resume_recomputes_pending_items_from_status(self):
        repo = SalesRepository(base_dir=self.base_dir)
        queue = load_work_queue(repo)
        pending = WorkItemBuilder().build()
        done = WorkItemBuilder().with_status(WorkItemStatus.COMPLETED).build()
        queue.add(pending)
        queue.add(done)
        save_work_queue(repo, queue)

        resumed_queue = load_work_queue(SalesRepository(base_dir=self.base_dir))
        pending_ids = [i.work_item_id for i in resumed_queue.pending_items()]
        self.assertEqual(pending_ids, [pending.work_item_id])

    def test_import_and_persist_dedups_against_a_prior_runs_saved_data(self):
        repo = SalesRepository(base_dir=self.base_dir)
        csv_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: None)  # csv_dir cleanup not required for test correctness

        first_csv = csv_dir / "run1.csv"
        first_csv.write_text("Company Name\nAcme\n", encoding="utf-8")
        import_and_persist(repo, str(first_csv))

        second_repo = SalesRepository(base_dir=self.base_dir)
        second_csv = csv_dir / "run2.csv"
        second_csv.write_text("Company Name\nAcme\nBrand New Co\n", encoding="utf-8")
        result = import_and_persist(second_repo, str(second_csv))

        self.assertEqual(result.companies_created, 1)  # Brand New Co only
        self.assertEqual(result.companies_reused, 1)  # Acme, seeded from disk
        self.assertEqual(len(second_repo.load_companies()), 2)

    def test_import_and_persist_accumulates_leads_across_runs(self):
        repo = SalesRepository(base_dir=self.base_dir)
        csv_dir = Path(tempfile.mkdtemp())

        first_csv = csv_dir / "run1.csv"
        first_csv.write_text("Company Name\nAcme\n", encoding="utf-8")
        import_and_persist(repo, str(first_csv))

        second_csv = csv_dir / "run2.csv"
        second_csv.write_text("Company Name\nBeta\n", encoding="utf-8")
        import_and_persist(repo, str(second_csv))

        self.assertEqual(len(repo.load_leads()), 2)


class CorruptDataTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.base_dir = Path(self._tmp_dir.name)
        self.repo = SalesRepository(base_dir=self.base_dir)

    def test_invalid_json_raises_sales_persistence_error(self):
        path = self.base_dir / "companies.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not valid json", encoding="utf-8")
        with self.assertRaises(SalesPersistenceError):
            self.repo.load_companies()

    def test_json_that_is_not_a_list_raises_sales_persistence_error(self):
        path = self.base_dir / "companies.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"not": "a list"}', encoding="utf-8")
        with self.assertRaises(SalesPersistenceError):
            self.repo.load_companies()

    def test_record_missing_a_required_key_raises_sales_persistence_error(self):
        path = self.base_dir / "companies.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('[{"company_id": "x"}]', encoding="utf-8")
        with self.assertRaises(SalesPersistenceError):
            self.repo.load_companies()

    def test_corrupt_work_items_file_does_not_prevent_loading_companies(self):
        # Each entity type has its own file - corruption in one must
        # not affect the others.
        self.repo.save_companies([Company(name="Acme")])
        work_items_path = self.base_dir / "work_items.json"
        work_items_path.write_text("not json", encoding="utf-8")
        self.assertEqual(len(self.repo.load_companies()), 1)
        with self.assertRaises(SalesPersistenceError):
            self.repo.load_work_items()


if __name__ == "__main__":
    unittest.main()
