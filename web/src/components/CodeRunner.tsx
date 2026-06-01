import { useCallback, useEffect, useMemo, useState } from 'react';
import type { CodeDemo } from '../data/codeDemos';
import { highlightPython } from '../lib/highlightPython';

type PyodideInstance = {
  runPythonAsync: (code: string) => Promise<unknown>;
};

declare global {
  interface Window {
    loadPyodide?: (config: { indexURL: string }) => Promise<PyodideInstance>;
  }
}

let pyodidePromise: Promise<PyodideInstance> | null = null;

async function getPyodide(): Promise<PyodideInstance> {
  if (!pyodidePromise) {
    pyodidePromise = (async () => {
      if (!window.loadPyodide) {
        await new Promise<void>((resolve, reject) => {
          const s = document.createElement('script');
          s.src = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js';
          s.onload = () => resolve();
          s.onerror = () => reject(new Error('Failed to load Pyodide'));
          document.head.appendChild(s);
        });
      }
      return window.loadPyodide!({
        indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/',
      });
    })();
  }
  return pyodidePromise;
}

interface Props {
  demo: CodeDemo;
  isOpen: boolean;
  onToggle: () => void;
}

export function CodeRunner({ demo, isOpen, onToggle }: Props) {
  const [output, setOutput] = useState('Click Run to execute Python in your browser (Pyodide).');
  const [running, setRunning] = useState(false);
  const [isError, setIsError] = useState(false);

  const highlighted = useMemo(() => highlightPython(demo.code), [demo.code]);

  const run = useCallback(async () => {
    setRunning(true);
    setIsError(false);
    setOutput('Loading Python runtime…');
    try {
      const pyodide = await getPyodide();
      await pyodide.runPythonAsync(`
import sys
from io import StringIO
sys.stdout = StringIO()
sys.stderr = StringIO()
`);
      await pyodide.runPythonAsync(demo.code);
      const stdout = await pyodide.runPythonAsync('sys.stdout.getvalue()');
      const stderr = await pyodide.runPythonAsync('sys.stderr.getvalue()');
      const text = (stdout as string) + (stderr as string);
      setOutput(text.trim() || '(no output)');
    } catch (e) {
      setIsError(true);
      setOutput(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }, [demo.code]);

  const headerId = `demo-${demo.id}-header`;
  const panelId = `demo-${demo.id}-panel`;

  return (
    <article
      className={`code-block${isOpen ? ' code-block--open' : ''}`}
      id={`demo-${demo.id}`}
    >
      <h3 className="code-block__heading">
        <button
          type="button"
          className="code-block__trigger"
          id={headerId}
          aria-expanded={isOpen}
          aria-controls={panelId}
          onClick={onToggle}
        >
          <span className="code-block__chevron" aria-hidden="true" />
          <span className="code-block__title">{demo.title}</span>
        </button>
        {isOpen && (
          <button
            type="button"
            className="code-block__run"
            onClick={(e) => {
              e.stopPropagation();
              void run();
            }}
            disabled={running}
          >
            {running ? 'Running…' : 'Run'}
          </button>
        )}
      </h3>

      <div
        className="code-block__body"
        id={panelId}
        role="region"
        aria-labelledby={headerId}
        hidden={!isOpen}
      >
        <p className="code-block__summary">{demo.summary}</p>

        <div className="code-block__io">
          <div className="code-block__io-col">
            <h4 className="code-block__io-heading">Inputs</h4>
            <dl className="code-block__io-list">
              {demo.inputs.map((item) => (
                <div key={item.name}>
                  <dt>{item.name}</dt>
                  <dd>{item.meaning}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="code-block__io-col">
            <h4 className="code-block__io-heading">Outputs</h4>
            <dl className="code-block__io-list">
              {demo.outputs.map((item) => (
                <div key={item.name}>
                  <dt>{item.name}</dt>
                  <dd>{item.meaning}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>

        <pre className="code-block__source">
          <code className="language-python hljs" dangerouslySetInnerHTML={{ __html: highlighted }} />
        </pre>

        <div className="code-block__output-wrap">
          <span className="code-block__output-label">Output</span>
          <pre className={`code-block__output${isError ? ' code-block__output--error' : ''}`}>{output}</pre>
        </div>
      </div>
    </article>
  );
}

function demoIdFromHash(hash: string): string | null {
  const match = hash.match(/^#demo-(.+)$/);
  return match ? match[1] : null;
}

export function CodeDemoGallery({ demos }: { demos: CodeDemo[] }) {
  const [openId, setOpenId] = useState<string | null>(demos[0]?.id ?? null);

  useEffect(() => {
    const syncFromHash = () => {
      const id = demoIdFromHash(window.location.hash);
      if (id && demos.some((demo) => demo.id === id)) {
        setOpenId(id);
      }
    };

    syncFromHash();
    window.addEventListener('hashchange', syncFromHash);
    return () => window.removeEventListener('hashchange', syncFromHash);
  }, [demos]);

  const toggle = useCallback((id: string) => {
    setOpenId((current) => (current === id ? null : id));
  }, []);

  const jumpTo = useCallback((id: string) => {
    setOpenId(id);
    window.history.replaceState(null, '', `${window.location.pathname}#demo-${id}`);
    requestAnimationFrame(() => {
      document.getElementById(`demo-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }, []);

  return (
    <div className="code-demo-gallery">
      <nav className="code-demo-gallery__nav" aria-label="Code examples">
        {demos.map((demo) => (
          <button
            key={demo.id}
            type="button"
            className={`code-demo-gallery__link${openId === demo.id ? ' code-demo-gallery__link--active' : ''}`}
            aria-current={openId === demo.id ? 'true' : undefined}
            onClick={() => jumpTo(demo.id)}
          >
            {demo.title}
          </button>
        ))}
      </nav>
      <div className="code-demo-accordion">
        {demos.map((demo) => (
          <CodeRunner
            key={demo.id}
            demo={demo}
            isOpen={openId === demo.id}
            onToggle={() => toggle(demo.id)}
          />
        ))}
      </div>
    </div>
  );
}
