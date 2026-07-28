"""Unit tests for argus.modules.sales.companies (Company, CompanyBuilder)."""

import dataclasses
import unittest

from argus.modules.sales.companies import (
    Company,
    CompanyBuilder,
    CompanyMetadata,
    ICompanyBuilder,
    InvalidCompanyError,
)


class CompanyDefaultsTests(unittest.TestCase):
    def test_defaults(self):
        company = Company()
        self.assertTrue(company.company_id)
        self.assertEqual(company.name, "")
        self.assertEqual(company.industry, "")
        self.assertEqual(company.website, "")
        self.assertEqual(company.territory, "")
        self.assertEqual(company.notes, "")
        self.assertIsInstance(company.metadata, CompanyMetadata)

    def test_default_company_id_is_unique_per_instance(self):
        self.assertNotEqual(Company().company_id, Company().company_id)


class CompanyImmutabilityTests(unittest.TestCase):
    def test_name_field_immutable(self):
        company = Company()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            company.name = "mutated"

    def test_company_id_field_immutable(self):
        company = Company()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            company.company_id = "mutated"


class CompanyBuilderIdentityTests(unittest.TestCase):
    def test_is_an_icompanybuilder(self):
        self.assertIsInstance(CompanyBuilder(), ICompanyBuilder)


class WithNameTests(unittest.TestCase):
    def test_with_name_returns_self_for_chaining(self):
        builder = CompanyBuilder()
        self.assertIs(builder.with_name("Acme"), builder)

    def test_with_name_is_overwritten_not_accumulated(self):
        company = CompanyBuilder().with_name("First").with_name("Second").build()
        self.assertEqual(company.name, "Second")

    def test_with_name_rejects_empty_string(self):
        with self.assertRaises(InvalidCompanyError):
            CompanyBuilder().with_name("")

    def test_with_name_rejects_none(self):
        with self.assertRaises(InvalidCompanyError):
            CompanyBuilder().with_name(None)

    def test_with_name_rejects_non_string(self):
        with self.assertRaises(InvalidCompanyError):
            CompanyBuilder().with_name(123)

    def test_build_without_name_raises_nothing_but_leaves_name_empty(self):
        # name is required to be non-empty ONLY when with_name() is
        # called with an invalid value - simply never calling
        # with_name() is not itself an error (build() performs no
        # additional validation, per the module's own convention).
        company = CompanyBuilder().build()
        self.assertEqual(company.name, "")


class WithOtherFieldsTests(unittest.TestCase):
    def test_with_industry_accepts_empty_string(self):
        company = CompanyBuilder().with_name("Acme").with_industry("").build()
        self.assertEqual(company.industry, "")

    def test_with_website_rejects_non_string(self):
        with self.assertRaises(InvalidCompanyError):
            CompanyBuilder().with_website(123)

    def test_with_territory_rejects_none(self):
        with self.assertRaises(InvalidCompanyError):
            CompanyBuilder().with_territory(None)

    def test_with_notes_is_overwritten_not_accumulated(self):
        company = (
            CompanyBuilder()
            .with_name("Acme")
            .with_notes("First")
            .with_notes("Second")
            .build()
        )
        self.assertEqual(company.notes, "Second")


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_populates_extra(self):
        company = (
            CompanyBuilder().with_name("Acme").with_metadata("source", "import").build()
        )
        self.assertEqual(company.metadata.extra["source"], "import")

    def test_with_metadata_accumulates_distinct_keys(self):
        company = (
            CompanyBuilder()
            .with_name("Acme")
            .with_metadata("a", 1)
            .with_metadata("b", 2)
            .build()
        )
        self.assertEqual(dict(company.metadata.extra), {"a": 1, "b": 2})

    def test_with_metadata_rejects_empty_key(self):
        with self.assertRaises(InvalidCompanyError):
            CompanyBuilder().with_metadata("", "v")


class BuildTests(unittest.TestCase):
    def test_full_chain_produces_the_expected_company(self):
        company = (
            CompanyBuilder()
            .with_name("Acme Packaging")
            .with_industry("Manufacturing")
            .with_website("acme.com")
            .with_territory("West")
            .with_notes("First contact")
            .build()
        )
        self.assertEqual(company.name, "Acme Packaging")
        self.assertEqual(company.industry, "Manufacturing")
        self.assertEqual(company.website, "acme.com")
        self.assertEqual(company.territory, "West")
        self.assertEqual(company.notes, "First contact")

    def test_build_produces_a_fresh_company_id_each_call(self):
        builder = CompanyBuilder().with_name("Acme")
        self.assertNotEqual(builder.build().company_id, builder.build().company_id)

    def test_build_after_build_does_not_mutate_the_earlier_company(self):
        builder = CompanyBuilder().with_name("First")
        first = builder.build()
        builder.with_name("Second")
        second = builder.build()
        self.assertEqual(first.name, "First")
        self.assertEqual(second.name, "Second")


if __name__ == "__main__":
    unittest.main()
