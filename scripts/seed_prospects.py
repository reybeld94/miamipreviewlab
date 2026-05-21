"""
Inserta 5 prospects de prueba (datos ficticios pero realistas).
Solo correr en desarrollo: python scripts/seed_prospects.py
"""
import sqlite3, json
from pathlib import Path

DB_PATH = Path("/opt/miamipreviewlab/data/mpl.db")

PROSPECTS = [
    {
        "source": "seed",
        "source_external_id": "seed-001",
        "business_name": "Barbería El Rey",
        "vertical": "belleza",
        "category_detail": "barber_shop",
        "address": "1245 W 49th St, Hialeah, FL 33012",
        "city": "hialeah",
        "zip": "33012",
        "lat": 25.8620,
        "lng": -80.3040,
        "phone": "(305) 555-0101",
        "google_rating": 4.6,
        "google_review_count": 87,
        "has_website": 0,
        "has_online_booking": 0,
        "has_whatsapp": 1,
        "instagram_handle": "barberia_elrey_hialeah",
        "opportunity_score": 82,
        "score_breakdown_json": json.dumps({"no_website": 40, "good_rating_high_volume": 20, "ig_active": 15}),
        "proposed_value": "Web + reserva online para reducir llamadas y capturar clientes nocturnos",
        "status": "shortlisted",
    },
    {
        "source": "seed",
        "source_external_id": "seed-002",
        "business_name": "Salón Uñas Mariposa",
        "vertical": "belleza",
        "category_detail": "nail_salon",
        "address": "3890 W 16th Ave, Hialeah, FL 33012",
        "city": "hialeah",
        "zip": "33012",
        "lat": 25.8451,
        "lng": -80.3021,
        "phone": "(305) 555-0202",
        "website_url": "http://salonmariposa.weebly.com",
        "google_rating": 4.2,
        "google_review_count": 43,
        "has_website": 1,
        "website_quality_score": 28,
        "has_online_booking": 0,
        "mobile_friendly": 0,
        "https": 0,
        "instagram_handle": "unas_mariposa",
        "opportunity_score": 75,
        "score_breakdown_json": json.dumps({"has_website": -25, "bad_website_quality": 30, "good_rating_high_volume": 20}),
        "proposed_value": "Reemplazar sitio Weebly por web moderna + galería + Booksy embed",
        "status": "shortlisted",
    },
    {
        "source": "seed",
        "source_external_id": "seed-003",
        "business_name": "Estudio de Belleza Carmen",
        "vertical": "belleza",
        "category_detail": "hair_salon",
        "address": "7820 NW 103rd St, Miami, FL 33016",
        "city": "miami",
        "zip": "33016",
        "lat": 25.9023,
        "lng": -80.3301,
        "phone": "(305) 555-0303",
        "website_url": "https://bellezacarmen.com",
        "google_rating": 4.8,
        "google_review_count": 112,
        "has_website": 1,
        "website_quality_score": 55,
        "has_online_booking": 0,
        "mobile_friendly": 1,
        "https": 1,
        "opportunity_score": 61,
        "score_breakdown_json": json.dumps({"has_website": -25, "good_rating_high_volume": 20, "no_online_booking": 25}),
        "proposed_value": "Integrar reserva online (Vagaro/Fresha) al sitio existente",
        "status": "discovered",
    },
    {
        "source": "seed",
        "source_external_id": "seed-004",
        "business_name": "Plomería Rápida Miami",
        "vertical": "hogar",
        "category_detail": "plumber",
        "address": "5510 W 20th Ave, Hialeah, FL 33016",
        "city": "hialeah",
        "zip": "33016",
        "lat": 25.8512,
        "lng": -80.3189,
        "phone": "(305) 555-0404",
        "google_rating": 4.4,
        "google_review_count": 58,
        "has_website": 0,
        "has_online_booking": 0,
        "has_whatsapp": 1,
        "opportunity_score": 78,
        "score_breakdown_json": json.dumps({"no_website": 40, "good_rating_high_volume": 20}),
        "proposed_value": "Landing page + cotización online + WhatsApp CTA para emergencias 24h",
        "status": "reviewed",
    },
    {
        "source": "seed",
        "source_external_id": "seed-005",
        "business_name": "Jardinería Los Hermanos",
        "vertical": "hogar",
        "category_detail": "landscaping",
        "address": "1100 NW 87th Ave, Miami, FL 33172",
        "city": "miami",
        "zip": "33172",
        "lat": 25.7751,
        "lng": -80.3501,
        "phone": "(305) 555-0505",
        "website_url": "http://jardinerialoshermanos.godaddysites.com",
        "google_rating": 3.9,
        "google_review_count": 21,
        "has_website": 1,
        "website_quality_score": 22,
        "has_online_booking": 0,
        "mobile_friendly": 0,
        "https": 0,
        "instagram_handle": "jardines_loshermanos",
        "opportunity_score": 70,
        "score_breakdown_json": json.dumps({"has_website": -25, "bad_website_quality": 30, "godaddy": -5}),
        "proposed_value": "Abandonar GoDaddy site, web nueva con galería de trabajos + formulario de presupuesto",
        "status": "discovered",
    },
]


def seed():
    db = sqlite3.connect(str(DB_PATH))
    inserted = 0
    skipped = 0
    for p in PROSPECTS:
        cols = list(p.keys())
        placeholders = ", ".join("?" for _ in cols)
        vals = list(p.values())
        try:
            db.execute(
                f"INSERT INTO prospects ({', '.join(cols)}) VALUES ({placeholders})",
                vals,
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    db.commit()
    db.close()
    print(f"Seed completo: {inserted} insertados, {skipped} ya existían.")


if __name__ == "__main__":
    seed()
