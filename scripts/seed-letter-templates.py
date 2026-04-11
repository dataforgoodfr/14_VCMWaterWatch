#!/usr/bin/env python3
"""Seed the LetterTemplate table in production NocoDB with the 3 existing templates.

Usage: python3 scripts/seed-letter-templates.py
"""

import json
import urllib.request

NOCODB_URL = "https://noco.services.dataforgood.fr/api/v3"
NOCODB_TOKEN = "cPgJmX2gc3ei8Fr1hX2R5bsYOgze4V2CrSSAz2c9"
NOCODB_BASE_ID = "pqc6cnm5mpnr9ka"


def api(method, path, data=None):
    req = urllib.request.Request(
        f"{NOCODB_URL}{path}",
        data=json.dumps(data).encode() if data else None,
        headers={"xc-token": NOCODB_TOKEN, "Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


# Find table ID
tables = api("GET", f"/meta/bases/{NOCODB_BASE_ID}/tables")["list"]
table_id = next(t["id"] for t in tables if t["title"] == "LetterTemplate")
print(f"Found LetterTemplate table: {table_id}")

templates = [
    {
        "Title": "Letter to the mayor",
        "Icon": "🏛️",
        "SortOrder": 1,
        "Locale": "en",
        "Active": True,
        "Content": (
            "Dear Mayor,\n\n"
            "I am writing to you as a resident of [YOUR MUNICIPALITY] to express my concern about the quality of drinking water distributed in our area.\n\n"
            "Recent analyses have shown that the levels of vinyl chloride monomer (VCM) and/or polyvinyl chloride (PVC) particles in our water supply exceed [or approach] the regulatory limits set by [RELEVANT REGULATION].\n\n"
            "As the authority responsible for the public water distribution service, I respectfully request:\n\n"
            "1. Full transparency on the latest water quality analyses for our distribution zone\n"
            "2. Information about the materials (notably PVC pipes) used in our water distribution network\n"
            "3. A concrete action plan and timeline for replacing any non-compliant infrastructure\n\n"
            "I remind you that access to safe drinking water is a fundamental right, and that the municipality has a legal obligation to ensure the quality of distributed water.\n\n"
            "I look forward to your written response within 15 days.\n\n"
            "Yours sincerely,\n"
            "[YOUR NAME]\n"
            "[YOUR ADDRESS]"
        ),
    },
    {
        "Title": "Email to water company",
        "Icon": "🏢",
        "SortOrder": 2,
        "Locale": "en",
        "Active": True,
        "Content": (
            "Dear Sir/Madam,\n\n"
            "As a customer and resident served by your water distribution network in [DISTRIBUTION ZONE], I am writing to request information about the quality of the water supplied to my home.\n\n"
            "I have become aware of concerns regarding vinyl chloride monomer (VCM) contamination in water distributed through PVC pipes. I would like to request:\n\n"
            "1. The most recent water quality analysis results for my distribution zone\n"
            "2. Information about the pipe materials used in my area\n"
            "3. Details about any planned pipe replacement or remediation programs\n"
            "4. Your company's monitoring protocol for VCM levels\n\n"
            "As a paying customer, I expect full transparency regarding the quality of the service I pay for. Safe drinking water is not optional — it is a legal obligation.\n\n"
            "Please provide a written response within 15 business days.\n\n"
            "Best regards,\n"
            "[YOUR NAME]\n"
            "[YOUR CUSTOMER REFERENCE]\n"
            "[YOUR ADDRESS]"
        ),
    },
    {
        "Title": "Letter to your MP",
        "Icon": "🏛️",
        "SortOrder": 3,
        "Locale": "en",
        "Active": True,
        "Content": (
            "Dear [MP NAME],\n\n"
            "I am writing to you as your constituent to raise a serious public health concern regarding drinking water quality in [YOUR AREA].\n\n"
            "Water analyses have revealed that the distribution zone serving our community shows [elevated/non-compliant] levels of vinyl chloride monomer (VCM), a substance classified as carcinogenic.\n\n"
            "This contamination is linked to aging PVC pipes in the water distribution network. Despite the known health risks, replacement of these pipes has been slow and insufficient.\n\n"
            "I urge you to:\n\n"
            "1. Raise this issue in Parliament and demand a national audit of PVC pipe infrastructure\n"
            "2. Push for increased funding for pipe replacement programs\n"
            "3. Advocate for stricter monitoring and public reporting of VCM levels\n"
            "4. Ensure that affected communities receive timely information and support\n\n"
            "The health of our community depends on decisive action. I look forward to hearing about the steps you will take.\n\n"
            "Yours sincerely,\n"
            "[YOUR NAME]\n"
            "[YOUR ADDRESS]\n"
            "[YOUR CONSTITUENCY]"
        ),
    },
]

for tpl in templates:
    api("POST", f"/data/{NOCODB_BASE_ID}/{table_id}/records", {"fields": tpl})
    print(f"  ✓ Inserted: {tpl['Title']}")

print("\nDone! All 3 templates seeded.")
