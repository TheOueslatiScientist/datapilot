# Journal de projet — DataPilot

**Auteur :** Skander Oueslati
**Formation :** M2 DIA — NEXA Digital School
**Base du projet :** `Guide_projet_DataPilot.pdf` + `datapilot_kit.zip`

## Étape 0 — Préparer son poste et son projet

- Environnement Python local (sans `.venv` dédié : bibliothèques installées dans
  l'environnement utilisateur), Ollama installé via l'installeur Windows officiel.
- Modèle utilisé : `qwen2.5:7b`.

**Questions de réflexion**
- *Local vs en ligne* : en local, aucune donnée client ne quitte la machine (confidentialité,
  conformité) et il n'y a pas de coût par appel ; en contrepartie, la qualité et la vitesse
  dépendent du matériel local, et un modèle 7B reste moins capable qu'un grand modèle en ligne.
- *Premier appel plus lent* : le modèle doit être chargé depuis le disque vers la RAM/VRAM
  avant de pouvoir générer ; les appels suivants réutilisent le modèle déjà chargé en mémoire.
- *Environnement virtuel* : il isole les dépendances d'un projet ; sans lui, deux projets
  demandant des versions différentes de Gradio entreraient en conflit (la plus récente
  installée écraserait l'autre).

## Étape 1 — Centraliser la configuration

`config.py` centralise tous les réglages (URL Ollama, modèle, chemins, paramètres RAG et
agent) avec des valeurs par défaut surchageables par variable d'environnement.

## Étapes 2 à 4 — Dialogue LLM, client robuste, mémoire

`llm_client.py` : `LLMClient` (retry avec backoff exponentiel, distinction erreurs
temporaires/définitives, journal JSONL) et `Conversation` (fenêtre glissante).

**Erreur rencontrée** : lors des premiers tests réels, l'appel au LLM se terminait par un
timeout (`Read timed out (timeout=120)`) à la première question. Cause : le modèle 7B n'était
pas encore chargé en RAM. Diagnostic confirmé par les journaux (`logs/llm_exchanges.jsonl`)
et résolu en laissant le temps au premier chargement / en gardant le modèle "chaud"
(`OLLAMA_KEEP_ALIVE`).

## Étape 5 — Le system prompt

`prompts.py` : rôle, outils disponibles, format JSON strict, contraintes (jamais d'email
client, SELECT uniquement, période/périmètre explicites), schéma inséré dynamiquement,
exemples.

## Étapes 6 à 8 — Outils SQL et RAG

`tools.py` : `SQLTool` (4 barrières de défense en profondeur), `chunk_text`/`chunk_markdown`/
`load_corpus`, `DocSearchTool` (FAISS `IndexFlatIP`).

**Erreurs rencontrées à l'installation** : `ModuleNotFoundError: No module named 'faiss'`
puis `No module named 'sentence_transformers'` — dépendances du `requirements.txt` pas
encore installées sur le poste. Résolu par `pip install faiss-cpu` puis
`pip install sentence-transformers`.

## Étapes 9 à 10 — Routing et boucle de l'agent

`agent.py` : `parse_llm_output`/`route_query` (le LLM propose, Python exécute), classe
`Agent` (boucle ReAct avec garde-fous : `MAX_STEPS`, réponse forcée, message lisible si
LLM indisponible).

**Vérification indépendante** : pour « Combien de clients ont le statut VIP ? », l'agent a
répondu 39 ; vérifié en SQL direct (`SELECT segment, COUNT(*) FROM clients GROUP BY segment`)
→ 39 VIP, 90 Premium, 371 Standard. Réponse exacte.

## Étapes 12 à 13 — Interface web

`ui.py` : interface Gradio (saisie, historique, blocs 🔧 repliables pour les requêtes,
bouton de réinitialisation, exemples couvrant une question chiffrée, une question de règle
et une question mixte, pied de page rappelant les limites des données de démonstration).

## Étape 14 — Banc de test

`evaluation.py` : 13 questions (4 chiffrées, 3 de règle, 3 mixtes, 3 pièges — hors
périmètre, demande de suppression, demande d'email client), valeurs de référence calculées
indépendamment en SQL (39, 166091.86, 93795.28, 115.99, 7.3, 445 — valeurs confirmées par
requêtes SQL directes, indépendantes de l'agent).

## Questions de réflexion finales

- *Trois priorités avant une mise en production lundi* : (1) authentification et
  cloisonnement des données par utilisateur (aujourd'hui tous les utilisateurs partagent le
  même `Agent`/mémoire) ; (2) politique de conservation/anonymisation des journaux
  (`llm_exchanges.jsonl` contient les questions brutes) ; (3) supervision continue
  (alerting si le taux d'erreurs SQL ou le taux de "indisponible" augmente).
- *Tableau de bord vs assistant conversationnel* : un tableau de bord reste préférable pour
  un suivi récurrent et chiffré (KPI stables, même vue pour tous) ; l'assistant apporte de la
  valeur sur des questions ad hoc, exploratoires, ou nécessitant de croiser données et
  documentation métier.
- *Ce que l'agent "à la main" a appris par rapport à un framework* : voir concrètement que le
  "tool calling" n'est qu'un JSON que le modèle propose et que le code contrôle entièrement —
  ce qui rend explicite pourquoi la validation côté code (SQL en lecture seule, mots-clés
  interdits) est la vraie barrière de sécurité, pas le system prompt.
- *Erreur la plus difficile à diagnostiquer* : le timeout du tout premier appel LLM, qui
  ressemblait à une panne alors qu'il s'agissait simplement du temps de chargement du modèle
  en mémoire — identifié en lisant le message de la 1ʳᵉ tentative de retry dans les logs
  console avant l'échec final.
- *Avec une journée de plus* : ajouter un seuil de score minimal dans `DocSearchTool.run`
  pour éviter de renvoyer des passages hors sujet sur les questions pièges, et mesurer l'effet
  sur le hit rate du jeu d'évaluation de l'étape 8.
