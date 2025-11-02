# Aging & DDR Papers Bot

Two-part bot inspired by projects like Scitify: it aggregates recent biology-relevant papers (Aging, DDR, DNA damage, Senescence, Telomeres) from arXiv, bioRxiv, medRxiv, PubMed, and ChemRxiv, publishes a static website (GitHub Pages) listing newest → oldest, and can optionally tweet one paper on a schedule.

## Structure

- `scipaperbot/` – Python package (models, storage, Twitter client, and source fetchers)
- `scripts/` – CLI scripts to update data and post to Twitter
- `site/` – Static website (HTML/CSS/JS) loading `site/data/papers.json`
- `.github/workflows/` – GitHub Actions for updating data, deploying Pages, and tweeting

## Quick start (local)

1. Create and activate a Python 3.11+ environment
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Update data (default: 7-day lookback):

```bash
python scripts/update_papers.py --config config.yaml
```

4. Open `site/index.html` in a browser, or serve the folder with any static server.

## Twitter (optional)

- Copy `.env.example` to `.env` and fill your credentials.
- Safe defaults in `config.yaml` keep tweeting disabled and dry-run enabled.
- Test auth:

```bash
python scripts/check_twitter_auth.py
```

- Dry-run a post (no tweet will be sent):

```bash
python scripts/post_to_twitter.py --config config.yaml --max-age-days 7 --dry-run
```

- To enable real tweeting, set `twitter.enabled: true` and `twitter.dry_run: false` in `config.yaml`, and ensure `.env` is populated.

## GitHub Pages & Actions

1. Push this repository to GitHub
2. In Settings → Pages, select "GitHub Actions" as the source
3. In Actions tab, run the workflow "Update Papers and Deploy Pages" or wait for the scheduled run
4. For tweeting via Actions, add repository Secrets:
	- `TWITTER_CONSUMER_KEY`
	- `TWITTER_CONSUMER_SECRET`
	- `TWITTER_ACCESS_TOKEN`
	- `TWITTER_ACCESS_TOKEN_SECRET`

Included workflows:

- `Update Papers and Deploy Pages` – updates data and deploys the `site/` folder to Pages
- `Tweet Morning IST` – runs twice each morning IST, updates data and posts one tweet (commits posted IDs)
- `Tweet Weekly` – weekly tweet run

## Configuration

Edit `config.yaml`:

- `keywords`: list of biology-oriented keywords (Aging, DNA damage, DDR, etc.)
- `lookback_days`: how many days back to fetch
- `sources`: enable/disable, options like arXiv categories and ChemRxiv bio-only heuristic
- `site_data_path`: path to the generated JSON (`site/data/papers.json`)
- `twitter`: `enabled` and `dry_run` safety switches

## Notes

- PubMed abstracts aren’t fetched to stay simple/fast; can be extended with EFetch.
- ChemRxiv goes through Crossref; `bio_only` gate filters out obvious non-bio items.
- The site does client-side filtering by text and source.
