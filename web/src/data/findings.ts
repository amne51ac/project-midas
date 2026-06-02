import sample from './m34_sample.json';
import synthesis from './synthesisSummary.json';
import wdCheck from './wdCheckSummary.json';
import { homeSectionHref, phasePageHref } from '../routing/appRoute';

export interface FindingStat {
  label: string;
  value: string;
  detail?: string;
}

export interface FindingBlock {
  id: string;
  title: string;
  phase: string;
  paragraphs: string[];
  bullets?: string[];
  stats?: FindingStat[];
  href?: string;
  hrefLabel?: string;
}

export interface FindingsData {
  headline: string;
  lede: string;
  atAGlance: FindingStat[];
  sections: FindingBlock[];
  limitations: string[];
  openQuestions: string[];
}

const meta = sample.meta;

export const FINDINGS: FindingsData = {
  headline: 'What we learned reviving Project Midas',
  lede:
    'Four phases took legacy B−V photometry for M34, reconnected it to Gaia-era catalogs, ' +
    'and asked whether a 2008-era binary heuristic still tells us anything useful. The short answer: ' +
    'the pipeline is reproducible and the join table is solid, but photometric Q-values alone miss most ' +
    'binaries that IR-color and modern surveys already flag.',
  atAGlance: [
    { label: 'Midas stars (pipeline)', value: meta.n_total.toLocaleString(), detail: 'After B-band filter' },
    { label: 'Gaia DR3 matched', value: `${meta.n_gaia_matched} (99.4%)`, detail: 'On join table' },
    { label: 'CG members', value: String(meta.n_cg_members), detail: 'P ≥ 0.7' },
    { label: 'Union binary fraction', value: '96%', detail: '253 / 263 CG members' },
    { label: 'Q-only (exclusive)', value: '4', detail: 'vs Malofeeva on CG sample' },
    { label: 'Phases complete', value: '4 / 4', detail: 'I → IV' },
  ],
  sections: [
    {
      id: 'reproducibility',
      title: 'Legacy photometry still runs — and matches Excel',
      phase: 'Phase I',
      paragraphs: [
        'The original Midas survey dropped to 3,760 stars after removing missing B-band data. Porting Midas.py to Python 3 preserved the Q-value logic, Yonsei–Yale isochrone fits, and Jones–Prosser mating.',
        'Regression against the Excel Control workbook yields 187 accepted singles and 171 binaries — the same counts the original team published. That gives a fixed baseline before any Gaia cross-match.',
      ],
      stats: [
        { label: 'Excel singles / binaries', value: '187 / 171' },
        { label: 'Distance', value: `~${meta.distance_pc} pc` },
        { label: 'Default E(B−V)', value: String(meta.ebv) },
      ],
      bullets: [
        'Interactive site + Pyodide demos make the arithmetic inspectable without a local Python install.',
        'DATA_DICTIONARY.md and REPRODUCTION.md document every column for downstream joins.',
      ],
      href: phasePageHref('phase-i'),
      hrefLabel: 'Phase I writeup',
    },
    {
      id: 'gaia-join',
      title: 'Gaia turns M34 into a cross-match problem, not a PM-selected list',
      phase: 'Phase II',
      paragraphs: [
        'Cantat-Gaudin UPMASK membership replaces Jones–Prosser as the primary filter: 263 Midas overlaps have P ≥ 0.7. The unified join table attaches Gaia source IDs, Malofeeva IR flags, WOCS rotation/RV fields, and Excel classification on one row per Midas star.',
        'Uniform dereddening at E(B−V) = 0.07 produces bv0 and mv0 for HR diagrams and synthesis mass bins. PARSEC isochrones overlay the legacy YY tracks for teaching — analysis still defaults to 0.2 Gyr YY for Q-value parity.',
      ],
      stats: [
        { label: 'Gaia match rate', value: '99.4%' },
        { label: 'Join columns', value: '37+' },
        { label: 'Malofeeva overlap', value: '248' },
        { label: 'WOCS overlap', value: '118' },
      ],
      href: homeSectionHref('data'),
      hrefLabel: 'Data explorer',
    },
    {
      id: 'validation',
      title: 'Q-value picks are precise but incomplete vs independent surveys',
      phase: 'Phase III',
      paragraphs: [
        'On Cantat-Gaudin members, the default Q cut (0 < Q ≤ 1, excluding near-single bvdev) achieves high precision against Malofeeva IR flags but low recall — most IR-flagged stars never received a high Q-value.',
        'WOCS radial-velocity truth is sparse in the VizieR table (23 targets with PRV); Gaia RUWE catches a different astrometric channel with partial overlap. ROC curves and Mv-binned bootstrap show completeness rising toward faint magnitudes where unresolved pairs dominate.',
      ],
      stats: [
        { label: 'Precision vs Malofeeva', value: '0.92' },
        { label: 'Recall vs Malofeeva', value: '0.19' },
        { label: 'F1', value: '0.32' },
        { label: 'RUWE recall (Q cut)', value: '0.30' },
      ],
      bullets: [
        'Q and Malofeeva measure different physics — track offset in B−V vs Gaia+WISE pseudocolor.',
        'Validation framework (ROC, confusion matrices) is reusable for threshold tuning.',
      ],
      href: phasePageHref('phase-iii'),
      hrefLabel: 'Phase III writeup',
    },
    {
      id: 'synthesis',
      title: 'Binary “fraction” depends on how you deduplicate channels',
      phase: 'Phase IV',
      paragraphs: [
        `Among ${synthesis.overall.n} CG members, the union of Q, Malofeeva, Excel, WOCS PRV, and RUWE flags ${synthesis.overall.nBinaryUnion} stars (${Math.round(synthesis.overall.fractionUnion * 100)}%) — but channel hits overlap heavily. Malofeeva alone accounts for ${synthesis.channels.find((c) => c.id === 'malofeeva')?.count ?? 242} flags; Q-value adds only ${synthesis.channels.find((c) => c.id === 'q')?.count ?? 51}.`,
        'Exclusive partitions tell the clearer story: 195 Malofeeva-only, 4 Q-only, 47 flagged by both. Mass-binned fractions are flat (~92–99% union) because Malofeeva dominates every bin — not evidence of a mass-dependent binary fraction in this first pass.',
      ],
      stats: synthesis.overlap.slice(0, 4).map((r) => ({ label: r.label, value: String(r.count) })),
      href: homeSectionHref('compare'),
      hrefLabel: 'Compare chapter',
    },
    {
      id: 'methods',
      title: 'B−V track offset and IR pseudocolor see mostly different stars',
      phase: 'Phase IV',
      paragraphs: [
        'The W2−BP vs de-reddened B−V diagram places 223 CG members with AllWISE+Gaia BP photometry on the same axes Malofeeva used. Malofeeva-only stars fill the IR-excess region; Q-only picks are almost absent (1 star with IR on the diagram).',
        'Dual-flag stars (Q ∩ Malofeeva) form a visible wedge — the channels correlate partially but are far from redundant. For population work, treat them as complementary diagnostics, not votes for the same binary type.',
      ],
      stats: [
        { label: 'With W2−BP', value: '223 CG members' },
        { label: 'Malofeeva only', value: '166' },
        { label: 'Q ∩ Malofeeva', value: '45' },
        { label: 'Q only', value: '1' },
      ],
      href: homeSectionHref('compare'),
      hrefLabel: 'Method comparison plots',
    },
    {
      id: 'white-dwarfs',
      title: 'Rubin LAWDS white dwarfs need more than Gaia DR3 at V ~ 20',
      phase: 'Phase IV',
      paragraphs: [
        'Rubin et al. (2008) selected 44 LAWDS candidates; 17 were spectroscopic DAs and five sit at the cluster distance modulus. We cross-match to Gaia DR3: 22 positional matches, zero clean parallax+PM cluster confirmations at V ≈ 19–21.',
        'LAWDS 15 and 17 show partial proper-motion agreement; photometric distance moduli from Rubin still support membership for several DAs. Faint white dwarf astrometry likely needs DR4 or dedicated PM follow-up — the check module is ready to rerun when a new Gaia export exists.',
      ],
      stats: [
        { label: 'LAWDS candidates', value: String(wdCheck.meta.nCandidates) },
        { label: 'Gaia matched', value: String(wdCheck.summary.nGaiaMatched) },
        { label: 'Paper cluster DAs', value: String(wdCheck.summary.nPaperClusterMembers) },
        { label: 'π + PM cluster match', value: String(wdCheck.summary.nClusterAstrometry) },
      ],
      href: homeSectionHref('compare'),
      hrefLabel: 'WD table',
    },
    {
      id: 'release',
      title: 'The pipeline is packaged for reproduction',
      phase: 'Phase IV',
      paragraphs: [
        'REPRODUCTION.md and run_reproduction.py orchestrate core → validation → synthesis → web exports. Processed CSVs stay local; checked-in JSON on the site carries the portable summaries (synthesis overlap, method-compare diagram, WD check, HR sample).',
        'CITATION.cff provides standard metadata. The exercise demonstrates that a dormant undergraduate-era photometry project can be revived as a validation study in the Gaia era — even when the original binary heuristic is no longer the best discriminator.',
      ],
      bullets: [
        'One command: python scripts/run_reproduction.py --stage all',
        'Web refresh: python scripts/build_web_all.py',
      ],
      href: homeSectionHref('tools'),
      hrefLabel: 'Tools & data release',
    },
  ],
  limitations: [
    'Union binary fraction is an upper envelope dominated by Malofeeva — not a clean spectroscopic census.',
    'Mass bins use YY 0.2 Gyr isochrone inversion; Mv0 dereddening not yet used for mass mapping.',
    'WOCS PRV available for only 23 targets; RV truth set is incomplete.',
    'Gaia DR3 parallaxes at V ~ 20 are too uncertain for LAWDS membership without follow-up.',
    'Processed CSVs are not yet on Zenodo; reproduction requires local raw Midas files.',
  ],
  openQuestions: [
    'Can joint Q + bvdev tuning raise recall without destroying precision?',
    'What is the channel-exclusive binary fraction vs mass (not the Malofeeva-dominated union)?',
    'Do DR4 astrometry or space-based IR confirm the five Rubin cluster white dwarfs?',
    'Does deep Midas BVR add value over Gaia G/BP/RP alone for faint equal-mass pairs?',
  ],
};
