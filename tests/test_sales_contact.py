"""Unit tests for argus.modules.sales.contacts (Contact, ContactBuilder)."""

import dataclasses
import unittest

from argus.modules.sales.contacts import (
    Contact,
    ContactBuilder,
    ContactMetadata,
    IContactBuilder,
    InvalidContactError,
)


class ContactDefaultsTests(unittest.TestCase):
    def test_defaults(self):
        contact = Contact()
        self.assertTrue(contact.contact_id)
        self.assertEqual(contact.company_id, "")
        self.assertEqual(contact.first_name, "")
        self.assertEqual(contact.last_name, "")
        self.assertEqual(contact.email, "")
        self.assertEqual(contact.phone, "")
        self.assertEqual(contact.title, "")
        self.assertEqual(contact.notes, "")
        self.assertIsInstance(contact.metadata, ContactMetadata)

    def test_default_contact_id_is_unique_per_instance(self):
        self.assertNotEqual(Contact().contact_id, Contact().contact_id)

    def test_no_field_is_required_a_bare_contact_is_valid(self):
        # Unlike Company/Campaign, Contact has no required-non-empty
        # field - see builder.py's own module docstring.
        contact = ContactBuilder().build()
        self.assertEqual(contact.first_name, "")
        self.assertEqual(contact.email, "")


class ContactImmutabilityTests(unittest.TestCase):
    def test_email_field_immutable(self):
        contact = Contact()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            contact.email = "mutated@example.com"

    def test_contact_id_field_immutable(self):
        contact = Contact()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            contact.contact_id = "mutated"


class ContactBuilderIdentityTests(unittest.TestCase):
    def test_is_an_icontactbuilder(self):
        self.assertIsInstance(ContactBuilder(), IContactBuilder)


class WithCompanyIdTests(unittest.TestCase):
    def test_with_company_id_returns_self_for_chaining(self):
        builder = ContactBuilder()
        self.assertIs(builder.with_company_id("company-1"), builder)

    def test_with_company_id_rejects_non_string(self):
        with self.assertRaises(InvalidContactError):
            ContactBuilder().with_company_id(123)

    def test_with_company_id_rejects_none(self):
        with self.assertRaises(InvalidContactError):
            ContactBuilder().with_company_id(None)


class WithNameFieldsTests(unittest.TestCase):
    def test_with_first_name_is_overwritten_not_accumulated(self):
        contact = (
            ContactBuilder().with_first_name("First").with_first_name("Second").build()
        )
        self.assertEqual(contact.first_name, "Second")

    def test_with_last_name_accepts_empty_string(self):
        contact = ContactBuilder().with_last_name("").build()
        self.assertEqual(contact.last_name, "")

    def test_with_last_name_rejects_non_string(self):
        with self.assertRaises(InvalidContactError):
            ContactBuilder().with_last_name(123)


class WithEmailPhoneTitleTests(unittest.TestCase):
    def test_with_email_returns_self_for_chaining(self):
        builder = ContactBuilder()
        self.assertIs(builder.with_email("jane@acme.com"), builder)

    def test_with_email_rejects_none(self):
        with self.assertRaises(InvalidContactError):
            ContactBuilder().with_email(None)

    def test_with_phone_rejects_non_string(self):
        with self.assertRaises(InvalidContactError):
            ContactBuilder().with_phone(555)

    def test_with_title_is_overwritten_not_accumulated(self):
        contact = ContactBuilder().with_title("VP").with_title("Director").build()
        self.assertEqual(contact.title, "Director")


class WithMetadataTests(unittest.TestCase):
    def test_with_metadata_populates_extra(self):
        contact = ContactBuilder().with_metadata("source", "import").build()
        self.assertEqual(contact.metadata.extra["source"], "import")

    def test_with_metadata_rejects_non_string_key(self):
        with self.assertRaises(InvalidContactError):
            ContactBuilder().with_metadata(123, "v")


class BuildTests(unittest.TestCase):
    def test_full_chain_produces_the_expected_contact(self):
        contact = (
            ContactBuilder()
            .with_company_id("company-1")
            .with_first_name("Jane")
            .with_last_name("Doe")
            .with_email("jane@acme.com")
            .with_phone("555-1111")
            .with_title("VP Sales")
            .with_notes("First contact")
            .build()
        )
        self.assertEqual(contact.company_id, "company-1")
        self.assertEqual(contact.first_name, "Jane")
        self.assertEqual(contact.last_name, "Doe")
        self.assertEqual(contact.email, "jane@acme.com")
        self.assertEqual(contact.phone, "555-1111")
        self.assertEqual(contact.title, "VP Sales")
        self.assertEqual(contact.notes, "First contact")

    def test_build_produces_a_fresh_contact_id_each_call(self):
        builder = ContactBuilder().with_first_name("Jane")
        self.assertNotEqual(builder.build().contact_id, builder.build().contact_id)

    def test_build_after_build_does_not_mutate_the_earlier_contact(self):
        builder = ContactBuilder().with_first_name("First")
        first = builder.build()
        builder.with_first_name("Second")
        second = builder.build()
        self.assertEqual(first.first_name, "First")
        self.assertEqual(second.first_name, "Second")


if __name__ == "__main__":
    unittest.main()
