import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';

hljs.registerLanguage('python', python);

export function highlightPython(code: string): string {
  return hljs.highlight(code.trim(), { language: 'python' }).value;
}
