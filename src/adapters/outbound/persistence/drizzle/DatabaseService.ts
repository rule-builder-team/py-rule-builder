import { drizzle, NodePgDatabase } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import { config } from '../../../../main/env';
import { logger } from '../../logger'; 

export class DatabaseService {
  private static instance: DatabaseService;
  public db!: NodePgDatabase;
  private pool!: Pool;

  private constructor() {}

  public static getInstance(): DatabaseService {
    if (!DatabaseService.instance) {
      DatabaseService.instance = new DatabaseService();
    }
    return DatabaseService.instance;
  }

  
  public async connectWithRetry(maxRetries = 5): Promise<void> {
    // IMPORTANT: This Node.js service is READ-ONLY by design.
    // To enforce database access constraints at the infrastructure level, configure the connection pool
    // to use a read-only database user. This provides an extra layer of protection against accidental
    // or unintended write operations. Example: create a PostgreSQL role with only SELECT permissions
    // and configure config.databaseUri to authenticate using that role's credentials.
    this.pool = new Pool({ connectionString: config.databaseUri });
    this.db = drizzle(this.pool);

    let attempt = 1;
    let currentInterval = config.dbConnectionInterval;

    while (attempt <= maxRetries) {
      try {
       
        await this.pool.query('SELECT 1');
        console.info(`Successfully connected to the database on attempt ${attempt}.`);
        return;
      } catch (error: any) {
        console.error(`Database connection failed (Attempt ${attempt}/${maxRetries}): ${error.message}`);
        
        if (attempt === maxRetries) {
          console.error('Max connection retries reached. Halting application.');
          process.exit(1);
        }

        console.info(`Waiting ${currentInterval}ms before next connection attempt...`);
        await this.sleep(currentInterval);
        
      
        currentInterval *= 2;
        attempt++;
      }
    }
  }

  private sleep(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export const databaseService = DatabaseService.getInstance();