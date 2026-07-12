import requests
import os
import folium
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ORS_API_KEY")  # clé API openrouteservice

# 1. Transformer une adresse en coordonnées GPS
def adresse_vers_coordonnees(adresse):
    url = "https://api.openrouteservice.org/geocode/search"
    parametres = {'api_key': API_KEY, 'text': adresse, 'size': 1}

    reponse = requests.get(url, params=parametres)
    if reponse.status_code == 200:
        data = reponse.json()
        if len(data['features']) > 0:
            return data['features'][0]['geometry']['coordinates']

    print(f"Adresse introuvable : {adresse}")
    return None

# 2. REecupération des données (coordonnees + matrice des temps/distances via l'API)
def obtenir_donnees(liste_adresses):
    liste_coordonnees = []
    print("Conversion des adresses en cours...\n")

    for lieu in liste_adresses:
        coords = adresse_vers_coordonnees(lieu)
        if coords:
            print(f"{lieu.ljust(35)} -> {coords}")
            liste_coordonnees.append(coords)

    if len(liste_coordonnees) != len(liste_adresses):
        print("Erreur : impossible de geocoder toutes les adresses. Arret.")
        return None, None, None

    url_matrix = "https://api.openrouteservice.org/v2/matrix/driving-car"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    body = {"locations": liste_coordonnees, "metrics": ["distance", "duration"]}

    reponse = requests.post(url_matrix, json=body, headers=headers)
    if reponse.status_code != 200:
        print("Erreur API Matrice :", reponse.text)
        return None, None, None

    data = reponse.json()
    return liste_coordonnees, data['durations'], data['distances']

#  3. Construction : Greedy Edge (meme principe que Kruskal, avec Union-Find)
def construction_gloutonne(matrice_couts):
    """Construit une tournee en ajoutant progressivement les aretes les plus courtes
    disponibles dans tout le graphe, tant que ca ne depasse pas 2 aretes par point et
    que ca ne referme pas une boucle avant d'avoir inclus tous les points.
    Utilise une structure Union-Find pour detecter les cycles prematures, exactement
    comme dans l'algorithme de Kruskal pour l'arbre couvrant minimal."""
    n = len(matrice_couts)
    aretes = sorted(
        (matrice_couts[i][j], i, j)
        for i in range(n) for j in range(i + 1, n)
    )

    parent = list(range(n))
    degre = [0] * n
    adjacence = [[] for _ in range(n)]

    def trouver(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    aretes_utilisees = 0
    for cout, i, j in aretes:
        if aretes_utilisees == n:
            break
        if degre[i] >= 2 or degre[j] >= 2:
            continue
        racine_i, racine_j = trouver(i), trouver(j)
        if racine_i == racine_j and aretes_utilisees != n - 1:
            continue  # creerait un cycle avant d'avoir visite tout le monde
        parent[racine_i] = racine_j
        degre[i] += 1
        degre[j] += 1
        adjacence[i].append(j)
        adjacence[j].append(i)
        aretes_utilisees += 1

    tournee = [0]
    precedent, actuel = -1, 0
    while len(tournee) < n:
        suivant = adjacence[actuel][0] if adjacence[actuel][0] != precedent else adjacence[actuel][1]
        tournee.append(suivant)
        precedent, actuel = actuel, suivant
    tournee.append(0)
    return tournee

# 4. Ajout du 2-opt 
def deux_opt(tournee, matrice_couts):
    """Ameliore une tournee en testant, pour chaque paire d'aretes, si les inverser
    (reconnecter le segment entre elles dans l'autre sens) raccourcit la tournee."""
    tournee = tournee[:]
    amelioration = True

    while amelioration:
        amelioration = False
        for i in range(1, len(tournee) - 2):
            for j in range(i + 1, len(tournee) - 1):
                a, b = tournee[i - 1], tournee[i]
                c, d = tournee[j], tournee[j + 1]

                cout_actuel = matrice_couts[a][b] + matrice_couts[c][d]
                cout_apres_inversion = matrice_couts[a][c] + matrice_couts[b][d]

                if cout_apres_inversion < cout_actuel - 1e-9:
                    tournee[i:j + 1] = reversed(tournee[i:j + 1])
                    amelioration = True

    return tournee

def cout_total(tournee, matrice_couts):
    return sum(matrice_couts[tournee[k]][tournee[k + 1]] for k in range(len(tournee) - 1))

# 5. Visualisation : tracer le vrai itineraire routier sur une carte
def obtenir_itineraire_complet(tournee, liste_coordonnees):
    """Recupere le trace routier reel (liste de points lat/lon) pour toute la tournee,
    segment par segment, via l'API Directions d'OpenRouteService."""
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}

    trace_complet = []
    for i in range(len(tournee) - 1):
        depart = liste_coordonnees[tournee[i]]
        arrivee = liste_coordonnees[tournee[i + 1]]
        body = {"coordinates": [depart, arrivee]}

        reponse = requests.post(url, json=body, headers=headers)
        if reponse.status_code == 200:
            data = reponse.json()
            segment = data['features'][0]['geometry']['coordinates']  # [lon, lat]
            trace_complet.extend((lat, lon) for lon, lat in segment)
        else:
            print(f"Erreur API Directions (segment {i}) :", reponse.text)

    return trace_complet

def afficher_carte(tournee, liste_coordonnees, liste_adresses, nom_fichier="tournee.html"):
    coords_folium = [(lat, lon) for lon, lat in liste_coordonnees]
    carte = folium.Map(location=coords_folium[0], zoom_start=10)

    for i, (lat, lon) in enumerate(coords_folium):
        couleur = "red" if i == 0 else "blue"
        folium.Marker(
            location=(lat, lon),
            popup=f"{i}. {liste_adresses[i]}",
            icon=folium.Icon(color=couleur)
        ).add_to(carte)

    trace_route = obtenir_itineraire_complet(tournee, liste_coordonnees)
    folium.PolyLine(trace_route, color="green", weight=4, opacity=0.8).add_to(carte)

    carte.save(nom_fichier)
    print(f"\nCarte enregistree dans {nom_fichier} - ouvre le fichier dans un navigateur.")

# --- 6. EXECUTION ---
adresses_a_visiter = [
    "10 rue Saint-Malo, Rennes, France",
    "Mairie de Plelan-le-Grand, France",
    "Baulon, France",
    "CHU Pontchaillou, Rennes, France",
    "Monterfil, France",
    "Campus de Ker Lann, Bruz, France",
    "Quedillac, France",
    "Chartres-de-Bretagne, France",
    "Le Rheu, France",
    "Cesson-Sevigne, France",
    "Saint-Gregoire, France",
    "Betton, France",
    "Chantepie, France",
    "Vern-sur-Seiche, France",
    "Pace, France",
    "Mordelles, France",
    "Montfort-sur-Meu, France",
    "Guichen, France",
    "Bain-de-Bretagne, France",
    "Janze, France",
    "Liffre, France",
    "Melesse, France",
    "Combourg, France",
    "Vitre, France",
    "La Guerche-de-Bretagne, France",
    "Retiers, France",
    "Becherel, France",
    "Noyal-Chatillon-sur-Seiche, France",
]

coordonnees, matrice_temps, matrice_distances = obtenir_donnees(adresses_a_visiter)

if coordonnees is not None:
    tournee_initiale = construction_gloutonne(matrice_temps)
    tournee_finale = deux_opt(tournee_initiale, matrice_temps)

    temps_total = cout_total(tournee_finale, matrice_temps)
    distance_totale = cout_total(tournee_finale, matrice_distances)

    print("\n")
    print(" BILAN DE LA TOURNEE (Greedy Edge + 2-opt) :")
    print(f"Temps total estime : {temps_total / 60:.1f} minutes")
    print(f"Distance totale    : {distance_totale / 1000:.2f} km")

    feuille_de_route = [adresses_a_visiter[i] for i in tournee_finale]
    print("\n ITINERAIRE :")
    print("\n -> \n".join(feuille_de_route))

    afficher_carte(tournee_finale, coordonnees, adresses_a_visiter)
