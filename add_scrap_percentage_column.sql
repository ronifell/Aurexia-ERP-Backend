-- Migration script to add scrap_percentage column to part_materials table
-- Run this script if you're using direct SQL instead of the Python script

-- Check if column exists (PostgreSQL)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'part_materials' 
        AND column_name = 'scrap_percentage'
    ) THEN
        ALTER TABLE part_materials 
        ADD COLUMN scrap_percentage NUMERIC(5, 2) DEFAULT 0;
        
        RAISE NOTICE 'Column scrap_percentage added successfully';
    ELSE
        RAISE NOTICE 'Column scrap_percentage already exists';
    END IF;
END $$;

-- For SQLite (if using SQLite):
-- ALTER TABLE part_materials ADD COLUMN scrap_percentage NUMERIC(5, 2) DEFAULT 0;
