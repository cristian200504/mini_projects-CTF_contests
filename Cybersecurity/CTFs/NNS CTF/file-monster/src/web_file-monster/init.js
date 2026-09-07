db = db.getSiblingDB('file-monster');
db.createUser({ user: 'viewer', pwd: 'viewer', roles: [{ role: 'read', db: 'file-monster' }] });
