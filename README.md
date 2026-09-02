# IA SOC Agent — Codex CLI, MCP, Skills, RAG et frontend

Dépôt monorepo du prototype opérationnel **IA SOC Agent** :

- `skills-router/security-skill-router/` — routeur déterministe Elastic/Splunk,
  registre des skills, règles MCP et tests de routage.
- `skills/` — skills Elastic/Kibana/Observability/Security.
- `skills-splunk/` — skills Splunk et SOC.
- `skills-router/security-skill-router/skills-rag/` — RAG opérationnel et SOC,
  corpus, indexeurs, handoff de contexte, recommandations et validation des
  preuves.
- `ia-soc-backend/` — API locale qui relie le frontend au routeur et aux RAG.
- `ia-soc-frontend/` — frontend Next.js **IA SOC Agent** avec chat,
  alertes, tickets, evidence & validation, review queue et feedback loop.

## Architecture de confiance

Le routeur choisit la plateforme, le skill et le MCP avant toute exécution. Les
RAG fournissent uniquement du contexte consultatif. Les sorties MCP sont la
seule source d evidence observée. La validation sépare les faits, hypothèses,
lacunes et recommandations ; le feedback humain alimente la boucle
d amélioration sans déclencher automatiquement une action de confinement.

## Démarrage local

### Backend

```powershell
cd .\ia-soc-backend
.\start.ps1
```

### Frontend IA SOC Agent

```powershell
cd .\ia-soc-frontend
npm.cmd install
npm.cmd run dev
```

Puis ouvrir `http://localhost:3000` ou `http://localhost:3000/chat`.

## Validation

Depuis `skills-router/security-skill-router/skills-rag` :

```powershell
py .\skills_rag.py index
py .\soc_rag.py index
py .\validate_soc_rag.py
py -m unittest .\test_soc_rag.py .\test_skills_rag.py .\test_evidence_validation.py .\test_context_handoff.py -v
```

Le projet ne contient pas de secrets ni de résultats MCP réels. Les
connecteurs Elastic/Splunk doivent être configurés côté serveur, jamais dans
le navigateur.

## Publication GitHub

Le dépôt est prévu pour être publié comme un monorepo. Avant le premier push,
vérifier le remote, le nom du compte et la branche par défaut :

```powershell
git remote add origin https://github.com/<compte>/<depot>.git
git branch -M main
git add .
git commit -m "chore: publish IA SOC Agent platform"
git push -u origin main
```
