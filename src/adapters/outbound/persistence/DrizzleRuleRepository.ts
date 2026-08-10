import { inArray } from 'drizzle-orm';
import { Rule, type RuleMode, type RuleType } from '../../../domain/Rule';
import { type RuleRepository } from '../../../application/ports/outbound/RuleRepository';
import { DatabaseService } from './drizzle/DatabaseService';
import { rulesTable } from './drizzle/schema';

// This repository is READ-ONLY by design to enforce CQRS separation.
// All write operations are handled by the Python service and published via RabbitMQ.
export class DrizzleRuleRepository implements RuleRepository {
  private db = DatabaseService.getInstance().db;


  private mapToDomain(row: any): Rule {
    const value = row.type === 'port' ? Number(row.value) : row.value;
    return new Rule(row.id, row.type as RuleType, row.mode as RuleMode, value, row.active);
  }

  async getAll(): Promise<Rule[]> {
    const rows = await this.db.select().from(rulesTable);
    return rows.map(this.mapToDomain);
  }

  async findByIds(ids: number[]): Promise<Rule[]> {
    const rows = await this.db.select()
      .from(rulesTable)
      .where(inArray(rulesTable.id, ids));
    return rows.map(this.mapToDomain);
  }
}