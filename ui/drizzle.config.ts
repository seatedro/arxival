// import config from "dotenv/config";
import { config } from "dotenv";
import { defineConfig } from "drizzle-kit";

config({ path: ".env.local" });

export default defineConfig({
  out: "./drizzle",
  schema: "./src/lib/schema.ts",
  dialect: "turso",
  dbCredentials: {
    url: process.env.TURSO_URL!,
    authToken: process.env.TURSO_TOKEN!,
  },
});
