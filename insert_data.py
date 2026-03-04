# insert_data.py
from api.models import District, Ville, Quartier

def main():
    # Création du district
    district_abidjan, created = District.objects.get_or_create(nom="DISTRICT D'ABIDJAN")
    print(f"District: {district_abidjan.nom}")

    # Données
    villes_quartiers = {
        "ANYAMA": [
            "Anyama Centre", "Ébimpé", "Azaguié-Brida", "Azaguié-Ahoua",
            "Azaguié-M'Bromé", "Akoupé-Zeudji", "Akoupé-Zeudji PK 24",
            "Akoupé-Zeudji Palme", "Attinguié", "Attinguié Carrefour",
            "Songon Agban", "Brou Assé", "Sodefor", "Ahouabo", "Belle-Ville",
            "Château", "Débarcadère", "PK 18", "PK 22", "PK 24", "PK 26",
            "Abattoir", "Gare Anyama", "Résidentiel", "Extension Nord", "Extension Sud"
        ],
        "ABOBO": [
            "Abobo-Baoulé", "Anonkoua-Kouté", "Agbekoi", "Sagbé", "Samaké",
            "Akeikoi", "N'Dotré", "Banco", "Avocatier", "Abobo Gare",
            "Abobo Centre", "Abobo Nord", "Abobo Sud", "Abobo Danga",
            "Abobo Plaque", "Abobo Habitat", "Abobo Belleville", "Abobo Sogefiha",
            "Abobo Anador", "Abobo Derrière Rail", "Abobo Palmier", "Abobo Moni",
            "Abobo PK 18", "Abobo PK 22", "Abobo Agnissankoi",
            "Abobo Carrefour Samaké", "Abobo Étoile", "Abobo Gobelet",
            "Abobo N'Dotré Extension"
        ],
        "ADJAMÉ": [
            "Adjamé Village", "Williamsville", "Paillet", "Liberté", "Habitat",
            "Adjamé Centre", "220 Logements", "220 Logements Extension",
            "Marché d'Adjamé", "Rue des Jardins", "Cité des Arts", "Gare Routière",
            "Williamsville Gare", "Williamsville Autoroute", "Williamsville Marché",
            "Williamsville Mosquée", "Paillet Centre", "Paillet Marché",
            "Paillet Extension", "Paillet Résidentiel"
        ],
        "TREICHVILLE": [
            "Treichville Centre", "Arras", "Biafra", "Zone 3", "Zone 4",
            "Palais des Sports", "Port", "Gare", "Mosquée", "Marché de Treichville",
            "Belleville Treichville", "Anoumabo"
        ]
    }

    # Insertion
    for nom_ville, quartiers in villes_quartiers.items():
        ville, created = Ville.objects.get_or_create(
            nom=nom_ville, 
            district=district_abidjan
        )
        print(f"Ville: {nom_ville}")

        for nom_quartier in quartiers:
            quartier, created = Quartier.objects.get_or_create(
                nom=nom_quartier,
                ville=ville
            )
            if created:
                print(f"  + {nom_quartier}")

    # Ajout des rues pour Treichville
    treichville = Ville.objects.get(nom="TREICHVILLE", district=district_abidjan)
    for i in range(12, 48):
        Quartier.objects.get_or_create(nom=f"Rue {i}", ville=treichville)
        print(f"  + Rue {i}")

    print("✅ Insertion terminée!")

if __name__ == "__main__":
    main()