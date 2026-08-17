# deploy-pages.yml

This workflow automatically deploys the `frontend/` folder to GitHub Pages every time a relevant change is pushed to `main`.

---

## When it runs

```yaml
on:
  push:
    branches: ["main"]
    paths:
      - "frontend/**"
      - ".github/workflows/deploy-pages.yml"
  workflow_dispatch:
```

- **On push to `main`** — but only if the push touches a file inside `frontend/` or this workflow file itself. A push that only changes `terraform/` or `README.md` does not trigger it.
- **`workflow_dispatch`** — lets you trigger it manually from the GitHub Actions tab without making a commit.

---

## Permissions

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

These are the minimum GitHub token permissions needed:

| Permission | Why |
|---|---|
| `contents: read` | Checkout the repository code |
| `pages: write` | Publish to GitHub Pages |
| `id-token: write` | Get a short-lived OIDC token to authenticate with GitHub Pages securely — no stored secrets needed |

---

## Concurrency

```yaml
concurrency:
  group: pages
  cancel-in-progress: true
```

If two pushes happen in quick succession, only the latest deployment runs. The in-progress one is cancelled. This prevents two deployments racing and potentially publishing an older version on top of a newer one.

---

## Steps

### 1. Checkout
```yaml
- uses: actions/checkout@v4
```
Downloads the repository code onto the runner so the rest of the steps can access it.

### 2. Configure Pages
```yaml
- uses: actions/configure-pages@v5
```
Validates that GitHub Pages is enabled for this repository and configured to use GitHub Actions as the source. If Pages is not enabled, this step fails with a clear error.

### 3. Upload frontend
```yaml
- uses: actions/upload-pages-artifact@v3
  with:
    path: frontend
```
Packages the entire `frontend/` folder into a Pages artifact — a zip that GitHub's deployment infrastructure knows how to publish. Only the `frontend/` folder is included, not the rest of the repository.

### 4. Deploy
```yaml
- id: deployment
  uses: actions/deploy-pages@v4
```
Publishes the artifact from the previous step to GitHub Pages. After this step completes, the live URL is available as `steps.deployment.outputs.page_url` and shown in the Actions log and on the environment summary.

---

## Environment

```yaml
environment:
  name: github-pages
  url: ${{ steps.deployment.outputs.page_url }}
```

This links the deployment to the built-in `github-pages` environment, which shows the live URL directly in the pull request and on the Actions run summary.

---

## What does NOT happen here

- No Node.js, no build step, no `npm install` — the frontend is plain HTML/CSS/JS with no build process.
- No AWS credentials — the frontend only needs the Lambda URL in `config.js`, which is a static file committed to the repo.
- No test step — tests for the Lambda function are run separately via `python3 -m unittest` locally.
