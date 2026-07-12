# Optimisation de tournée de livraison (TSP)

Ce projet résout un problème d'optimisation de tournée : trouver l'ordre de visite qui minimise le temps de trajet pour livrer un ensemble d'adresses à partir d'un point de départ (dépôt), sur des données réelles de géolocalisation et de routage routier.

## Contexte

Le problème du voyageur de commerce (TSP - Traveling Salesman Problem) est un problème classique de recherche opérationnelle, à la base de nombreuses applications logistiques réelles (livraison, tournées commerciales, ramassage scolaire...). Ce projet explore plusieurs approches de résolution, du simple algorithme glouton jusqu'à la solution exacte, pour comprendre le compromis entre rapidité de calcul et qualité de la solution.

## Méthode retenue : Greedy Edge + 2-opt

Le projet utilise en pratique une combinaison de deux algorithmes :

**1. Construction initiale — Greedy Edge**
On liste toutes les paires de points possibles, triées par distance croissante, et on ajoute une arête à la tournée si elle respecte deux règles : aucun point ne peut avoir plus de 2 connexions, et on n'a pas le droit de refermer une boucle avant d'avoir inclus tous les points. Cette dernière contrainte est vérifiée efficacement grâce à une structure **Union-Find**, exactement le même principe que dans l'algorithme de **Kruskal** pour l'arbre couvrant minimal. Contrairement à un algorithme glouton "au fil de l'eau" comme le plus proche voisin, cette méthode regarde globalement quelles sont les arêtes les plus courtes disponibles dans tout le graphe, ce qui évite le piège classique du point isolé oublié jusqu'à la fin de la tournée.

**2. Amélioration locale — 2-opt**
On part de la tournée construite et on teste, pour chaque paire d'arêtes, si les inverser (reconnecter le segment entre elles dans l'autre sens) raccourcit la tournée totale. On répète jusqu'à ce qu'aucune inversion n'apporte plus d'amélioration. Cette étape corrige notamment les trajets qui se croisent visuellement sur la carte — un signe classique de sous-optimalité.

## Pourquoi ne pas juste calculer la solution optimale exacte ?

Le TSP appartient à la classe des problèmes **NP-difficiles** : il n'existe aucun algorithme connu qui garantisse la tournée optimale en un temps raisonnable quand le nombre de points grandit. La méthode exacte la plus efficace connue (programmation dynamique de Held-Karp) a une complexité en **O(2ⁿ × n²)** — exponentielle.

Concrètement :
- Pour **8 adresses**, ça représente environ 6 300 opérations : instantané.
- Pour les **30 adresses** de ce projet, ça représenterait environ 2³⁰ × 30² ≈ **1 milliard de milliards** d'opérations : totalement impraticable, même sur un supercalculateur.

C'est pour cette raison structurelle (et non par manque d'optimisation du code) que ce projet, comme la quasi-totalité des solutions logistiques réelles utilisées par les entreprises de livraison, se base sur une heuristique de construction rapide suivie d'une amélioration locale, plutôt que sur une résolution exacte. Sur des instances plus petites testées en cours de développement (6 à 13 points), la combinaison Greedy Edge + 2-opt s'est révélée systématiquement plus proche de l'optimum que le plus proche voisin seul, avec un écart moyen de moins de 1% par rapport à la solution exacte.

## Résultats

Tournée testée sur 30 adresses réelles autour de Rennes (Ille-et-Vilaine) :
- Temps total estimé : **[à compléter avec ton résultat]** minutes
- Distance totale : **[à compléter avec ton résultat]** km
- Carte interactive : **[lien GitHub Pages à insérer une fois généré, voir plus bas]**

## Limites

- Le Greedy Edge + 2-opt ne garantit pas la tournée optimale (seule la programmation dynamique le garantit, mais elle ne passe pas à l'échelle — voir ci-dessus).
- Le 2-opt lui-même peut rester bloqué dans un "optimum local" : il ne sait qu'inverser un segment de tournée, jamais déplacer un point isolé ailleurs dans la séquence (ce type de mouvement, appelé *or-opt*, nécessiterait un algorithme plus avancé de type 3-opt).
- Aucune contrainte réaliste supplémentaire n'est prise en compte (fenêtres horaires de livraison, capacité de véhicule, plusieurs véhicules).
- Le tracé final nécessite un appel API par segment de la tournée (29 appels pour 30 adresses) — à surveiller si le nombre d'adresses augmente fortement, en raison des limites de requêtes de l'API gratuite.

## Installation

```bash
git clone https://github.com/kelian-esnoult/tournee-livraison-optimisee.git
cd tournee-livraison-optimisee
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

Crée un fichier `.env` à la racine avec ta propre clé API (gratuite sur [openrouteservice.org](https://openrouteservice.org/dev/#/signup)) :
```
ORS_API_KEY=(le numéro de ta clé)
```

## Utilisation

```bash
python tournee_finale.py
```

## Stack technique
Python · requests · folium · OpenRouteService API (Geocoding, Matrix, Directions) · Union-Find

## Ce que ce projet m'a appris

Point de départ : un problème purement théorique de recherche opérationnelle vu en cours, sans mise en pratique. Ce projet m'a permis de :
- Manipuler une API REST réelle (authentification, gestion d'erreurs, formats de données géographiques)
- Comprendre concrètement pourquoi un algorithme glouton simple peut échouer, à travers des exemples numériques vérifiés
- Relier un algorithme de cours (Kruskal / Union-Find) à une application pratique différente de son usage habituel
- Comprendre la notion de complexité NP-difficile de façon appliquée plutôt que purement théorique, et le compromis temps de calcul / qualité de solution qui en découle dans l'industrie
