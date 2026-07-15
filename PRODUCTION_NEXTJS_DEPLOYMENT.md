# Production Next.js & Django Deployment Guide

This guide outlines how to deploy the new Next.js UI on Railway and route traffic correctly, while keeping your existing Django backend and APIs.

## Step 1: Deploy the Next.js Frontend on Railway

1. Go to your **Railway Dashboard**.
2. Click **New** -> **GitHub Repo** -> select the `room-nest` repository.
3. Once the service is created, click on it and go to **Settings**.
4. Scroll down to **Root Directory** and set it to: `/frontend`.
5. Under **Variables**, add the following environment variables:
   - `NEXT_PUBLIC_API_URL`: Set this to your Django backend public URL (e.g., `https://backend.roomnest.online` or your internal Railway Django service URL).
   - `NEXT_PUBLIC_SUPABASE_URL`: Your production Supabase URL.
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Your production Supabase anonymous public key.

---

## Step 2: Route `roomnest.online` to Next.js

1. Go to the settings of your newly created **Next.js service** on Railway.
2. Under **Domains**, click **Custom Domain** and enter: `roomnest.online` (and/or `www.roomnest.online`).
3. Follow the DNS instructions provided by Railway to point the custom domain to the Next.js app.

---

## Step 3: Map the Django Backend Domain

1. Go to your existing **Django service** settings on Railway.
2. Under **Domains**, map it to a subdomain (e.g., `api.roomnest.online` or a free Railway domain like `roomnest-api.up.railway.app`).
3. Ensure the backend environment variables have:
   - `CSRF_TRUSTED_ORIGINS`: Include `https://roomnest.online` and `https://www.roomnest.online`.
   - `ALLOWED_HOSTS`: Include the subdomain and `roomnest.online`.
