// application/ports/outbound/RuleRepository.ts
// This repository interface is READ-ONLY by design.
// All write operations (CREATE, UPDATE, DELETE) are handled exclusively by the Python service.
// The Node.js service publishes mutation commands to RabbitMQ for asynchronous processing.
import { Rule } from '../../../domain/Rule';

export interface RuleRepository {
  getAll(): Promise<Rule[]>;
  findByIds(ids: number[]): Promise<Rule[]>;
}