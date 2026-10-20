/**
 * Single source of truth for the Pyomo hub (/pyomo/).
 *
 * Membership rules:
 *  1. Every key listed below (curated) belongs to the hub.
 *  2. Any published note/project whose frontmatter has `pyomoCluster: <key>` belongs
 *     and is shown in that cluster automatically (no edit here).
 *  3. Any published note/project/course tagged "Pyomo" also belongs. Without a
 *     pyomoCluster it appears in the hub's "more" section.
 *
 * Keys use the form "<collection>/<slug>".
 */
import { normalizeTag, resolveCanonicalTag } from '../utils/tag-text';

export const PYOMO_HUB_URL = '/pyomo/';
export const PYOMO_HUB_TITLE = 'راهنمای جامع آموزش Pyomo';

export const PYOMO_HUB_TAGS = ['Pyomo'];

export const pyomoLadder: string[][] = [
  ['notes/mathematical-modeling-art', 'courses/optimization-modeling'],
  ['notes/pyomo-optimization-guide', 'notes/pyomo-solvers', 'notes/google-colab'],
  ['notes/gams-to-python-supply-chain-network', 'notes/gams-to-python-supplier-selection', 'notes/gams-to-python-production-inventory'],
  ['notes/pyomo-unit-commitment-guide', 'courses/intro-power-system', 'courses/advanced-power-system'],
  ['notes/bilevel-optimization-stackelberg', 'notes/kkt-conditions-examples', 'courses/uncertainty-modeling'],
];

export const pyomoClusters: Record<string, string[]> = {
  foundations: ['notes/pyomo-optimization-guide', 'notes/pyomo-solvers', 'notes/google-colab', 'notes/optimization-production-lessons'],
  gams: [
    'notes/gams-to-python-supply-chain-network',
    'notes/gams-to-python-supplier-selection',
    'notes/gams-to-python-production-inventory',
  ],
  power: [
    'notes/pyomo-unit-commitment-guide',
    'notes/ac-studies',
    'notes/dist-reconfiguration',
    'notes/uncertainty-modeling-note',
    'projects/load-hosting',
    'projects/bess-allocation',
    'projects/ev-solar',
    'projects/energy-water-system',
    'projects/community-energy-v2g-system',
  ],
  advanced: [
    'notes/bilevel-optimization-stackelberg',
    'notes/kkt-conditions-examples',
    'notes/epsilon-constraint-bi-objective',
  ],
  // Classic MILP models; several are implemented with PuLP, and the same formulation carries over to Pyomo.
  milp: [
    'notes/brick-factory-scheduling',
    'notes/cutting-stock-problem',
    'notes/seasonal-storage-arbitrage-problem',
    'notes/freight-procurement-combinatorial-auction',
    'notes/ev-charging-station-siting-milp',
    'notes/closed-loop-supply-chain',
    'notes/industrial-symbiosis-network-design',
  ],
};

export const pyomoCourses: string[] = [
  'courses/optimization-modeling',
  'courses/intro-power-system',
  'courses/advanced-power-system',
  'courses/uncertainty-modeling',
];

// Linked from the hub as starting points but not Pyomo tutorials themselves (no backlink).
const NON_MEMBER_KEYS = new Set(['notes/mathematical-modeling-art']);

export const pyomoCuratedKeys = new Set<string>([
  ...pyomoLadder.flat(),
  ...Object.values(pyomoClusters).flat(),
  ...pyomoCourses,
]);

const tagSet = new Set(PYOMO_HUB_TAGS.map((t) => normalizeTag(resolveCanonicalTag(t))));

export function hasPyomoTag(tags: string[] = []): boolean {
  return tags.some((t) => tagSet.has(normalizeTag(resolveCanonicalTag(t))));
}

export function isKnownPyomoCluster(key?: string): key is string {
  return Boolean(key && Object.prototype.hasOwnProperty.call(pyomoClusters, key));
}

/** True when a page should link back to the Pyomo hub. */
export function isPyomoHubMember(kind: string, slug: string, tags: string[] = [], pyomoCluster?: string): boolean {
  const key = `${kind}/${slug}`;
  if (NON_MEMBER_KEYS.has(key)) return false;
  return pyomoCuratedKeys.has(key) || isKnownPyomoCluster(pyomoCluster) || hasPyomoTag(tags);
}
