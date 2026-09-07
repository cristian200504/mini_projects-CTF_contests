import { serve } from 'bun';
import mongoose from 'mongoose';
import robots from '../public/robots.txt' with { type: 'file' };
import homepage from './index.html';

const fileSchema = new mongoose.Schema({
  name: { type: String, required: true },
});
const FileModel = mongoose.model('File', fileSchema);
const connectionString = `mongodb://%2Ftmp%2Fmongodb-27017.sock/file-monster?authSource=admin`;
const connectionOptions = {
  user: 'admin',
  pass: process.env.MONGODB_ADMIN_PW,
  dbName: 'file-monster',
  authSource: 'admin',
};
console.log('[file-monster] connection info', connectionString, connectionOptions);
await mongoose
  .connect(connectionString, connectionOptions)
  .catch((error) => console.warn(`[file-monster WARN mongo:connect]`, error));
mongoose.connection.on('error', (err) => {
  console.warn(`[file-monster WARN mongo:runtime]`, err);
});
mongoose.connection.on('disconnected', (err) => {
  console.warn(`[file-monster WARN mongo:disconnect]`, err);
});

process.on('SIGINT', async () => {
  console.log('[file-monster] SIGINT');
  await mongoose.disconnect();
  process.exit(0);
});

const filenameRegex = /^[a-zA-Z][a-zA-Z0-9\.]*$/;
const server = serve({
  routes: {
    '/': homepage,
    '/robots.txt': new Response(await Bun.file(robots).bytes()),
    '/upload': {
      async POST(req) {
        const form = await req.formData();
        const file = form.get('file');

        if (!(file instanceof File)) {
          return Response.json({ ok: false, error: 'No file uploaded' }, { status: 400 });
        }

        if (!filenameRegex.test(file.name)) {
          return Response.json({ ok: false, error: 'Invalid filename' }, { status: 400 });
        }

        const path = `/tmp/${file.name}`;
        const f = Bun.file(path);

        if (await f.exists()) {
          return Response.json({ ok: false, error: 'Filename is already in use' }, { status: 400 });
        }

        const txt = (await file.text())
          .replaceAll('"', '')
          .replaceAll("'", '')
          .replaceAll('`', '')
          .replace('FLAG', process.env.FLAG ?? 'nns{demo_flag}');
        await Bun.write(path, txt);

        const dbFile = new FileModel({
          name: file.name,
        });
        await dbFile.save();

        return Response.json({
          ok: true,
          filename: file.name,
          path,
          fileMonster: 'nom nom tasty file',
        });
      },
    },
    '/files': {
      async GET(req) {
        const files = await FileModel.find();
        return Response.json({ files });
      },
    },
  },
});

console.log(`[file-monster] listening on ${server.url}`);
