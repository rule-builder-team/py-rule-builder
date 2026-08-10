import { Rule, type RuleMode, type RuleType } from '../../domain/Rule';
import { type RuleRepository } from '../ports/outbound/RuleRepository';
import { type RabbitMQService } from '../../adapters/outbound/rabbitmq/RabbitMQService';

export class FirewallService {
  constructor(
    private readonly ruleRepository: RuleRepository,
    private readonly rabbitmqService: RabbitMQService
  ) {}

  async addRules(type: RuleType, mode: RuleMode, values: any[]) {
    if (mode !== 'blacklist' && mode !== 'whitelist') throw new Error('INVALID_MODE');
    if (!Array.isArray(values) || values.length === 0) throw new Error('INVALID_VALUES');

    const createdRules = values.map(value => new Rule(undefined, type, mode, value, true));
    const envelope = this.rabbitmqService.createEnvelope('CREATE_RULE', {
      type,
      mode,
      rules: createdRules.map(rule => rule.toJSON())
    });
    await this.rabbitmqService.publish('firewall-rules-queue', envelope);

    return {
      type,
      mode,
      values: createdRules.map(rule => ({ id: rule.id, value: rule.value, active: rule.active })),
      status: 'success'
    };
  }

  async deleteRules(ids: any[]) {
    this.validateIds(ids);

    const existing = await this.ruleRepository.findByIds(ids);
    if (existing.length !== ids.length) {
      throw new Error('RULE_NOT_FOUND');
    }

    // Publish delete command to RabbitMQ using standardized message envelope
    const envelope = this.rabbitmqService.createEnvelope('DELETE_RULE', {
      ids: ids
    });
    await this.rabbitmqService.publish('firewall-rules-queue', envelope);

    return { ids: ids, status: 'success', message: 'Delete command published for processing' };
  }

  async getRules(type?: string) {
    if (type && !['ip', 'domain', 'port'].includes(type)) {
      throw new Error('INVALID_TYPE_FILTER');
    }

    let rules = await this.ruleRepository.getAll();
    if (type) {
      rules = rules.filter((r: Rule) => r.type === type);
    }

    return {
      ips: rules.filter((r: Rule) => r.type === 'ip').map((r: Rule) => r.toJSON()),
      domains: rules.filter((r: Rule) => r.type === 'domain').map((r: Rule) => r.toJSON()),
      ports: rules.filter((r: Rule) => r.type === 'port').map((r: Rule) => r.toJSON())
    };
  }

  async updateRulesStatus(ids: any[], active: any) {
    this.validateIds(ids);
    if (typeof active !== 'boolean') throw new Error('INVALID_ACTIVE_STATUS');

    const existingRules = await this.ruleRepository.findByIds(ids);
    if (existingRules.length !== ids.length) throw new Error('RULE_NOT_FOUND');

    // Publish status update command to RabbitMQ using standardized message envelope
    const envelope = this.rabbitmqService.createEnvelope('UPDATE_RULE', {
      ids: ids,
      active: active
    });
    await this.rabbitmqService.publish('firewall-rules-queue', envelope);

    return { ids: ids, active: active, status: 'success', message: 'Status update command published for processing' };
  }

  private validateIds(ids: any[]) {
    if (!Array.isArray(ids) || ids.length === 0 || !ids.every(id => Number.isInteger(id))) {
      throw new Error('INVALID_IDS');
    }
  }
}