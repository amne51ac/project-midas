export type CredenceTrustTier = 'validated' | 'provisional' | 'exploratory' | 'unknown';

export type CredenceRecommendedUse = 'classify' | 'rank_and_review' | 'ranking_only';

const TIER_LABEL: Record<CredenceTrustTier, string> = {
  validated: 'Validated',
  provisional: 'Provisional',
  exploratory: 'Exploratory',
  unknown: 'Unknown',
};

const USE_LABEL: Record<CredenceRecommendedUse, string> = {
  classify: 'OK to classify at default threshold',
  rank_and_review: 'Rank and review — threshold not guaranteed',
  ranking_only: 'Ranking only — do not threshold',
};

export function trustTierLabel(tier: CredenceTrustTier | string): string {
  return TIER_LABEL[tier as CredenceTrustTier] ?? tier;
}

export function recommendedUseLabel(use: CredenceRecommendedUse | string): string {
  return USE_LABEL[use as CredenceRecommendedUse] ?? use;
}

export function trustTierClass(tier: CredenceTrustTier | string): string {
  return `credence-trust credence-trust--${tier}`;
}
