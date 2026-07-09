# Optimisation de tournée de livraison (TSP)

Ce projet résout un problème d'optimisation de tournée : trouver l'ordre de visite qui minimise le temps/la distance pour livrer plusieurs adresses à partir d'un point de départ (dépôt), en utilisant des données réelles de géolocalisation et de routage.

## Contexte

Le problème du voyageur de commerce (TSP - Traveling Salesman Problem) est un problème classique de recherche opérationnelle, à la base de nombreuses applications logistiques réelles (livraison, tournées commerciales, ramassage scolaire...). Ce projet en propose une résolution simple et une visualisation sur une carte interactive.

## Méthode

1. **Géocodage** des adresses en coordonnées GPS via l'API [OpenRouteService](https://openrouteservice.org/) (Geocoding API)
2. **Calcul des temps/distances** entre chaque paire de points via l'API Matrix d'OpenRouteService
3. **Résolution** via un algorithme glouton du plus proche voisin : à chaque étape, on se rend vers le point non visité le plus rapide à atteindre
4. **Visualisation** : récupération du tracé routier réel (API Directions) entre chaque étape de la tournée, affiché sur une carte interactive avec `folium`

## Résultats

Tournée testée sur 6 adresses autour de Rennes :
- Temps total estimé : 134.1 min
- Distance totale : 99.07 km
- Carte interactive : [voir la carte] https://kelian-esnoult.github.io/tournee-livraison-optimisee/tournee.html


## Limites

- L'algorithme du plus proche voisin est une **heuristique** : il ne garantit pas de trouver la tournée optimale, contrairement à un solveur exact (type OR-Tools ou une formulation MIP complète). Sur cet exemple, l'écart avec l'optimum n'a pas été mesuré — piste d'amélioration possible.
- Ne passe pas à l'échelle sans adaptation : au-delà de quelques dizaines de points, le nombre d'appels API (un par segment pour le tracé routier) et le temps de calcul deviennent limitants.
- Ne prend pas en compte de contraintes réalistes supplémentaires (fenêtres horaires de livraison, capacité du véhicule, plusieurs véhicules).

## Installation

```bash
git clone https://github.com/<ton-pseudo>/tournee-livraison-optimisee.git
cd tournee-livraison-optimisee
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

Crée un fichier `.env` à la racine avec ta propre clé API (gratuite sur [openrouteservice.org](https://openrouteservice.org/dev/#/signup)) :
```
ORS_API_KEY=ta_cle_ici
```

## Utilisation

```bash
python rendu.py
```

## Stack technique
Python · requests · folium · OpenRouteService API (Geocoding, Matrix, Directions)
