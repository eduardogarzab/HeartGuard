ALTER TABLE org_invitations
    ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP;
