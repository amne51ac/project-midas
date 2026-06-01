import { useCallback, useState } from 'react';

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
  title: string;
  code: string;
}

export function CodeRunner({ title, code }: Props) {
  const [output, setOutput] = useState('Click Run to execute Python in your browser (Pyodide).');
  const [running, setRunning] = useState(false);
  const [isError, setIsError] = useState(false);

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
      await pyodide.runPythonAsync(code);
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
  }, [code]);

  return (
    <div className="code-block">
      <div className="code-block__header">
        <span>{title}</span>
        <button type="button" className="code-block__run" onClick={run} disabled={running}>
          {running ? 'Running…' : 'Run'}
        </button>
      </div>
      <pre>{code.trim()}</pre>
      <pre className={`code-block__output${isError ? ' code-block__output--error' : ''}`}>{output}</pre>
    </div>
  );
}
