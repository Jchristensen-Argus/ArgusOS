"""
Unit tests for argus.modules.sales.import_pipeline (row_parser,
Importer, ImportResult).

Covers: valid imports, within-run and cross-run (seeded) duplicate
handling, malformed rows, and column mapping overrides. Event
publishing from the importer is covered by test_sales_events.py, not
duplicated here.
"""

import tempfile
import unittest
from pathlib import Path

from argus.modules.sales.campaigns import Campaign
from argus.modules.sales.companies import Company
from argus.modules.sales.contacts import Contact
from argus.modules.sales.import_pipeline import DEFAULT_COLUMN_MAPPING, Importer
from argus.modules.sales.import_pipeline.exceptions import RowParseError
from argus.modules.sales.import_pipeline.row_parser import parse_row


def _write_csv(directory: Path, name: str, content: str) -> str:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return str(path)


class RowParserTests(unittest.TestCase):
    def test_parse_row_extracts_every_mapped_field(self):
        raw_row = {
            "Company Name": "Acme",
            "Industry": "Manufacturing",
            "Email": "jane@acme.com",
        }
        fields = parse_row(
            raw_row, column_mapping=DEFAULT_COLUMN_MAPPING, row_number=1
        )
        self.assertEqual(fields["company_name"], "Acme")
        self.assertEqual(fields["company_industry"], "Manufacturing")
        self.assertEqual(fields["contact_email"], "jane@acme.com")

    def test_parse_row_strips_whitespace(self):
        raw_row = {"Company Name": "  Acme  "}
        fields = parse_row(
            raw_row, column_mapping=DEFAULT_COLUMN_MAPPING, row_number=1
        )
        self.assertEqual(fields["company_name"], "Acme")

    def test_parse_row_defaults_missing_optional_column_to_empty_string(self):
        raw_row = {"Company Name": "Acme"}
        fields = parse_row(
            raw_row, column_mapping=DEFAULT_COLUMN_MAPPING, row_number=1
        )
        self.assertEqual(fields["contact_email"], "")

    def test_parse_row_raises_on_missing_required_field(self):
        raw_row = {"Company Name": ""}
        with self.assertRaises(RowParseError):
            parse_row(raw_row, column_mapping=DEFAULT_COLUMN_MAPPING, row_number=1)

    def test_parse_row_error_message_includes_row_number(self):
        raw_row = {"Company Name": ""}
        try:
            parse_row(raw_row, column_mapping=DEFAULT_COLUMN_MAPPING, row_number=7)
            self.fail("expected RowParseError")
        except RowParseError as error:
            self.assertIn("Row 7", str(error))


class ImporterValidImportTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.dir = Path(self._tmp_dir.name)

    def test_single_row_produces_one_lead_company_contact(self):
        path = _write_csv(
            self.dir,
            "single.csv",
            "Company Name,Industry,Email,First Name,Last Name\n"
            "Acme,Manufacturing,jane@acme.com,Jane,Doe\n",
        )
        result = Importer().import_file(path)
        self.assertEqual(result.total_rows, 1)
        self.assertEqual(result.leads_created, 1)
        self.assertEqual(result.companies_created, 1)
        self.assertEqual(result.contacts_created, 1)
        self.assertEqual(result.errors, ())

    def test_lead_references_its_company_and_contact_by_id(self):
        path = _write_csv(
            self.dir,
            "single.csv",
            "Company Name,Email\nAcme,jane@acme.com\n",
        )
        result = Importer().import_file(path)
        lead = result.leads[0]
        company = result.companies[0]
        contact = result.contacts[0]
        self.assertEqual(lead.company_id, company.company_id)
        self.assertEqual(lead.contact_id, contact.contact_id)

    def test_row_with_no_campaign_produces_lead_with_blank_campaign_id(self):
        path = _write_csv(self.dir, "single.csv", "Company Name\nAcme\n")
        result = Importer().import_file(path)
        self.assertEqual(result.leads[0].campaign_id, "")
        self.assertEqual(result.campaigns_created, 0)

    def test_custom_column_mapping_is_honored(self):
        path = _write_csv(
            self.dir, "custom.csv", "Account Name\nAcme Custom Mapped\n"
        )
        custom_mapping = {"company_name": "Account Name"}
        result = Importer(column_mapping=custom_mapping).import_file(path)
        self.assertEqual(result.companies[0].name, "Acme Custom Mapped")


class ImporterWithinRunDedupTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.dir = Path(self._tmp_dir.name)

    def test_same_company_name_across_rows_is_deduped_case_insensitively(self):
        path = _write_csv(
            self.dir,
            "dupe_company.csv",
            "Company Name,Email\nAcme,a@acme.com\nACME,b@acme.com\n",
        )
        result = Importer().import_file(path)
        self.assertEqual(result.companies_created, 1)
        self.assertEqual(result.companies_reused, 1)
        self.assertEqual(len(result.companies), 1)

    def test_same_contact_email_across_rows_is_deduped_case_insensitively(self):
        path = _write_csv(
            self.dir,
            "dupe_contact.csv",
            "Company Name,Email\nAcme,Jane@Acme.com\nBeta,jane@acme.com\n",
        )
        result = Importer().import_file(path)
        self.assertEqual(result.contacts_created, 1)
        self.assertEqual(result.contacts_reused, 1)

    def test_same_campaign_name_across_rows_is_deduped(self):
        path = _write_csv(
            self.dir,
            "dupe_campaign.csv",
            "Company Name,Campaign\nAcme,Q3 Outreach\nBeta,Q3 Outreach\n",
        )
        result = Importer().import_file(path)
        self.assertEqual(result.campaigns_created, 1)
        self.assertEqual(result.campaigns_reused, 1)

    def test_leads_are_never_deduped_one_per_row(self):
        path = _write_csv(
            self.dir,
            "same_company_two_leads.csv",
            "Company Name\nAcme\nAcme\n",
        )
        result = Importer().import_file(path)
        self.assertEqual(result.leads_created, 2)
        self.assertEqual(len(result.leads), 2)
        self.assertNotEqual(result.leads[0].lead_id, result.leads[1].lead_id)


class ImporterCrossRunDedupTests(unittest.TestCase):
    """Covers Importer's `existing_*` seed parameters (Sprint 1, Slice 5)."""

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.dir = Path(self._tmp_dir.name)

    def test_seeded_company_is_reused_not_recreated(self):
        existing = Company(name="Acme")
        path = _write_csv(self.dir, "seeded.csv", "Company Name\nAcme\n")
        result = Importer(existing_companies=[existing]).import_file(path)
        self.assertEqual(result.companies_created, 0)
        self.assertEqual(result.companies_reused, 1)
        self.assertEqual(result.companies[0].company_id, existing.company_id)

    def test_seeded_contact_is_reused_not_recreated(self):
        existing = Contact(email="jane@acme.com")
        path = _write_csv(
            self.dir, "seeded.csv", "Company Name,Email\nAcme,jane@acme.com\n"
        )
        result = Importer(existing_contacts=[existing]).import_file(path)
        self.assertEqual(result.contacts_created, 0)
        self.assertEqual(result.contacts_reused, 1)
        self.assertEqual(result.contacts[0].contact_id, existing.contact_id)

    def test_seeded_campaign_is_reused_not_recreated(self):
        existing = Campaign(name="Q3 Outreach")
        path = _write_csv(
            self.dir, "seeded.csv", "Company Name,Campaign\nAcme,Q3 Outreach\n"
        )
        result = Importer(existing_campaigns=[existing]).import_file(path)
        self.assertEqual(result.campaigns_created, 0)
        self.assertEqual(result.campaigns_reused, 1)

    def test_unrelated_seeded_company_is_preserved_in_full_result_set(self):
        # result.companies is the FULL current set - a previously
        # stored Company not touched by this run's rows must still be
        # present, since the caller will save this list as a full
        # replacement of the stored collection (see result.py's
        # Asymmetry note).
        untouched = Company(name="Untouched Co")
        path = _write_csv(self.dir, "seeded.csv", "Company Name\nNew Co\n")
        result = Importer(existing_companies=[untouched]).import_file(path)
        names = {c.name for c in result.companies}
        self.assertEqual(names, {"Untouched Co", "New Co"})


class ImporterMalformedRowTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.dir = Path(self._tmp_dir.name)

    def test_row_missing_company_name_is_recorded_as_an_error(self):
        # A genuinely blank CSV line is skipped by csv.DictReader
        # itself before Importer ever sees it - to exercise the
        # malformed-row path, the row must have content in some other
        # column while leaving the required Company Name blank.
        path = _write_csv(
            self.dir, "bad.csv", "Company Name,Notes\n,missing company name\n"
        )
        result = Importer().import_file(path)
        self.assertEqual(result.failed, 1)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("company_name", result.errors[0])

    def test_a_bad_row_does_not_abort_the_rest_of_the_import(self):
        path = _write_csv(
            self.dir,
            "mixed.csv",
            "Company Name,Notes\n"
            "Good Co,first\n"
            ",no company on this row\n"
            "Another Good Co,third\n",
        )
        result = Importer().import_file(path)
        self.assertEqual(result.total_rows, 3)
        self.assertEqual(result.leads_created, 2)
        self.assertEqual(result.failed, 1)
        self.assertEqual(result.succeeded, 2)

    def test_all_bad_rows_produce_zero_leads_but_no_exception(self):
        path = _write_csv(
            self.dir,
            "all_bad.csv",
            "Company Name,Notes\n,first bad\n,second bad\n",
        )
        result = Importer().import_file(path)
        self.assertEqual(result.leads_created, 0)
        self.assertEqual(result.failed, 2)


if __name__ == "__main__":
    unittest.main()
