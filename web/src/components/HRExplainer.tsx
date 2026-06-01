export function HRExplainer() {
  return (
    <div className="hr-explainer">
      <div className="hr-explainer__grid hr-explainer__grid--wide">
        <div className="hr-explainer__panel">
          <h3 className="hr-explainer__heading">What the axes mean</h3>
          <p>
            The <strong>Hertzsprung–Russell (HR) diagram</strong> plots stellar color against
            luminosity. We use <strong>B−V</strong> (bluer left) and <strong>absolute magnitude
            M<sub>V</sub></strong> (brighter upward — astronomers flip the usual scale so smaller
            M<sub>V</sub> means more luminous).
          </p>
          <p>
            For a cluster at known distance, every member shares the same distance modulus, so
            apparent magnitudes map directly onto the diagram.
          </p>
        </div>

        <div className="hr-explainer__panel">
          <h3 className="hr-explainer__heading">What is an isochrone?</h3>
          <p>
            An <strong>isochrone</strong> (“same age”) is a model curve: where would stars of every
            mass sit if they formed together? Stellar-evolution codes integrate nuclear burning and
            structure to predict temperature and luminosity at a chosen age and metallicity.
          </p>
          <p>
            Project Midas uses <strong>Yonsei–Yale</strong> tracks at solar metallicity ([Fe/H] = 0).
            Overlaying an isochrone on cluster photometry yields an age estimate and a reference for
            binary detection.
          </p>
        </div>

        <div className="hr-explainer__panel">
          <h3 className="hr-explainer__heading">Reading the turnoff</h3>
          <p>
            The <strong>main-sequence turnoff</strong> is the bend where the band curves toward
            giants: the highest-mass stars still fusing hydrogen in their cores. Its location sets the
            cluster age — a higher, bluer turnoff means younger.
          </p>
          <p>
            For M34 (~200 Myr), turnoff stars are near M<sub>V</sub> ≈ 1 and B−V ≈ 0.3, corresponding
            to roughly <strong>2 M<sub>☉</sub></strong> stars beginning to evolve off the main
            sequence.
          </p>
        </div>

        <div className="hr-explainer__panel">
          <h3 className="hr-explainer__heading">Age in practice</h3>
          <p>
            Fitting is not a single click: you compare several isochrones, minimize residuals in
            color and magnitude, and check that the turnoff, main-sequence width, and faint end all
            agree. Ages of 100–400 Myr look similar at a glance but predict different turnoff
            positions by ~0.5–1 mag.
          </p>
          <p>
            Independent work on M34 — photometry, WOCS rotation, gyrochronology — converges on{' '}
            <strong>180–220 Myr</strong>, consistent with the 200 Myr Yonsei–Yale track.
          </p>
        </div>

        <div className="hr-explainer__panel">
          <h3 className="hr-explainer__heading">Binaries on the diagram</h3>
          <p>
            An unresolved equal-mass pair adds light without shifting color much. The system appears
            ~0.75 mag <em>brighter</em> than a single star at the same B−V — a parallel track above
            the single-star isochrone.
          </p>
          <p>
            Project Midas measures how far each star sits between the single and binary tracks (the{' '}
            <strong>Q-value</strong>) to flag unresolved companions without needing resolved
            spectra.
          </p>
        </div>

        <div className="hr-explainer__panel">
          <h3 className="hr-explainer__heading">What changes with age</h3>
          <ul className="hr-explainer__list">
            <li>
              <strong>100 Myr</strong> — turnoff high; massive stars still on MS (Pleiades-like).
            </li>
            <li>
              <strong>200 Myr</strong> — M34; turnoff near Mv ≈ 1.
            </li>
            <li>
              <strong>400–600 Myr</strong> — turnoff fainter; only solar-type and lower-mass stars
              remain on MS (Hyades / Praesepe regime).
            </li>
            <li>
              <strong>1 Gyr</strong> — old open cluster; narrow MS, faint turnoff.
            </li>
          </ul>
        </div>
      </div>

      <aside className="hr-explainer__note">
        <strong>Classic vs. observational HR diagrams.</strong> Textbooks often plot log&nbsp;L vs.
        log&nbsp;T. Observational work uses color and magnitude because those are what telescopes
        measure. The main sequence is the same physics in either view — a diagonal mass sequence from
        hot blue stars to cool red dwarfs.
      </aside>
    </div>
  );
}
