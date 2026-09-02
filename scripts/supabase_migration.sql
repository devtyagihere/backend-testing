-- ============================================================
-- FreightWaves — Supabase SQL Migration
-- Table: charter_inquiries
-- Run this in your Supabase SQL Editor (once only)
-- ============================================================

-- 1. Create the charter_inquiries table
CREATE TABLE IF NOT EXISTS public.charter_inquiries (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    inquiry_id  TEXT NOT NULL UNIQUE,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    email       TEXT NOT NULL,
    commodity   TEXT NOT NULL,
    parcel_mt   NUMERIC(12, 2) NOT NULL CHECK (parcel_mt > 0),
    load_port   TEXT NOT NULL,
    discharge_port TEXT NOT NULL,
    voyage_notes TEXT DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'PENDING'
                CHECK (status IN ('PENDING','UNDER REVIEW','VESSEL MATCHING','QUOTATION SENT','ACCEPTED','REJECTED'))
);

-- 2. Create index for fast queries
CREATE INDEX IF NOT EXISTS idx_charter_inquiries_created_at ON public.charter_inquiries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_charter_inquiries_status ON public.charter_inquiries(status);
CREATE INDEX IF NOT EXISTS idx_charter_inquiries_inquiry_id ON public.charter_inquiries(inquiry_id);

-- 3. Enable Row Level Security
ALTER TABLE public.charter_inquiries ENABLE ROW LEVEL SECURITY;

-- 4. Policy: Allow ANON / public to INSERT only (submit form)
CREATE POLICY "Public can submit inquiries"
    ON public.charter_inquiries
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- 5. Policy: Allow authenticated service role full access (admin reads/updates)
CREATE POLICY "Service role has full access"
    ON public.charter_inquiries
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- 6. BLOCK public SELECT — only service_role (backend) can read
-- (No SELECT policy for anon = blocked by RLS)

-- ============================================================
-- Verification query — run after migration:
-- SELECT * FROM public.charter_inquiries ORDER BY created_at DESC LIMIT 5;
-- ============================================================
