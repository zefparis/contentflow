import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "@shared/schema";
import * as supportSchema from "@shared/support";

const connectionString = process.env.DATABASE_URL!;

if (!connectionString) {
  throw new Error("DATABASE_URL environment variable is not set");
}

// Create the connection
const client = postgres(connectionString);

// Create the database instance with all schemas
export const db = drizzle(client, { 
  schema: { 
    ...schema, 
    ...supportSchema 
  } 
});

// Export the client as pool for backwards compatibility
export const pool = client;

export type Database = typeof db;