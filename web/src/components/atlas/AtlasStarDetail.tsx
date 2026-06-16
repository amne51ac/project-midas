import type { AtlasReferenceObject } from '../../data/atlasReferenceObjects';
import type { AtlasCluster, AtlasStar } from '../../data/atlasTypes';
import { T0 } from '../../utils/tierLabel';
import { recommendedUseLabel, trustTierClass, trustTierLabel } from '../../utils/credenceTrust';
import type { AtlasPick } from './atlasPickTypes';

const KIND_LABEL: Record<AtlasReferenceObject['kind'], string> = {
  star: 'Bright star · Navigation layer',
  galaxy: 'Galaxy · Deep sky',
  nebula: 'Nebula · Deep sky',
  cluster: 'Star cluster · Deep sky',
};

interface Props {
  pick: AtlasPick;
  clusters: AtlasCluster[];
  pinned: boolean;
  onClose: () => void;
}

function clusterName(clusters: AtlasCluster[], id: string): string {
  return clusters.find((c) => c.id === id)?.name ?? id;
}

function MemberDetail({ star, clusters }: { star: AtlasStar; clusters: AtlasCluster[] }) {
  const tier = star.trustTier ?? 'unknown';
  const use = star.recommendedUse ?? 'ranking_only';
  const canClassify = use === 'classify';
  const binaryFlag = canClassify
    ? star.pBinary >= 0.5
      ? 'Likely binary (infer, validated tier)'
      : 'Unlikely binary (infer, validated tier)'
    : star.rankPct != null
      ? `Exploratory score — top ${(star.rankPct * 100).toFixed(0)}% of cluster by p_binary (ranking only)`
      : 'Exploratory tier — use p_binary for ranking, not fixed threshold';
  const memberFlag =
    star.pMember != null
      ? star.pMember >= 0.5
        ? 'High P(member) from ingest'
        : 'Low P(member) from ingest'
      : null;

  return (
    <>
      <p className="atlas-detail__kind">Cluster member · Credence {T0}</p>
      <h3 className="atlas-detail__title">{clusterName(clusters, star.clusterId)}</h3>
      {star.trustTier && (
        <p className="atlas-detail__trust">
          <span className={trustTierClass(tier)}>{trustTierLabel(tier)}</span>
          {star.trustScore != null && (
            <span className="atlas-detail__trust-score">trust {star.trustScore.toFixed(2)}</span>
          )}
        </p>
      )}
      <dl className="atlas-detail__grid">
        <div>
          <dt>Gaia source id</dt>
          <dd>{star.id}</dd>
        </div>
        <div>
          <dt>Position</dt>
          <dd>
            RA {star.ra.toFixed(4)}° · Dec {star.dec.toFixed(4)}°
          </dd>
        </div>
        {star.g != null && (
          <div>
            <dt>G magnitude</dt>
            <dd>{star.g.toFixed(2)}</dd>
          </div>
        )}
        <div>
          <dt>p_binary (infer)</dt>
          <dd>
            {star.pBinary.toFixed(4)}
            {star.pInterval90Low != null && star.pInterval90High != null && (
              <span className="atlas-detail__interval">
                {' '}
                [{star.pInterval90Low.toFixed(2)}, {star.pInterval90High.toFixed(2)}]
              </span>
            )}
          </dd>
        </div>
        {star.trustTier && (
          <div>
            <dt>Recommended use</dt>
            <dd>{recommendedUseLabel(use)}</dd>
          </div>
        )}
        {star.pMember != null && (
          <div>
            <dt>P(member) ingest</dt>
            <dd>{star.pMember.toFixed(3)}</dd>
          </div>
        )}
        <div>
          <dt>Malofeeva IR (M34)</dt>
          <dd>{star.malofeeva ? 'Flagged' : 'Not flagged'}</dd>
        </div>
      </dl>
      <div className="atlas-detail__interpret">
        <p>{binaryFlag}</p>
        {memberFlag && <p>{memberFlag}</p>}
        {star.malofeeva ? <p>Independent Malofeeva et al. IR-excess binary candidate.</p> : null}
      </div>
    </>
  );
}

function ReferenceDetail({ star }: { star: AtlasReferenceObject }) {
  return (
    <>
      <p className="atlas-detail__kind">{KIND_LABEL[star.kind]}</p>
      <h3 className="atlas-detail__title">{star.name}</h3>
      <dl className="atlas-detail__grid">
        <div>
          <dt>Constellation</dt>
          <dd>{star.constellation}</dd>
        </div>
        <div>
          <dt>Position</dt>
          <dd>
            RA {star.ra.toFixed(2)}° · Dec {star.dec.toFixed(2)}°
          </dd>
        </div>
        <div>
          <dt>Apparent mag</dt>
          <dd>{star.mag.toFixed(1)}</dd>
        </div>
        <div>
          <dt>Type</dt>
          <dd>{star.kind}</dd>
        </div>
      </dl>
      {star.note && <p className="atlas-detail__interpret">{star.note}</p>}
    </>
  );
}

export function AtlasStarDetail({ pick, clusters, pinned, onClose }: Props) {
  return (
    <aside className={`atlas-detail${pinned ? ' atlas-detail--pinned' : ''}`} aria-live="polite">
      {pinned && (
        <div className="atlas-detail__head">
          <button type="button" className="atlas-detail__close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
      )}
      {pick.type === 'member' ? (
        <MemberDetail star={pick.star} clusters={clusters} />
      ) : (
        <ReferenceDetail star={pick.star} />
      )}
    </aside>
  );
}
