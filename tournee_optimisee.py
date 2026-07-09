import requests
import os
import folium
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ORS_API_KEY")  # protection de la clé API

# 1. FONCTION OUTIL : Traduire une adresse
def adresse_vers_coordonnees(adresse):
    url = "https://api.openrouteservice.org/geocode/search"
    parametres = {
        'api_key': API_KEY,
        'text': adresse,
        'size': 1
    }
    
    reponse = requests.get(url, params=parametres)
    
    if reponse.status_code == 200:
        data = reponse.json()
        if len(data['features']) > 0:
            return data['features'][0]['geometry']['coordinates']
    
    print(f"Adresse introuvable : {adresse}")
    return None

# 2. FONCTION PRINCIPALE : 
def calculer_meilleure_tournee(liste_adresses):
    
    # A. Géocodage de toutes les adresses
    liste_coordonnees = []
    print("Conversion des adresses en cours...\n")
    
    for lieu in liste_adresses:
        coords = adresse_vers_coordonnees(lieu)
        if coords:
            print(f"{lieu.ljust(30)} -> {coords}")
            liste_coordonnees.append(coords)
            
    # Sécurité : vérifier qu'on a bien trouvé les coordonnées
    if len(liste_coordonnees) != len(liste_adresses):
        print("Erreur : Impossible de geocoder toutes les adresses. Arret.")
        return None, None, None

    # B. Récupération des matrices
    url_matrix = "https://api.openrouteservice.org/v2/matrix/driving-car"
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json'
    }
    body = {
        "locations": liste_coordonnees,
        "metrics": ["distance", "duration"] 
    }
    
    reponse = requests.post(url_matrix, json=body, headers=headers)
    
    if reponse.status_code == 200:
        data = reponse.json()
        matrice_temps = data['durations']
        matrice_distances = data['distances']
    else:
        print("Erreur API Matrice :", reponse.text)
        return None, None, None

    # C. Algorithme du Plus Proche Voisin (en Temps)
    nb_lieux = len(matrice_temps)
    non_visites = list(range(1, nb_lieux))
    
    tournee = [0]
    position_actuelle = 0
    temps_total = 0
    distance_totale = 0
    
    while non_visites:
        client_le_plus_rapide = None
        temps_min = float('inf')
        
        for client in non_visites:
            temps_trajet = matrice_temps[position_actuelle][client]
            if temps_trajet < temps_min:
                temps_min = temps_trajet
                client_le_plus_rapide = client
                
        tournee.append(client_le_plus_rapide)
        non_visites.remove(client_le_plus_rapide)
        
        temps_total += temps_min
        distance_totale += matrice_distances[position_actuelle][client_le_plus_rapide]
        position_actuelle = client_le_plus_rapide
        
    # Retour au point de départ
    temps_retour = matrice_temps[position_actuelle][0]
    distance_retour = matrice_distances[position_actuelle][0]
    
    tournee.append(0)
    temps_total += temps_retour
    distance_totale += distance_retour
    
    return tournee, temps_total, distance_totale, liste_coordonnees

# 3. VISUALISATION
def obtenir_itineraire_complet(tournee, liste_coordonnees):
    """Récupère le tracé routier réel (liste de points lat/lon) pour toute la tournée,
    segment par segment, via l'API Directions d'OpenRouteService."""
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json'
    }

    trace_complet = []
    for i in range(len(tournee) - 1):
        depart = liste_coordonnees[tournee[i]]
        arrivee = liste_coordonnees[tournee[i + 1]]
        body = {"coordinates": [depart, arrivee]}

        reponse = requests.post(url, json=body, headers=headers)
        if reponse.status_code == 200:
            data = reponse.json()
            segment = data['features'][0]['geometry']['coordinates']  # [lon, lat] par point
            segment_folium = [(lat, lon) for lon, lat in segment]      # inversion pour folium
            trace_complet.extend(segment_folium)
        else:
            print(f"Erreur API Directions (segment {i}) :", reponse.text)

    return trace_complet

def afficher_carte(tournee, liste_coordonnees, liste_adresses, nom_fichier="tournee.html"):
    # Attention : l'API ORS renvoie les coordonnées en [longitude, latitude]
    # alors que folium attend [latitude, longitude] -> il faut inverser
    coords_folium = [(lat, lon) for lon, lat in liste_coordonnees]

    carte = folium.Map(location=coords_folium[0], zoom_start=11)

    for i, (lat, lon) in enumerate(coords_folium):
        couleur = "red" if i == 0 else "blue"  # le dépôt en rouge, les clients en bleu
        folium.Marker(
            location=(lat, lon),
            popup=liste_adresses[i],
            icon=folium.Icon(color=couleur)
        ).add_to(carte)

    trace_route = obtenir_itineraire_complet(tournee, liste_coordonnees)
    folium.PolyLine(trace_route, color="green", weight=4, opacity=0.8).add_to(carte)

    carte.save(nom_fichier)
    print(f"\nCarte enregistree dans {nom_fichier}, ouvre le fichier dans un navigateur.")



# 4. EXÉCUTION 
adresses_a_visiter = [
    "Rue du Bois Perrin, Rennes",
    "Mairie de Plelan-le-Grand",
    "10 rue Saint-Malo, Rennes",
    "Baulon",
    "CHU Pontchaillou, Rennes",
    "Rue du Presbytere, Monterfil",
    "Campus de KerLann, Bruz"
]

# On lance notre fonction principale
resultats = calculer_meilleure_tournee(adresses_a_visiter)

# Si la fonction n'a pas renvoyé "None" (donc s'il n'y a pas eu d'erreur)
if resultats[0] is not None: 
    tournee_finale, temps_sec, dist_m, coordonnees = resultats
    
    print("\n")
    print(" BILAN DE LA TOURNEE :")
    print(f"Temps total estime : {temps_sec / 60:.1f} minutes")
    print(f" Distance totale    : {dist_m / 1000:.2f} km")
    
    # Affichage de l'itinéraire
    feuille_de_route = [adresses_a_visiter[i] for i in tournee_finale]
    print("\n ITINERAIRE :")
    print("\n -> \n".join(feuille_de_route))

    # Génération de la carte
    afficher_carte(tournee_finale, coordonnees, adresses_a_visiter)