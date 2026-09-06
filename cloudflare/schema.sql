PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY, body TEXT NOT NULL, revision INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS routes(slug TEXT PRIMARY KEY, profile_id TEXT NOT NULL REFERENCES profiles(id),
  state TEXT NOT NULL CHECK(state IN ('enabled','suspended')), revision INTEGER NOT NULL);
