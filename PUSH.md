# Pushing this to GitHub

Run these from inside the unzipped folder.

```bash
git init
git add .
git commit -m "Phase 1: SQLite build, query helpers, exploration notebook"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

Create the empty repository on GitHub first, with no README, no .gitignore, and no license,
since this folder already has all three.

If git asks for a password, it wants a personal access token, not your account password.
Generate one under Settings, Developer settings, Personal access tokens, Fine-grained
tokens. Scope it to the single repository with Contents set to read and write. Paste the
token when prompted for the password.

`data/tracker.db` is gitignored on purpose. It is a build artifact and anyone who clones the
repository rebuilds it in one command.
