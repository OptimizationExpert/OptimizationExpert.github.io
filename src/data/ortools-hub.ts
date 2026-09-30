/**
 * Single source of truth for the OR-Tools hub (/ortools/).
 *
 * Membership rules:
 *  1. Every key listed below (curated) belongs to the hub.
 *  2. Any published note/project/course tagged with one of HUB_TAGS also
 *     belongs, even if it is not curated yet. Such entries appear in the
 *     hub's "more tutorials" section until they are placed in a cluster.
 *
 * Keys use the form "<collection>/<slug>".
 */
import { normalizeTag, resolveCanonicalTag } from '../utils/tag-text';

export type HubKind = 'notes' | 'projects' | 'courses';

export const ORTOOLS_HUB_URL = '/ortools/';
export const ORTOOLS_HUB_TITLE = 'راهنمای جامع آموزش OR-Tools';

export const HUB_TAGS = ['OR-Tools', 'CP-SAT', 'ortools'];

export const ortoolsLadder: string[][] = [
  ['notes/mathematical-modeling-art', 'courses/optimization-modeling'],
  ['notes/cp-intro', 'notes/puzzle-calendar-cp', 'notes/domino-fit-cp'],
  ['notes/job-shop-scheduling-cp-sat', 'notes/brick-factory-scheduling', 'notes/crew-pairing-problem'],
  ['notes/generalized-vehicle-routing-problem', 'projects/dynamic-vrp-reoptimization', 'courses/vrp-python'],
];

export const ortoolsClusters: Record<string, string[]> = {
  scheduling: [
    'notes/job-shop-scheduling-cp-sat',
    'notes/brick-factory-scheduling',
    'notes/berth-allocation-problem',
    'notes/crew-pairing-problem',
    'notes/radiotherapy-scheduling-optimization',
    'projects/butchery-inspection-scheduling',
  ],
  routing: [
    'notes/generalized-vehicle-routing-problem',
    'notes/time-dependent-vrp',
    'notes/debris-clearance-arc-routing',
    'projects/dynamic-vrp-reoptimization',
  ],
  location: ['notes/facility-location-problem', 'notes/ambulance-location-mclp'],
  puzzles: [
    'notes/cp-intro',
    'notes/puzzle-calendar-cp',
    'notes/domino-fit-cp',
    'notes/tiling-puzzle-cp',
    'notes/linkedin-patches-cp',
  ],
  debugging: ['notes/infeasible-model-diagnosis'],
};

export const ortoolsCourses: string[] = ['courses/vrp-python', 'courses/health-opt'];

// Entries used as general starting points on the hub. They are linked from the
// hub but are not OR-Tools tutorials themselves, so they get no backlink.
const NON_MEMBER_KEYS = new Set(['notes/mathematical-modeling-art', 'courses/optimization-modeling']);

/** Keys that are already placed somewhere on the hub. */
export const curatedKeys = new Set<string>([
  ...ortoolsLadder.flat(),
  ...Object.values(ortoolsClusters).flat(),
  ...ortoolsCourses,
]);

const hubTagSet = new Set(HUB_TAGS.map((t) => normalizeTag(resolveCanonicalTag(t))));

export function hasHubTag(tags: string[] = []): boolean {
  return tags.some((t) => hubTagSet.has(normalizeTag(resolveCanonicalTag(t))));
}

/** True when a page should link back to the OR-Tools hub. */
export function isOrtoolsHubMember(kind: HubKind, slug: string, tags: string[] = []): boolean {
  const key = `${kind}/${slug}`;
  if (NON_MEMBER_KEYS.has(key)) return false;
  return curatedKeys.has(key) || hasHubTag(tags);
}
