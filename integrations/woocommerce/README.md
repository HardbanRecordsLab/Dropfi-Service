# DROPIFY Fulfillment AI — WooCommerce Plugin

Sprint 4 (#9) integration. Turns any WooCommerce product into an AI-matched
DROPIFY job (photography, listing copy, video, fulfillment) in one click —
using the platform's White-Label Reseller API (#F8), not a special integration
endpoint, so it needs zero extra DROPIFY backend deployment.

## Install

1. Copy `dropify-fulfillment-ai.php` into `wp-content/plugins/dropify-fulfillment-ai/` on your WordPress site (or zip the folder and upload via **Plugins → Add New → Upload Plugin**).
2. Activate it under **Plugins**.
3. In your DROPIFY dashboard, go to **Developer / API** and create a partner API key.
4. In WordPress, go to **Settings → DROPIFY Fulfillment AI** and paste:
   - **DROPIFY API URL** — e.g. `https://api.yourdomain.com/api`
   - **Partner API key** — the `dpk_...` key from step 3
5. Optionally enable **Auto-create on publish** to post a job automatically for every new product.

## Use

Open any WooCommerce product → the **DROPIFY Fulfillment AI** box in the sidebar →
**Create DROPIFY job**. The job appears instantly in the store owner's DROPIFY
dashboard, gets AI-matched to freelancers within seconds, and its status can be
refreshed from the same box.

## What it talks to

- `POST {api_url}/v1/external/jobs` (partner-key auth) — creates the job.
- `GET {api_url}/jobs/{id}` (public read) — refreshes status.

Both are existing, tested DROPIFY backend endpoints (`backend/app/routes/developer.py`,
`backend/app/routes/jobs.py`) — this plugin adds no new backend surface area.
